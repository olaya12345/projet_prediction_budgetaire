# ============================================
# FICHIER : smart_average_model.py
# RÔLE    : Moyenne saisonnière intelligente
# ============================================

import pandas as pd
import numpy as np
from scipy import stats
import os
import math


def _safe(val, default=0.0):
    """Retourne default si val est nan/inf/None."""
    try:
        v = float(val)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except (TypeError, ValueError):
        return default


def calculer_budget_previsionnel(account_code, year_target, min_years=3, max_years=5, silent=False):
    """
    Calcule le budget prévisionnel par mois.

    Règles comptables :
    - Classe 6 (charges) : solde_net = Debit - Credit (positif = charge)
    - Classe 7 (produits): solde_net = Credit - Debit (positif = produit)

    Pour la prédiction :
    - On utilise les écritures où Credit = 0 pour classe 6 (écritures de charge originales)
    - On utilise les écritures où Debit = 0 pour classe 7 (écritures de produit originales)
    """
    
    # --- 1. CHARGER LES DONNÉES ---
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    data_path = os.path.join(project_root, "data", "data_for_ai.csv")
    
    if not os.path.exists(data_path):
        return {"error": f"Fichier introuvable : {data_path}"}

    df = pd.read_csv(data_path)
    account_code_int = int(account_code) if isinstance(account_code, str) else account_code
    df_acc = df[df['account'] == account_code_int].copy()
    
    if len(df_acc) < 1:
        return {"error": f"Pas de donnees pour {account_code}"}
    
    # Préparer les colonnes
    df_acc['date'] = pd.to_datetime(df_acc['date'])
    df_acc['year'] = df_acc['date'].dt.year
    df_acc['month'] = df_acc['date'].dt.month
    
    # Déterminer la classe (6 = charge, 7 = produit)
    est_classe_6 = str(account_code).startswith('6')
    
    # Calculer le montant net selon la classe
    # Pour classe 6: Debit - Credit (valeur positive = charge)
    # Pour classe 7: Credit - Debit (valeur positive = produit)
    # On utilise la formule directe SANS filtre pour avoir les vraie valeurs
    df_acc['montant_debit'] = df_acc['Debit'].fillna(0)
    df_acc['montant_credit'] = df_acc['Credit'].fillna(0)
    
    if est_classe_6:
        # Classe 6 = charges = Debit - Credit (les deux peuvent être non-zeros)
        df_acc['solde_net'] = df_acc['montant_debit'] - df_acc['montant_credit']
    else:
        # Classe 7 = produits = Credit - Debit
        df_acc['solde_net'] = df_acc['montant_credit'] - df_acc['montant_debit']
    
    # --- 2. SÉLECTIONNER LES ANNÉES HISTORIQUES ---
    available_years = sorted(df_acc['year'].unique())
    # Exclure l'année target si elle est dans les données
    available_years = [y for y in available_years if y < year_target]
    n_years = min(max_years, len(available_years))
    n_years = max(min_years, n_years)
    
    years_to_use = available_years[-n_years:] if available_years else []
    df_hist = df_acc[df_acc['year'].isin(years_to_use)].copy() if years_to_use else df_acc.copy()

    if not silent:
        print(f"\n{'='*65}")
        print(f"  PRÉVISION BUDGÉTAIRE — Moyenne Intelligente")
        print(f"{'='*65}")
        print(f"  Compte        : {account_code}")
        print(f"  Années source : {years_to_use}")
        print(f"  Année cible   : {year_target}")
        print(f"  Transactions  : {len(df_hist)}")
    
    # --- 3. CALCUL PAR MOIS CALENDAIRE ---
    predictions = []
    
    for month_num in range(1, 13):
        month_data = df_hist[df_hist['month'] == month_num]
        
        if len(month_data) == 0:
            # Pas de données pour ce mois, mettre 0
            predictions.append({
                'mois_num': month_num,
                'mois': pd.Timestamp(f"{year_target}-{month_num:02d}-01").strftime('%B'),
                'budget_debit': 0,
                'budget_credit': 0,
                'budget_total': 0,
                'tendance_pct': 0,
                'fiabilite': 0,
                'n_annees': 0
            })
            continue
        
        # Moyenne des valeurs historiques
        valeurs = month_data['solde_net'].values
        mean_value = np.mean(valeurs)
        
        # Si la moyenne est négative ou proche de 0, utiliser l'écart-type comme estimation
        if mean_value <= 0:
            std_val = np.std(valeurs) if len(valeurs) > 1 else abs(mean_value)
            mean_value = std_val
        
        # Tendance sur les valeurs absolues (pour éviter tendances négatives aberrantes)
        abs_valeurs = np.abs(valeurs)
        years_in_month = month_data['year'].values
        
        if len(years_in_month) >= 2 and mean_value > 0:
            # Régression linéaire sur les valeurs absolues
            slope, intercept, r_value, p_value, std_err = stats.linregress(years_in_month, abs_valeurs)
            
            # Tendance en %
            tendance_pct = (slope / mean_value) * 100
            
            # Limiter la tendance entre -20% et +20% par an
            tendance_pct = max(-20, min(20, tendance_pct))
            
            # Facteur de croissance
            years_ahead = year_target - years_in_month[-1]
            facteur_croissance = 1 + (tendance_pct / 100) * years_ahead
            facteur_croissance = max(0.5, min(1.5, facteur_croissance))
        else:
            tendance_pct = 0
            facteur_croissance = 1.0
        
        # Budget previsionnel (toujours positif)
        budget_prevu = max(0, mean_value * facteur_croissance)
        
        # Fiabilité basée sur le nombre d'années et la variance
        score = 100
        if len(years_in_month) < 3:
            score -= 20
        if len(years_in_month) < 2:
            score -= 30
        if np.std(valeurs) > np.mean(valeurs) * 0.5:
            score -= 20
        score = max(0, min(100, score))
        
        month_name = pd.Timestamp(f"{year_target}-{month_num:02d}-01").strftime('%B')
        
        # Volatilité
        std_val = np.std(valeurs) if len(valeurs) > 1 else 0
        cv = (std_val / abs(mean_value)) * 100 if mean_value != 0 else 0
        if cv > 30:
            volatilite = "Élevée"
        elif cv > 15:
            volatilite = "Moyenne"
        else:
            volatilite = "Faible"
        
        if est_classe_6:
            predictions.append({
                'mois_num': month_num,
                'mois': month_name,
                'budget_debit': round(budget_prevu, 2),
                'budget_credit': 0,
                'budget_total': round(budget_prevu, 2),
                'tendance_pct': round(tendance_pct, 2),
                'volatilite': volatilite,
                'fiabilite': score,
                'n_annees': len(years_in_month),
                'intervalle': f"[{budget_prevu * 0.8:,.0f} - {budget_prevu * 1.2:,.0f}]",
                'anomalies': []
            })
        else:
            predictions.append({
                'mois_num': month_num,
                'mois': month_name,
                'budget_debit': 0,
                'budget_credit': round(budget_prevu, 2),
                'budget_total': round(budget_prevu, 2),
                'tendance_pct': round(tendance_pct, 2),
                'volatilite': volatilite,
                'fiabilite': score,
                'n_annees': len(years_in_month),
                'intervalle': f"[{budget_prevu * 0.8:,.0f} - {budget_prevu * 1.2:,.0f}]",
                'anomalies': []
            })
    
    # --- 4. BUDGET ANNUEL ---
    df_pred = pd.DataFrame(predictions)
    
    budget_annuel_debit = df_pred['budget_debit'].sum()
    budget_annuel_credit = df_pred['budget_credit'].sum()
    budget_annuel_total = budget_annuel_debit + budget_annuel_credit
    
    fiabilite_moyenne = df_pred['fiabilite'].mean()
    
    # --- 5. RAPPORT ---
    if not silent:
        print(f"\n  {'Prévisions mensuelles':}")
        print(f"  {'-'*63}")
        for _, row in df_pred.iterrows():
            print(f"  {row['mois']:10s} | Budget: {row['budget_total']:>12,.0f} DH | Fiab: {row['fiabilite']}%")
        
        print(f"\n  {'Budget Annuel '}{year_target}:")
        print(f"  {'-'*63}")
        print(f"  {'Débit total' if est_classe_6 else 'Crédit total'}: {budget_annuel_debit + budget_annuel_credit:>15,.2f} DH")
        print(f"  Fiabilité moy.: {fiabilite_moyenne:>15.0f} %")
        print(f"{'='*65}\n")
    
    # --- 6. RETOUR ---
    return {
        'account': account_code,
        'model': 'Moyenne Saisonnière Intelligente',
        'year_target': year_target,
        'years_used': list(years_to_use),
        'predictions_monthly': df_pred,
        'budget_annuel': {
            'debit': round(budget_annuel_debit, 2),
            'credit': round(budget_annuel_credit, 2),
            'total': round(budget_annuel_total, 2)
        },
        'fiabilite_globale': round(fiabilite_moyenne, 0)
    }


# --- TEST DIRECT ---
if __name__ == "__main__":
    # Test sur un compte
    annee_choisie = int(input("Entrez l'année à prédire (ex: 2026) : "))
    result = calculer_budget_previsionnel("612100102000", year_target=annee_choisie)
    if "error" in result:
        print(f"Erreur : {result['error']}")
    else:
        print("Calcul terminé avec succès")
        print(f"Budget annuel : {result['budget_annuel']['total']:,.0f} DH")