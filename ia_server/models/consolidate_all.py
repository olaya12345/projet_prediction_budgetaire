# ============================================
# FICHIER : consolidate_all.py
# RÔLE    : Calcule les prédictions par classe (6 ou 7)
#           avec routage vers le modèle ML choisi
#
# MODÈLES DISPONIBLES :
#   - "smart_average"  : Moyenne Saisonnière (défaut)
#   - "prophet"        : Prophet
#   - "arima"          : ARIMA/SARIMA
#   - "random_forest"  : Random Forest
#   - "xgboost"        : XGBoost
#   - "auto"           : Compare tous → prend le meilleur MAPE
# ============================================

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np

MOIS_FR = ['Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
           'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre']

# Modèles supportés et leurs labels
MODELES_DISPONIBLES = {
    "smart_average": "Moyenne Saisonnière",
    "prophet":       "Prophet",
    "arima":         "ARIMA/SARIMA",
    "random_forest": "Random Forest",
    "xgboost":       "XGBoost",
    "auto":          "Auto (Meilleur MAPE)",
}


def get_data_path():
    current_file  = os.path.abspath(__file__)
    models_dir    = os.path.dirname(current_file)
    ia_server_dir = os.path.dirname(models_dir)
    project_root  = os.path.dirname(ia_server_dir)
    return os.path.join(project_root, "data", "data_for_ai.csv")


# ─── ROUTEUR DE MODÈLE ───────────────────────────────────────────
def _obtenir_predictions_modele(compte, year_target, modele, classe):
    """
    Appelle le bon modèle et retourne les prédictions mensuelles
    sous un format unifié : liste de 12 valeurs (index 0 = Janvier).

    Retourne:
        dict {
            "monthly_values": [v1, ..., v12],   # prédictions mensuelles
            "model_nom":      str,
            "fiabilite":      float,
            "mape":           float | None,
            "error":          str | None
        }
    """

    # ── 1. SMART AVERAGE (format original) ──────────────────────
    if modele == "smart_average":
        from models.smart_average_model import calculer_budget_previsionnel
        result = calculer_budget_previsionnel(compte, year_target, silent=True)

        if "error" in result:
            return {"error": result["error"], "model_nom": "Moyenne Saisonnière"}

        df_pred = result["predictions_monthly"]
        monthly = []
        for m in range(1, 13):
            row = df_pred[df_pred["mois_num"] == m]
            if len(row) > 0:
                r = row.iloc[0]
                val = r["budget_debit"] if classe == 6 else r["budget_credit"]
            else:
                val = 0
            monthly.append(round(float(val), 2))

        fiabilite = result.get("fiabilite_globale", 85)
        return {
            "monthly_values": monthly,
            "model_nom":      "Moyenne Saisonnière",
            "fiabilite":      fiabilite,
            "mape":           round((100 - fiabilite) * 0.5, 2),
            "error":          None,
            # Données supplémentaires par mois (tendance, fiabilite)
            "predictions_monthly_df": df_pred,
        }

    # ── 2. MODÈLES ML (format ml_engine : ds + yhat) ────────────
    if modele in ("prophet", "arima", "random_forest", "xgboost"):
        from models.ml_engine import executer_modele
        result = executer_modele(modele, compte, year_target)

        if "error" in result:
            return {"error": result["error"], "model_nom": MODELES_DISPONIBLES.get(modele, modele)}

        df_pred = result["predictions"]   # DataFrame : ds | yhat

        # Extraire les 12 valeurs mensuelles depuis ds/yhat
        monthly = [0.0] * 12
        for _, row in df_pred.iterrows():
            try:
                mois = pd.to_datetime(row["ds"]).month
                monthly[mois - 1] = round(float(row["yhat"]), 2)
            except Exception:
                pass

        mape      = result["metrics"].get("MAPE")
        fiabilite = result.get("fiabilite", max(0, round(100 - (mape or 0), 1)))

        return {
            "monthly_values": monthly,
            "model_nom":      result["model"],
            "fiabilite":      fiabilite,
            "mape":           mape,
            "error":          None,
            "predictions_monthly_df": None,
        }

    # ── 3. AUTO : compare tous, prend le meilleur MAPE ──────────
    if modele == "auto":
        from models.ml_engine import comparer_tous_les_modeles
        result = comparer_tous_les_modeles(compte, year_target)

        if "error" in result:
            # Fallback sur smart_average si tous échouent
            return _obtenir_predictions_modele(compte, year_target, "smart_average", classe)

        meilleur_key = result.get("meilleur_modele", "smart_average")

        # Re-appel avec le meilleur modèle identifié
        res_best = _obtenir_predictions_modele(compte, year_target, meilleur_key, classe)
        if res_best.get("error") is None:
            res_best["model_nom"] = f"Auto → {res_best['model_nom']}"
        return res_best

    # ── Modèle inconnu ───────────────────────────────────────────
    return {"error": f"Modèle inconnu : '{modele}'. Choisissez parmi : {list(MODELES_DISPONIBLES.keys())}"}


