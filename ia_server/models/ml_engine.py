# ============================================
# FICHIER : ml_engine.py
# RÔLE    : Orchestrateur — compare tous les modèles
#           et retourne automatiquement le meilleur
# ============================================

import pandas as pd
import numpy as np
import os
import sys
import time
import warnings
warnings.filterwarnings('ignore')

current_file  = os.path.abspath(__file__)
models_dir    = os.path.dirname(current_file)       # ia_server/models
ia_server_dir = os.path.dirname(models_dir)         # ia_server
sys.path.insert(0, ia_server_dir)


# ─── CONFIGURATION DES MODÈLES ───────────────────────────────────
# Pour désactiver un modèle, mettre enabled=False
MODELES_CONFIG = {
    "smart_average": {
        "nom":     "Moyenne Saisonnière",
        "enabled": True,
        "timeout": 30,    # secondes max
    },
    "prophet": {
        "nom":     "Prophet",
        "enabled": True,
        "timeout": 60,
    },
    "arima": {
        "nom":     "ARIMA/SARIMA",
        "enabled": True,
        "timeout": 300,   # ARIMA est lent
    },
    "random_forest": {
        "nom":     "Random Forest",
        "enabled": True,
        "timeout": 60,
    },
    "xgboost": {
        "nom":     "XGBoost",
        "enabled": True,
        "timeout": 60,
    },
}


def executer_modele(nom_modele, account_code, year_target):
    """
    Exécute un modèle et retourne son résultat standardisé.
    Gère les erreurs proprement.
    """
    try:
        start = time.time()

        if nom_modele == "smart_average":
            from models.smart_average_model import calculer_budget_previsionnel
            result = calculer_budget_previsionnel(account_code, year_target=year_target)

            if "error" in result:
                return {"error": result["error"], "model": "Moyenne Saisonnière"}

            # Standardiser le format (smart_average retourne un format différent)
            df_pred = result['predictions_monthly']

            # Calculer MAPE approximatif basé sur la fiabilité
            fiabilite = result['fiabilite_globale']
            mape_approx = round((100 - fiabilite) * 0.5, 2)

            predictions_std = pd.DataFrame({
                'ds':   pd.to_datetime(
                    df_pred['mois_num'].apply(
                        lambda m: f"{year_target}-{m:02d}-01"
                    )
                ),
                'yhat': df_pred['budget_total']
            })

            return {
                "model":       "Moyenne Saisonnière",
                "model_key":   "smart_average",
                "predictions": predictions_std,
                "metrics": {
                    "MAE":  None,
                    "RMSE": None,
                    "MAPE": mape_approx,
                    "R2":   None
                },
                "budget_annuel": result['budget_annuel'],
                "fiabilite":     result['fiabilite_globale'],
                "duree_sec":     round(time.time() - start, 1)
            }

        elif nom_modele == "prophet":
            from models.prophet_model import entrainer_et_predire_prophet
            result = entrainer_et_predire_prophet(account_code, year_target=year_target)

            if "error" in result:
                return {"error": result["error"], "model": "Prophet"}

            return {
                "model":       "Prophet",
                "model_key":   "prophet",
                "predictions": result['predictions'].rename(columns={'yhat': 'yhat'}),
                "metrics":     result['metrics'],
                "budget_annuel": {
                    "total": round(result['predictions']['yhat'].sum(), 2)
                },
                "fiabilite":  max(0, round(100 - result['metrics']['MAPE'], 1)),
                "duree_sec":  round(time.time() - start, 1)
            }

        elif nom_modele == "arima":
            from models.arima_model import entrainer_et_predire_arima
            result = entrainer_et_predire_arima(account_code, year_target=year_target)

            if "error" in result:
                return {"error": result["error"], "model": "ARIMA"}

            return {
                "model":       "ARIMA/SARIMA",
                "model_key":   "arima",
                "predictions": result['predictions'],
                "metrics":     result['metrics'],
                "budget_annuel": {
                    "total": round(result['predictions']['yhat'].sum(), 2)
                },
                "fiabilite":  max(0, round(100 - result['metrics']['MAPE'], 1)),
                "duree_sec":  round(time.time() - start, 1)
            }

        elif nom_modele == "random_forest":
            from models.random_forest_model import entrainer_et_predire_rf
            result = entrainer_et_predire_rf(account_code, year_target=year_target)

            if "error" in result:
                return {"error": result["error"], "model": "Random Forest"}

            return {
                "model":       "Random Forest",
                "model_key":   "random_forest",
                "predictions": result['predictions'],
                "metrics":     result['metrics'],
                "budget_annuel": {
                    "total": round(result['predictions']['yhat'].sum(), 2)
                },
                "fiabilite":  max(0, round(100 - result['metrics']['MAPE'], 1)),
                "duree_sec":  round(time.time() - start, 1)
            }

        elif nom_modele == "xgboost":
            from models.xgboost_model import entrainer_et_predire_xgboost
            result = entrainer_et_predire_xgboost(account_code, year_target=year_target)

            if "error" in result:
                return {"error": result["error"], "model": "XGBoost"}

            return {
                "model":       "XGBoost",
                "model_key":   "xgboost",
                "predictions": result['predictions'],
                "metrics":     result['metrics'],
                "budget_annuel": {
                    "total": round(result['predictions']['yhat'].sum(), 2)
                },
                "fiabilite":  max(0, round(100 - result['metrics']['MAPE'], 1)),
                "duree_sec":  round(time.time() - start, 1)
            }

    except Exception as e:
        return {"error": str(e), "model": nom_modele}


