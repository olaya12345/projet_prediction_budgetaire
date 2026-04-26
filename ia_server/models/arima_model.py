# ============================================
# FICHIER : arima_model.py
# RÔLE    : Prédiction avec ARIMA + métriques
# ============================================

import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
import warnings
warnings.filterwarnings('ignore')


def entrainer_et_predire_arima(account_code, year_target, test_months=3):
    """
    Entraîne SARIMA sur un compte SAP et calcule les métriques.

    Paramètres:
        account_code : str, ex: "COMPTE_7111"
        year_target  : int, année cible obligatoire
        test_months  : int, mois gardés pour tester (défaut 3)
    """

    # --- 1. CHARGER LES DONNÉES ---
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    data_path = os.path.join(project_root, "data", "data_for_ai.csv")

    if not os.path.exists(data_path):
        return {"error": f"Fichier introuvable : {data_path}"}

    df = pd.read_csv(data_path)
    df_acc = df[df['account'] == account_code].copy()

    if len(df_acc) < 12:
        return {"error": f"Pas assez de données pour {account_code}"}

    # Préparer la série temporelle avec index de dates propre
    df_acc['date'] = pd.to_datetime(df_acc['date'])
    df_acc = df_acc.sort_values('date').reset_index(drop=True)

    # Vérification année cible
    max_year = df_acc['date'].dt.year.max()
    if year_target <= max_year:
        return {"error": f"L'année cible ({year_target}) doit être après {max_year}"}

    # Calcul des mois à prédire
    years_ahead = year_target - max_year
    months_to_predict = years_ahead * 12

    serie = df_acc['montant_final'].values

    # --- 2. SÉRIE AVEC INDEX TEMPOREL PROPRE ---
    df_serie = pd.DataFrame(
        {'montant': serie},
        index=pd.date_range(start='2016-01', periods=len(serie), freq='MS')
    )

    # --- 3. TEST DE STATIONNARITÉ (ADF) ---
    adf_result = adfuller(serie)
    p_value = adf_result[1]
    d = 0 if p_value < 0.05 else 1

    print(f"\n[ARIMA] Compte : {account_code}")
    print(f"  Stationnarité (ADF p-value) : {p_value:.4f} → d={d}")
    print(f"  Cible : {year_target} ({months_to_predict} mois à prédire)")

    # --- 4. SÉPARATION TRAIN / TEST ---
    split_index = len(df_serie) - test_months
    train_serie = df_serie.iloc[:split_index]
    test_serie  = df_serie.iloc[split_index:]

    print(f"  Train : {len(train_serie)} mois")
    print(f"  Test  : {len(test_serie)} mois")

    # --- 5. ENTRAÎNEMENT SARIMA SUR TRAIN ---
    try:
        model = SARIMAX(
            train_serie['montant'],
            order=(1, d, 1),
            seasonal_order=(1, 1, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        model_fit = model.fit(disp=False)
        print(f"  Modèle : SARIMA(1,{d},1)(1,1,1,12)")
    except Exception:
        print(f"  [!] SARIMA echoue, fallback ARIMA(1,{d},1)")
        model = SARIMAX(train_serie['montant'], order=(1, d, 1))
        model_fit = model.fit(disp=False)

    # --- 6. PRÉDICTION SUR TEST SET ---
    pred_test = model_fit.forecast(steps=test_months)

    # --- 7. MÉTRIQUES ---
    y_true = test_serie['montant'].values
    y_pred = pred_test.values

    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-6))) * 100

    metrics = {
        "MAE":  round(mae, 2),
        "RMSE": round(rmse, 2),
        "MAPE": round(mape, 2),
        "R2":   round(r2, 4)
    }

    print(f"\n  Métriques sur test set ({test_months} mois) :")
    print(f"    MAE  : {metrics['MAE']:>12,.2f} DH")
    print(f"    RMSE : {metrics['RMSE']:>12,.2f} DH")
    print(f"    MAPE : {metrics['MAPE']:>12,.2f} %")
    print(f"    R²   : {metrics['R2']:>12,.4f}")

    # --- 8. PRÉDICTION POUR L'ANNÉE CIBLE (step by step) ---
    # On prédit mois par mois en ajoutant chaque prédiction à l'historique
    print(f"\n  Génération des prédictions pour {year_target}...")
    print(f"  (Peut prendre 1-2 minutes)")

    history = df_serie['montant'].tolist()
    predictions_list = []

    for step in range(months_to_predict):
        try:
            temp_model = SARIMAX(
                history,
                order=(1, d, 1),
                seasonal_order=(1, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            temp_fit = temp_model.fit(disp=False)
            pred = float(temp_fit.forecast(steps=1)[0])
        except Exception:
            temp_model = SARIMAX(history, order=(1, d, 1))
            temp_fit = temp_model.fit(disp=False)
            pred = float(temp_fit.forecast(steps=1)[0])

        predictions_list.append(pred)
        history.append(pred)

    # Créer les dates futures
    future_index = pd.date_range(
        start=df_serie.index[-1] + pd.DateOffset(months=1),
        periods=months_to_predict,
        freq='MS'
    )

    df_futur = pd.DataFrame({
        'ds':   future_index,
        'yhat': [round(p, 2) for p in predictions_list]
    })

    # Filtrer uniquement l'année cible
    df_predictions = df_futur[df_futur['ds'].dt.year == year_target].copy()

    print(f"\n  Prédictions {year_target} :")
    print(df_predictions.to_string(index=False))

    # --- 9. RETOUR ---
    test_results = pd.DataFrame({
        'ds':   test_serie.index,
        'y':    y_true,
        'yhat': y_pred
    })

    return {
        "account":      account_code,
        "model":        "ARIMA/SARIMA",
        "year_target":  year_target,
        "d_value":      d,
        "predictions":  df_predictions,
        "metrics":      metrics,
        "test_results": test_results
    }


# --- TEST DIRECT ---
if __name__ == "__main__":
    print("="*60)
    print("  TEST DU MODÈLE ARIMA")
    print("="*60)

    annee = int(input("Entrez l'année à prédire : "))
    result = entrainer_et_predire_arima("COMPTE_7111", year_target=annee)

    if "error" in result:
        print(f"Erreur : {result['error']}")
    else:
        print(f"\n✅ ARIMA terminé !")
        print(f"  MAPE : {result['metrics']['MAPE']}%")
        print(f"  MAE  : {result['metrics']['MAE']:,.0f} DH")