# ─── FONCTION PRINCIPALE ─────────────────────────────────────────
def calculer_predictions_par_classe(
    classe:       int,
    year_target:  int,
    year_realise:  int  = None,
    modele:       str  = "smart_average",
    sample_size:  int  = None,     # ← NOUVEAU: limiter nb comptes pour modèles lents
):
    """
    Calcule les prédictions pour tous les comptes d'une classe donnée.

    Paramètres:
        classe       : 6 (Charges) ou 7 (Produits)
        year_target  : Année à prédire
        year_realise : Année de référence (défaut = dernière année complète)
        modele       : Modèle ML à utiliser (voir MODELES_DISPONIBLES)

    Logique comptable:
        - Classe 6 (Charges) : débit - crédit  (positif)
        - Classe 7 (Produits): crédit - débit  (positif)
    """

    # Validation modèle
    if modele not in MODELES_DISPONIBLES:
        return {"error": f"Modèle '{modele}' inconnu. Disponibles : {list(MODELES_DISPONIBLES.keys())}"}

    # Résolution de year_realise
    if year_realise is None:
        available = get_available_years()
        if available:
            complete_years = [y for y in available if y < 2026]
            year_realise = max(complete_years) if complete_years else max(available)
        else:
            year_realise = year_target - 1

    data_path = get_data_path()
    if not os.path.exists(data_path):
        return {"error": f"Fichier introuvable : {data_path}"}

    df = pd.read_csv(data_path)

    df_classe = df[df["classe"] == classe].copy()
    if len(df_classe) == 0:
        return {"error": f"Aucun compte trouvé pour la classe {classe}"}

    df_classe["date"]  = pd.to_datetime(df_classe["date"])
    df_classe["annee"] = df_classe["date"].dt.year
    df_classe["mois"]  = df_classe["date"].dt.month
    df_classe["montant_final"] = df_classe["montant_final"].fillna(0)

    comptes = sorted(df_classe["account"].unique())
    
    # Limiter le nombre de comptes si sample_size fourni
    if sample_size and sample_size < len(comptes):
        import random
        random.seed(42)
        comptes = random.sample(comptes, sample_size)

    resultats       = []
    alertes_comptes = []
    modeles_utilises = {}   # compte → nom du modèle réellement utilisé

    for compte in comptes:
        df_acc = df_classe[df_classe["account"] == compte].copy()

        # Libellé
        libelle = str(compte)
        if "libelle" in df_acc.columns:
            libelle_val = df_acc["libelle"].iloc[0]
            if pd.notna(libelle_val) and str(libelle_val).strip():
                libelle = str(libelle_val)

        # Montant orienté comptablement
        if classe == 6:
            df_acc["montant_value"] = df_acc.apply(
                lambda x: x["Debit"] if pd.notna(x["Debit"]) and x["Credit"] == 0 else 0, axis=1
            )
            debit_only  = df_acc[df_acc["Credit"] == 0]["Debit"].sum()  if "Debit"  in df_acc.columns else 0
            credit_only = df_acc[df_acc["Debit"]  == 0]["Credit"].sum() if "Credit" in df_acc.columns else 0
            if credit_only > debit_only * 0.1:
                alertes_comptes.append({
                    "account":     str(compte),
                    "libelle":     libelle,
                    "classe":      classe,
                    "type_alerte": "credit_inhabituel",
                    "message":     f"Compte classe 6 avec crédit {credit_only:,.0f} > 10% débit {debit_only:,.0f}",
                    "debit":       round(debit_only, 2),
                    "credit":      round(credit_only, 2)
                })
        else:
            df_acc["montant_value"] = df_acc.apply(
                lambda x: x["Credit"] if pd.notna(x["Credit"]) and x["Debit"] == 0 else 0, axis=1
            )
            debit_only  = df_acc[df_acc["Credit"] == 0]["Debit"].sum()  if "Debit"  in df_acc.columns else 0
            credit_only = df_acc[df_acc["Debit"]  == 0]["Credit"].sum() if "Credit" in df_acc.columns else 0
            if debit_only > credit_only * 0.1:
                alertes_comptes.append({
                    "account":     str(compte),
                    "libelle":     libelle,
                    "classe":      classe,
                    "type_alerte": "debit_inhabituel",
                    "message":     f"Compte classe 7 avec débit {debit_only:,.0f} > 10% crédit {credit_only:,.0f}",
                    "debit":       round(debit_only, 2),
                    "credit":      round(credit_only, 2)
                })

        # ── APPEL AU ROUTEUR ────────────────────────────────────
        pred_result = _obtenir_predictions_modele(compte, year_target, modele, classe)

        if pred_result.get("error"):
            # Fallback sur smart_average si le modèle demandé échoue
            print(f"  [!] {compte} -- {pred_result['error']} -- Fallback smart_average")
            pred_result = _obtenir_predictions_modele(compte, year_target, "smart_average", classe)
            if pred_result.get("error"):
                continue   # impossible même avec le fallback

        monthly_preds = pred_result["monthly_values"]    # [v1, ..., v12]
        model_nom     = pred_result["model_nom"]
        fiabilite_mod = pred_result.get("fiabilite", 85)
        df_pred_smart = pred_result.get("predictions_monthly_df")  # uniquement smart_average

        modeles_utilises[str(compte)] = model_nom

        # ── CONSTRUCTION DES DONNÉES MENSUELLES ─────────────────
        available_years_acc = sorted(df_acc["annee"].unique())
        available_years_for_moy = [y for y in available_years_acc if y < year_target]

        mois_data = []
        for month_num in range(1, 13):
            prediction = monthly_preds[month_num - 1]