def comparer_tous_les_modeles(account_code, year_target):
    """
    Lance tous les modèles activés sur un compte et retourne
    une comparaison complète avec le meilleur modèle identifié.

    Paramètres:
        account_code : str, ex: "COMPTE_7111"
        year_target  : int, année cible

    Retourne:
        dict avec résultats de tous les modèles + meilleur modèle
    """

    print("\n" + "="*70)
    print(f"  ML ENGINE — Comparaison des modèles")
    print(f"  Compte : {account_code} | Année : {year_target}")
    print("="*70)

    resultats = {}
    modeles_valides = []

    # --- LANCER CHAQUE MODÈLE ---
    for model_key, config in MODELES_CONFIG.items():
        if not config["enabled"]:
            print(f"\n  ⏭️  {config['nom']} — Désactivé")
            continue

        print(f"\n  🔄 Lancement : {config['nom']}...")

        result = executer_modele(model_key, account_code, year_target)

        if "error" in result:
            print(f"  ❌ {config['nom']} — Erreur : {result['error']}")
            resultats[model_key] = {"error": result["error"], "model": config['nom']}
        else:
            duree = result.get('duree_sec', '?')
            mape  = result['metrics']['MAPE']
            print(f"  ✅ {config['nom']} — MAPE: {mape}% | Durée: {duree}s")
            resultats[model_key] = result
            modeles_valides.append(model_key)

    if not modeles_valides:
        return {"error": "Aucun modèle n'a réussi à prédire ce compte."}

    # --- TROUVER LE MEILLEUR MODÈLE ---
    # Exclure smart_average du classement MAPE (pas de vrai test set)
    # Il est gardé comme référence mais ne peut pas gagner
    modeles_comparables = [k for k in modeles_valides if k != "smart_average"]

    if modeles_comparables:
        meilleur_key = min(
            modeles_comparables,
            key=lambda k: resultats[k]['metrics']['MAPE']
        )
    else:
        # Si aucun autre modèle, utiliser smart_average par défaut
        meilleur_key = "smart_average"

    meilleur = resultats[meilleur_key]

    # --- RAPPORT COMPARATIF ---
    print("\n" + "="*70)
    print(f"  COMPARAISON FINALE — {account_code} ({year_target})")
    print("="*70)
    print(f"\n  {'Modèle':<25} | {'MAPE':>8} | {'MAE':>15} | {'Fiabilité':>10} | Statut")
    print(f"  {'-'*70}")

    for key in MODELES_CONFIG:
        if key not in resultats:
            continue
        r = resultats[key]
        if "error" in r:
            print(f"  {r['model']:<25} | {'N/A':>8} | {'N/A':>15} | {'N/A':>10} | ❌ Erreur")
        elif key == "smart_average":
            # Afficher sans MAPE (pas comparable)
            fiab = r['fiabilite']
            print(f"  {r['model']:<25} | {'N/A':>8} | {'N/A':>15} | {fiab:>9.1f}% | 📊 Référence")
        else:
            mape     = r['metrics']['MAPE']
            mae      = r['metrics']['MAE']
            fiab     = r['fiabilite']
            est_best = "🏆 MEILLEUR" if key == meilleur_key else ""
            mae_str  = f"{mae:,.0f} DH" if mae else "N/A"
            print(f"  {r['model']:<25} | {mape:>7.2f}% | {mae_str:>15} | {fiab:>9.1f}% | {est_best}")

    print(f"\n  🏆 Meilleur modèle : {meilleur['model']} (MAPE {meilleur['metrics']['MAPE']}%)")
    print(f"  💰 Budget annuel   : {meilleur['budget_annuel']['total']:,.0f} DH")
    print("="*70)

    # Classement sans smart_average
    classement = sorted(
        [
            {
                "modele":    resultats[k]['model'],
                "mape":      resultats[k]['metrics']['MAPE'],
                "fiabilite": resultats[k]['fiabilite']
            }
            for k in modeles_comparables
            if k in resultats and "error" not in resultats[k]
        ],
        key=lambda x: x['mape']
    )

    # Ajouter smart_average en bas comme référence
    if "smart_average" in resultats and "error" not in resultats["smart_average"]:
        classement.append({
            "modele":    "Moyenne Saisonnière",
            "mape":      None,
            "fiabilite": resultats["smart_average"]["fiabilite"],
            "note":      "Référence (pas de test set)"
        })

    # --- RETOUR COMPLET ---
    return {
        "account":          account_code,
        "year_target":      year_target,
        "meilleur_modele":  meilleur_key,
        "meilleur_nom":     meilleur['model'],
        "meilleur_mape":    meilleur['metrics']['MAPE'],
        "predictions":      meilleur['predictions'],
        "budget_annuel":    meilleur['budget_annuel'],
        "tous_les_modeles": resultats,
        "classement":       classement
    }


# --- TEST DIRECT ---
if __name__ == "__main__":
    print("="*70)
    print("  TEST ML ENGINE — Comparaison automatique des modèles")
    print("="*70)

    compte = input("Compte SAP (ex: COMPTE_7111) : ").strip() or "COMPTE_7111"
    annee  = int(input("Année à prédire (ex: 2028) : ") or 2028)

    result = comparer_tous_les_modeles(compte, annee)

    if "error" in result:
        print(f"\n❌ Erreur : {result['error']}")
    else:
        print(f"\n✅ ML Engine terminé !")
        print(f"\n  Classement final (modèles avec test set réel) :")
        for i, r in enumerate(result['classement'], 1):
            if r.get('mape') is not None:
                print(f"    {i}. {r['modele']:<25} MAPE: {r['mape']}%")
            else:
                print(f"    -  {r['modele']:<25} {r.get('note', '')}")

        print(f"\n  Prédictions du meilleur modèle ({result['meilleur_nom']}) :")
        print(result['predictions'].to_string(index=False))