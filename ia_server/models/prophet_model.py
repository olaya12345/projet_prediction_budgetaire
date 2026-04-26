import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
import numpy as np
import os

def entrainer_et_predire_prophet(account_code,year_target,test_months=3):
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    data_path = os.path.join(project_root,"data","data_for_ai.csv")

    if not os.path.exists(data_path):
        return {"error": f"Fichier introuvable : {data_path}"}
    df = pd.read_csv(data_path)
    df_acc = df[df['account'] == account_code].copy()
    if len(df_acc) <12:
        return {"error": f"Pas assez de données pour {account_code}"}
    
    #preparer pour prophet (colnnes ds et y obl)
    df_prophet = df_acc[['date','montant_final']].rename(
        columns={'date':'ds','montant_final':'y'}
    )
    df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])
    df_prophet = df_prophet.sort_values('ds').reset_index(drop=True)

    max_year_in_data = df_prophet['ds'].dt.year.max()

    if year_target <= max_year_in_data:
        # Predire pour l'annee meme si elle est dans les donnees (partiellement)
        years_ahead = 1
        months_to_predict = 12
    else:
        years_ahead = year_target - max_year_in_data
        months_to_predict = (years_ahead * 12) + 12

    split_index = len(df_prophet) - test_months
    train = df_prophet.iloc[:split_index].copy()
    test = df_prophet.iloc[split_index:].copy()

    print(f"\n[Prophet] Compte : {account_code}")
    print(f" Train  : {train['ds'].min().date()} -> {train['ds'].max().date()} ({len(train)} mois)")
    print(f" test : {test['ds'].min().date()} -> {test['ds'].max().date()} ({len(test)} mois)" )
    print(f" Cible : {year_target} (Génération de {months_to_predict} mois futurs)")

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode='multiplicative'
    )
    model.fit(train)

    test_forecast = model.predict(test[['ds']])
    test['yhat'] = test_forecast['yhat'].values

    y_true = test['y'].values
    y_pred = test['yhat'].values
#calcul de métrique
    mae = mean_absolute_error(y_true,y_pred)
    rmse = np.sqrt(mean_squared_error(y_true,y_pred))
    r2 = r2_score(y_true,y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    metrics = {
        "MAE":round(mae,2),
        "RMSE":round(rmse,2),
        "MAPE":round(mape,2),
        "R2":round(r2,4)
    }

    print(f"\n Métriques sur test set ({test_months} mois) :")
    print(f" MAE : {metrics['MAE']:>12,.2f} DH")
    print(f"RMSE : {metrics['RMSE']:>12,.2f} DH")
    print(f" MAPE : {metrics['MAPE']:>12,.2f}%")
    print(f"R2 : {metrics['R2']:<12,.4f}")

    model_full = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode = 'multiplicative'
    )
    model_full.fit(df_prophet)

    #Générer le futur jusqu'a l'année cible
    future = model_full.make_future_dataframe(periods=months_to_predict,freq='ME')
    forecast_all = model_full.predict(future)

    #filtrer les 12mois de l'année cible
    forecast_target = forecast_all[forecast_all['ds'].dt.year == year_target].copy()
    predictions_target = forecast_target[['ds','yhat']].copy()
    predictions_target['yhat'] = predictions_target['yhat'].round(2)

    return{
        "account":account_code,
        "model":"Prophet",
        "year_target":year_target,
        "predictions":predictions_target,
        "metrics":metrics,
        "test_results":test[['ds','y','yhat']]
    }


if __name__=="__main__":
    print("="*60)
    print(" TEST DU MODELE PROPHET (Dynamique)")
    print("="*60)

    annee_choisie = int(input("Entrez l'année à prédire avec Prophet :"))
    result = entrainer_et_predire_prophet("COMPTE_7111",year_target=annee_choisie)

    if "error" in result:
        print(f"Erreur : {result['error']}")
    else:
        print(f"\nPrédictions {annee_choisie} :")
        print(result['predictions'].to_string(index=False))
        print("\n" + "="*60)
