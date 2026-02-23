# ============================================
# FICHIER : prophet_model.py
# RÔLE    : Prédiction avec Prophet + métriques
# ============================================

import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import os

def entrainer_et_predire_prophet(account_code, periods=12, test_months=3):
    """
    Entraîne Prophet sur un compte SAP et calcule les métriques de qualité.
    
    Paramètres:
        account_code : str, ex: "COMPTE_7111"
        periods      : int, nombre de mois à prédire (défaut 12 pour 2026)
        test_months  : int, nombre de mois gardés pour tester (défaut 3)
        
    Retourne:
        dict avec :
            - predictions : DataFrame des prédictions 2026
            - metrics     : dict avec MAE, RMSE, MAPE, R²
            - test_results: DataFrame des prédictions vs réalité sur test set
    """
    
    # --- 1. CHARGER LES DONNÉES ---
    data_path = "../../data/data_for_ai.csv"
    if not os.path.exists(data_path):
        return {"error": "Fichier data_for_ai.csv introuvable"}

    df = pd.read_csv(data_path)
    df_acc = df[df['num_compte'] == account_code].copy()
    
    if len(df_acc) < 12:
        return {"error": f"Pas assez de données pour {account_code}"}
    
    # Préparer pour Prophet (colonnes ds et y obligatoires)
    df_prophet = df_acc[['date', 'montant_final']].rename(
        columns={'date': 'ds', 'montant_final': 'y'}
    )
    df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])
    df_prophet = df_prophet.sort_values('ds').reset_index(drop=True)
    
    # --- 2. SÉPARATION TRAIN / TEST ---
    # On garde les 3 derniers mois (oct, nov, dec 2025) pour tester
    split_index = len(df_prophet) - test_months
    
    train = df_prophet.iloc[:split_index].copy()
    test  = df_prophet.iloc[split_index:].copy()
    
    print(f"\n[Prophet] Compte : {account_code}")
    print(f"  Train : {train['ds'].min().date()} → {train['ds'].max().date()} ({len(train)} mois)")
    print(f"  Test  : {test['ds'].min().date()} → {test['ds'].max().date()} ({len(test)} mois)")
    
    # --- 3. ENTRAÎNEMENT DU MODÈLE ---
    model = Prophet(
        yearly_seasonality=True,   # Saisonnalité annuelle (budget)
        weekly_seasonality=False,  # Pas de semaine (données mensuelles)
        daily_seasonality=False,   # Pas de jour (données mensuelles)
        seasonality_mode='multiplicative'  # Meilleur pour données financières
    )
    model.fit(train)
    
    # --- 4. PRÉDICTION SUR LE TEST SET (pour calculer les métriques) ---
    test_forecast = model.predict(test[['ds']])
    test['yhat'] = test_forecast['yhat'].values
    
    # --- 5. CALCUL DES MÉTRIQUES ---
    y_true = test['y'].values
    y_pred = test['yhat'].values
    
    mae   = mean_absolute_error(y_true, y_pred)
    rmse  = np.sqrt(mean_squared_error(y_true, y_pred))
    r2    = r2_score(y_true, y_pred)
    
    # MAPE (Mean Absolute Percentage Error)
    # Formule : moyenne de |réel - prédit| / |réel| * 100
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    metrics = {
        "MAE":  round(mae, 2),
        "RMSE": round(rmse, 2),
        "MAPE": round(mape, 2),  # en %
        "R2":   round(r2, 4)
    }
    
    print(f"\n  Métriques sur test set ({test_months} mois) :")
    print(f"    MAE  : {metrics['MAE']:>12,.2f} DH  (erreur moyenne absolue)")
    print(f"    RMSE : {metrics['RMSE']:>12,.2f} DH  (erreur quadratique)")
    print(f"    MAPE : {metrics['MAPE']:>12,.2f} %   (erreur en pourcentage)")
    print(f"    R²   : {metrics['R2']:>12,.4f}     (qualité de prédiction, 1 = parfait)")
    
    # --- 6. PRÉDICTION POUR 2026 (le vrai objectif) ---
    # On réentraîne sur TOUTES les données (train + test) pour prédire 2026
    model_full = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode='multiplicative'
    )
    model_full.fit(df_prophet)
    
    future = model_full.make_future_dataframe(periods=periods, freq='ME')
    forecast_2026 = model_full.predict(future)
    
    # Ne garder que les 12 mois futurs (2026)
    predictions_2026 = forecast_2026[['ds', 'yhat']].tail(periods).copy()
    predictions_2026['yhat'] = predictions_2026['yhat'].round(2)
    
    # --- 7. RETOUR ---
    return {
        "account":       account_code,
        "model":         "Prophet",
        "predictions":   predictions_2026,  # DataFrame
        "metrics":       metrics,            # dict
        "test_results":  test[['ds', 'y', 'yhat']]  # DataFrame pour analyse
    }


# --- TEST DIRECT ---
if __name__ == "__main__":
    print("="*60)
    print("  TEST DU MODÈLE PROPHET")
    print("="*60)
    
    # Test sur le Chiffre d'Affaires
    result = entrainer_et_predire_prophet("COMPTE_7111")
    
    if "error" in result:
        print(f"Erreur : {result['error']}")
    else:
        print("\nPrédictions 2026 :")
        print(result['predictions'].to_string(index=False))
        print("\n" + "="*60)