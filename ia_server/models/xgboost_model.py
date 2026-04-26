# ============================================
# FICHIER : xgboost_model.py
# RÔLE    : Prédiction avec XGBoost + métriques
# ============================================

import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
import warnings
warnings.filterwarnings('ignore')


def entrainer_et_predire_xgboost(account_code, year_target, test_months=3):
    """
    Entraîne XGBoost sur un compte SAP.

    XGBoost vs Random Forest :
    - Random Forest : 200 arbres indépendants, moyenne des résultats
    - XGBoost : arbres séquentiels, chaque arbre corrige les erreurs du précédent
    - XGBoost est souvent plus précis mais plus sensible aux hyperparamètres

    Mêmes features que Random Forest :
        - mois, annee, sin/cos saisonnalité
        - lag_1, lag_3, lag_6, lag_12
        - rolling_3, rolling_6, rolling_12

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

    if len(df_acc) < 24:
        return {"error": f"Pas assez de données pour {account_code} (min 24 mois)"}

    # Préparer la série
    df_acc['date'] = pd.to_datetime(df_acc['date'])
    df_acc = df_acc.sort_values('date').reset_index(drop=True)

    # Vérification année cible
    max_year = df_acc['date'].dt.year.max()
    if year_target <= max_year:
        return {"error": f"L'année cible ({year_target}) doit être après {max_year}"}

    print(f"\n[XGBoost] Compte : {account_code}")
    print(f"  Cible : {year_target}")

    # --- 2. CRÉER LES FEATURES (identiques à Random Forest) ---
    df_feat = pd.DataFrame({
        'date':    df_acc['date'],
        'montant': df_acc['montant_final'],
        'annee':   df_acc['date'].dt.year,
        'mois':    df_acc['date'].dt.month,
    })

    # Saisonnalité cyclique
    df_feat['mois_sin'] = np.sin(2 * np.pi * df_feat['mois'] / 12)
    df_feat['mois_cos'] = np.cos(2 * np.pi * df_feat['mois'] / 12)

    # Lag features
    df_feat['lag_1']  = df_feat['montant'].shift(1)
    df_feat['lag_3']  = df_feat['montant'].shift(3)
    df_feat['lag_6']  = df_feat['montant'].shift(6)
    df_feat['lag_12'] = df_feat['montant'].shift(12)

    # Moyennes mobiles
    df_feat['rolling_3']  = df_feat['montant'].shift(1).rolling(3).mean()
    df_feat['rolling_6']  = df_feat['montant'].shift(1).rolling(6).mean()
    df_feat['rolling_12'] = df_feat['montant'].shift(1).rolling(12).mean()

    # Supprimer les NaN
    df_feat = df_feat.dropna().reset_index(drop=True)

    print(f"  Features créées : {len(df_feat)} observations après lags")

    # --- 3. DÉFINIR X ET Y ---
    feature_cols = [
        'annee', 'mois', 'mois_sin', 'mois_cos',
        'lag_1', 'lag_3', 'lag_6', 'lag_12',
        'rolling_3', 'rolling_6', 'rolling_12'
    ]

    X = df_feat[feature_cols].values
    y = df_feat['montant'].values

    # --- 4. SÉPARATION TRAIN / TEST ---
    split_index = len(X) - test_months
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    print(f"  Train : {len(X_train)} mois")
    print(f"  Test  : {len(X_test)} mois")

    # --- 5. ENTRAÎNEMENT XGBOOST ---
    model = XGBRegressor(
        n_estimators=300,      # 300 arbres séquentiels
        max_depth=5,           # Moins profond que RF pour éviter overfitting
        learning_rate=0.05,    # Taux d'apprentissage faible = plus précis
        subsample=0.8,         # 80% des données par arbre
        colsample_bytree=0.8,  # 80% des features par arbre
        random_state=42,
        verbosity=0
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    print(f"  Modèle : XGBoost (300 arbres, lr=0.05, depth=5)")

    # --- 6. PRÉDICTION SUR TEST SET ---
    y_pred = model.predict(X_test)

    # --- 7. MÉTRIQUES ---
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-6))) * 100

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
    print(f"\n  Génération des prédictions pour {year_target}...")

    historique = df_acc['montant_final'].tolist()
    predictions_list = []

    years_ahead = year_target - max_year
    months_to_predict = years_ahead * 12

    for step in range(months_to_predict):
        last_date = df_acc['date'].iloc[-1]
        future_date = last_date + pd.DateOffset(months=step + 1)
        future_annee = future_date.year
        future_mois  = future_date.month

        n = len(historique)

        lag_1  = historique[n-1]  if n >= 1  else 0
        lag_3  = historique[n-3]  if n >= 3  else 0
        lag_6  = historique[n-6]  if n >= 6  else 0
        lag_12 = historique[n-12] if n >= 12 else 0

        rolling_3  = np.mean(historique[n-3:n])  if n >= 3  else np.mean(historique)
        rolling_6  = np.mean(historique[n-6:n])  if n >= 6  else np.mean(historique)
        rolling_12 = np.mean(historique[n-12:n]) if n >= 12 else np.mean(historique)

        mois_sin = np.sin(2 * np.pi * future_mois / 12)
        mois_cos = np.cos(2 * np.pi * future_mois / 12)

        X_future = np.array([[
            future_annee, future_mois, mois_sin, mois_cos,
            lag_1, lag_3, lag_6, lag_12,
            rolling_3, rolling_6, rolling_12
        ]])

        pred = float(model.predict(X_future)[0])
        predictions_list.append({
            'ds':   future_date,
            'yhat': round(pred, 2)
        })
        historique.append(pred)

    # Filtrer l'année cible
    df_futur = pd.DataFrame(predictions_list)
    df_predictions = df_futur[df_futur['ds'].dt.year == year_target].copy()

    print(f"\n  Prédictions {year_target} :")
    print(df_predictions.to_string(index=False))

    # --- 9. IMPORTANCE DES FEATURES ---
    importance = pd.DataFrame({
        'feature':    feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\n  Top 5 features importantes :")
    for _, row in importance.head(5).iterrows():
        print(f"    {row['feature']:<15} : {row['importance']:.3f}")

    # --- 10. RETOUR ---
    test_results = pd.DataFrame({
        'y':    y_test,
        'yhat': y_pred
    })

    return {
        "account":            account_code,
        "model":              "XGBoost",
        "year_target":        year_target,
        "predictions":        df_predictions,
        "metrics":            metrics,
        "feature_importance": importance,
        "test_results":       test_results
    }


# --- TEST DIRECT ---
if __name__ == "__main__":
    print("="*60)
    print("  TEST DU MODÈLE XGBOOST")
    print("="*60)

    annee = int(input("Entrez l'année à prédire : "))
    result = entrainer_et_predire_xgboost("COMPTE_7111", year_target=annee)

    if "error" in result:
        print(f"Erreur : {result['error']}")
    else:
        print(f"\n✅ XGBoost terminé !")
        print(f"  MAPE : {result['metrics']['MAPE']}%")
        print(f"  MAE  : {result['metrics']['MAE']:,.0f} DH")