# Tendance & fiabilité par mois (disponibles seulement via smart_average)
            tendance_pct = 0
            fiabilite    = fiabilite_mod
            volatilite  = "Faible"
            if df_pred_smart is not None:
                row_smart = df_pred_smart[df_pred_smart["mois_num"] == month_num]
                if len(row_smart) > 0:
                    tendance_pct = row_smart.iloc[0].get("tendance_pct", 0)
                    fiabilite    = row_smart.iloc[0].get("fiabilite", fiabilite_mod)
                    volatilite  = row_smart.iloc[0].get("volatilite", "Faible")

            # Réalisé de l'année de référence
            mois_annee_realise = df_acc[
                (df_acc["annee"] == year_realise) & (df_acc["mois"] == month_num)
            ]
            realise = mois_annee_realise["montant_value"].sum() if len(mois_annee_realise) > 0 else 0

            # Moyenne historique (toutes années < year_target)
            vals_mois = []
            for ann in available_years_for_moy:
                data_mois = df_acc[(df_acc["annee"] == ann) & (df_acc["mois"] == month_num)]
                if len(data_mois) > 0:
                    vals_mois.append(data_mois["montant_value"].sum())
            moyenne = np.mean(vals_mois) if vals_mois else 0

            # Variation prédiction vs réalisé
            variation = ((prediction - realise) / realise * 100) if realise != 0 else 0

            # S'assurer que fiabilite n'est pas NaN
            fiabilite = round(float(fiabilite) if fiabilite and not pd.isna(fiabilite) else 85, 0)

            mois_data.append({
                "mois_num":    month_num,
                "mois":        MOIS_FR[month_num - 1],
                "realise":     round(realise, 2),
                "moyenne":     round(moyenne, 2),
                "prediction":  round(prediction, 2),
                "variation":   round(variation, 2),
                "tendance_pct": round(tendance_pct, 2),
                "fiabilite":   fiabilite,
                "volatilite":  volatilite
            })

        # ── TOTAUX DU COMPTE ────────────────────────────────────
        total_realise    = sum(m["realise"]    for m in mois_data)
        total_moyenne    = sum(m["moyenne"]    for m in mois_data)
        total_prediction = sum(m["prediction"] for m in mois_data)
        total_variation  = (
            (total_prediction - total_realise) / total_realise * 100
            if total_realise != 0 else 0
        )

        resultats.append({
            "account":          str(compte),
            "libelle":          libelle,
            "classe":           classe,
            "modele_utilise":   model_nom,           # ← nouveau champ
            "annee_realise":    year_realise,
            "annee_prediction": year_target,
            "donnees_mensuelles": mois_data,
            "totaux": {
                "realise":    round(total_realise, 2),
                "moyenne":    round(total_moyenne, 2),
                "prediction": round(total_prediction, 2),
                "variation":  round(total_variation, 2)
            },
            "fiabilite_moyenne": round(
                np.mean([m["fiabilite"] for m in mois_data if m and m.get("fiabilite", 0) > 0]) or 85, 0
            )
        })

    # ── TOTAUX GLOBAUX ───────────────────────────────────────────
    total_realise_global    = sum(r["totaux"]["realise"]    for r in resultats)
    total_moyenne_global    = sum(r["totaux"]["moyenne"]    for r in resultats)
    total_prediction_global = sum(r["totaux"]["prediction"] for r in resultats)
    total_variation_global  = (
        (total_prediction_global - total_realise_global) / total_realise_global * 100
        if total_realise_global != 0 else 0
    )

    return {
        "success":        True,
        "classe":         classe,
        "classe_label":   "Charges" if classe == 6 else "Produits",
        "modele":         modele,                           # ← nouveau
        "modele_label":   MODELES_DISPONIBLES.get(modele, modele),  # ← nouveau
        "modeles_par_compte": modeles_utilises,             # ← nouveau (utile pour "auto")
        "annee_realise":    year_realise,
        "annee_prediction": year_target,
        "nb_comptes":     len(resultats),
        "comptes":        resultats,
        "totaux_globaux": {
            "realise":    round(total_realise_global, 2),
            "moyenne":    round(total_moyenne_global, 2),
            "prediction": round(total_prediction_global, 2),
            "variation":  round(total_variation_global, 2)
        },
        "alertes":    alertes_comptes,
        "nb_alertes": len(alertes_comptes),
        "mois":       MOIS_FR
    }


# ─── UTILITAIRES ─────────────────────────────────────────────────
def get_comptes_par_classe(classe: int):
    data_path = get_data_path()
    if not os.path.exists(data_path):
        return []
    df = pd.read_csv(data_path)
    return sorted(df[df["classe"] == classe]["account"].unique().tolist())


def get_available_years():
    data_path = get_data_path()
    if not os.path.exists(data_path):
        return []
    df = pd.read_csv(data_path)
    df["date"]  = pd.to_datetime(df["date"])
    df["annee"] = df["date"].dt.year
    return sorted(df["annee"].unique().tolist())


def consolider_tous_les_comptes(year_target, with_ia_comments=True, modele="smart_average"):
    """Wrapper de compatibilité — supporte maintenant le paramètre modele."""
    result_classe6 = calculer_predictions_par_classe(classe=6, year_target=year_target, modele=modele)
    result_classe7 = calculer_predictions_par_classe(classe=7, year_target=year_target, modele=modele)

    comptes_dict = {}

    if "error" not in result_classe6:
        for c in result_classe6.get("comptes", []):
            df_pred = pd.DataFrame(c["donnees_mensuelles"])
            comptes_dict[c["account"]] = {
                "model":          c.get("modele_utilise", "Moyenne Saisonnière"),
                "budget_annuel":  {
                    "debit":  c["totaux"]["prediction"],
                    "credit": 0,
                    "total":  c["totaux"]["prediction"]
                },
                "fiabilite_globale":   c.get("fiabilite_moyenne", 85),
                "predictions_monthly": df_pred,
                "commentaire_ia":      None
            }

    if "error" not in result_classe7:
        for c in result_classe7.get("comptes", []):
            df_pred = pd.DataFrame(c["donnees_mensuelles"])
            comptes_dict[c["account"]] = {
                "model":          c.get("modele_utilise", "Moyenne Saisonnière"),
                "budget_annuel":  {
                    "debit":  0,
                    "credit": c["totaux"]["prediction"],
                    "total":  c["totaux"]["prediction"]
                },
                "fiabilite_globale":   c.get("fiabilite_moyenne", 85),
                "predictions_monthly": df_pred,
                "commentaire_ia":      None
            }

    return {
        "year":  year_target,
        "budget_global": {
            "depenses_annuel": result_classe6.get("totaux_globaux", {}).get("prediction", 0)
                               if "error" not in result_classe6 else 0,
            "produits_annuel": result_classe7.get("totaux_globaux", {}).get("prediction", 0)
                               if "error" not in result_classe7 else 0,
            "net_annuel": 0,
            "depenses_mensuelles": [0] * 12,
            "produits_mensuels":   [0] * 12,
            "net_mensuel":         [0] * 12,
        },
        "stats":   {"comptes_traites": len(comptes_dict), "comptes_erreurs": 0},
        "comptes": comptes_dict
    }


# ─── TEST DIRECT ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("="*70)
    print("  TEST — Prédictions par classe avec sélection du modèle")
    print("="*70)

    available_years = get_available_years()
    print(f"\nAnnées disponibles : {available_years}")
    year_target = max(available_years) + 1 if available_years else 2027

    print("\nModèles disponibles :")
    for k, v in MODELES_DISPONIBLES.items():
        print(f"  {k:<15} → {v}")

    modele_choisi = input("\nModèle à utiliser (défaut: smart_average) : ").strip() or "smart_average"

    for classe in [6, 7]:
        label = "Charges" if classe == 6 else "Produits"
        print(f"\n{'='*70}")
        print(f"  Classe {classe} ({label}) — Modèle : {modele_choisi}")
        print("="*70)

        result = calculer_predictions_par_classe(
            classe=classe, year_target=year_target, modele=modele_choisi
        )

        if "error" in result:
            print(f"  Erreur : {result['error']}")
        else:
            print(f"  Comptes      : {result['nb_comptes']}")
            print(f"  Modèle label : {result['modele_label']}")
            t = result["totaux_globaux"]
            print(f"  Total Réalisé    : {t['realise']:>15,.2f} DH")
            print(f"  Total Moyenne    : {t['moyenne']:>15,.2f} DH")
            print(f"  Total Prédiction : {t['prediction']:>15,.2f} DH")
            print(f"  Variation        : {t['variation']:>14.2f}%")

            if result.get("nb_alertes", 0) > 0:
                print(f"\n  [!] Alertes : {result['nb_alertes']}")
                for alerte in result["alertes"][:3]:
                    print(f"    - {alerte['message']}")

            print("\n  Exemple — 3 premiers comptes :")
            for c in result["comptes"][:3]:
                t2 = c["totaux"]
                print(
                    f"    {c['account']:<20} "
                    f"Real={t2['realise']:>12,.0f}  "
                    f"Moy={t2['moyenne']:>12,.0f}  "
                    f"Prédit={t2['prediction']:>12,.0f}  "
                    f"[{c['modele_utilise']}]"
                )