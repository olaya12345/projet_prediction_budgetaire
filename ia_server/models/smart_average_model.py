# ============================================
# FICHIER : smart_average_model.py
# RÔLE    : Moyenne saisonnière intelligente
# ============================================

import pandas as pd
import numpy as np
from scipy import stats
import os

def calculer_budget_previsionnel(account_code, year_target=2026, min_years=3, max_years=5):
    """
    Calcule le budget prévisionnel par mois en utilisant la moyenne des années précédentes.
    
    Méthode :
    1. Prendre les N dernières années (min 3, max 5)
    2. Grouper par mois calendaire (Janvier, Février, etc.)
    3. Calculer moyenne + détection de tendance automatique
    4. Appliquer facteur de croissance détecté
    5. Calculer intervalle de confiance et fiabilité
    
    Paramètres:
        account_code : str, ex: "COMPTE_7111"
        year_target  : int, année cible (défaut 2026)
        min_years    : int, minimum d'années historiques
        max_years    : int, maximum d'années historiques
        
    Retourne:
        dict avec toutes les infos + prédictions mensuelles
    """
    
    # --- 1. CHARGER LES DONNÉES ---
    data_path = "../../data/data_for_ai.csv"
    if not os.path.exists(data_path):
        return {"error": "Fichier data_for_ai.csv introuvable"}

    df = pd.read_csv(data_path)
    df_acc = df[df['num_compte'] == account_code].copy()
    
    if len(df_acc) < 12:
        return {"error": f"Pas assez de données pour {account_code}"}
    
    # Préparer les colonnes
    df_acc['date'] = pd.to_datetime(df_acc['date'])
    df_acc['year'] = df_acc['date'].dt.year
    df_acc['month'] = df_acc['date'].dt.month
    df_acc['month_name'] = df_acc['date'].dt.strftime('%B')
    
    # Séparer débit et crédit
    df_acc['montant_debit'] = df_acc.apply(
        lambda x: x['montant_final'] if x['type'] == 'dépense' else 0, axis=1
    )
    df_acc['montant_credit'] = df_acc.apply(
        lambda x: x['montant_final'] if x['type'] == 'produit' else 0, axis=1
    )
    
    # --- 2. SÉLECTIONNER LES ANNÉES HISTORIQUES ---
    available_years = sorted(df_acc['year'].unique())
    n_years = min(max_years, len(available_years))
    n_years = max(min_years, n_years)
    
    years_to_use = available_years[-n_years:]  # Les N dernières années
    df_hist = df_acc[df_acc['year'].isin(years_to_use)].copy()
    
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
            continue
        
        # Moyennes débit/crédit
        debits_hist  = month_data['montant_debit'].values
        credits_hist = month_data['montant_credit'].values
        
        mean_debit  = np.mean(debits_hist)
        mean_credit = np.mean(credits_hist)
        
        # --- DÉTECTION AUTOMATIQUE DE TENDANCE ---
        # On regarde si ça monte ou ça descend au fil des années
        years_in_month = month_data['year'].values
        montants_total = month_data['montant_final'].values
        
        if len(years_in_month) >= 2:
            # Régression linéaire : tendance = pente
            slope, intercept, r_value, p_value, std_err = stats.linregress(years_in_month, montants_total)
            
            # Calculer la tendance annuelle en %
            if mean_debit + mean_credit > 0:
                tendance_pct = (slope / (mean_debit + mean_credit)) * 100
            else:
                tendance_pct = 0
            
            # Appliquer la tendance pour l'année cible
            years_ahead = year_target - years_in_month[-1]
            facteur_croissance = 1 + (tendance_pct / 100) * years_ahead
            
            # Limiter le facteur pour éviter les aberrations
            facteur_croissance = np.clip(facteur_croissance, 0.7, 1.5)
        else:
            tendance_pct = 0
            facteur_croissance = 1.0
        
        # Budget prévisionnel avec tendance
        budget_debit  = mean_debit * facteur_croissance
        budget_credit = mean_credit * facteur_croissance
        
        # --- INTERVALLE DE CONFIANCE (95%) ---
        std_debit  = np.std(debits_hist) if len(debits_hist) > 1 else 0
        std_credit = np.std(credits_hist) if len(credits_hist) > 1 else 0
        
        # Intervalle = moyenne ± 1.96 * écart-type (95% confiance)
        conf_debit_low   = max(0, budget_debit - 1.96 * std_debit)
        conf_debit_high  = budget_debit + 1.96 * std_debit
        conf_credit_low  = max(0, budget_credit - 1.96 * std_credit)
        conf_credit_high = budget_credit + 1.96 * std_credit
        
        # --- VOLATILITÉ ---
        # Coefficient de variation = écart-type / moyenne
        cv_debit  = (std_debit / budget_debit * 100) if budget_debit > 0 else 0
        cv_credit = (std_credit / budget_credit * 100) if budget_credit > 0 else 0
        
        if cv_debit > 30 or cv_credit > 30:
            volatilite = "Élevée"
        elif cv_debit > 15 or cv_credit > 15:
            volatilite = "Moyenne"
        else:
            volatilite = "Faible"
        
        # --- DÉTECTION D'ANOMALIES ---
        # Outliers = valeurs > 3 écarts-types de la moyenne
        anomalies = []
        for idx, val in enumerate(montants_total):
            z_score = (val - np.mean(montants_total)) / (np.std(montants_total) + 1e-6)
            if abs(z_score) > 3:
                year_anomaly = years_in_month[idx]
                anomalies.append(f"{year_anomaly} (valeur exceptionnelle)")
        
        # --- SCORE DE FIABILITÉ ---
        # Basé sur : nombre d'années, volatilité, R² de la tendance
        score = 100
        
        # Pénalité si peu d'années
        if len(years_in_month) < 3:
            score -= 20
        
        # Pénalité si volatilité élevée
        if volatilite == "Élevée":
            score -= 30
        elif volatilite == "Moyenne":
            score -= 15
        
        # Bonus si tendance claire (R² élevé)
        if len(years_in_month) >= 2:
            if r_value**2 > 0.8:
                score += 10
        
        # Pénalité si anomalies
        score -= len(anomalies) * 10
        
        score = max(0, min(100, score))
        
        # --- STOCKER LES RÉSULTATS ---
        month_name = pd.to_datetime(f"{year_target}-{month_num:02d}-01").strftime('%B')
        
        predictions.append({
            'mois_num':        month_num,
            'mois':            month_name,
            'budget_debit':    round(budget_debit, 2),
            'budget_credit':   round(budget_credit, 2),
            'budget_total':    round(budget_debit + budget_credit, 2),
            'tendance_pct':    round(tendance_pct, 2),
            'intervalle_debit':  f"[{conf_debit_low:,.0f} - {conf_debit_high:,.0f}]",
            'intervalle_credit': f"[{conf_credit_low:,.0f} - {conf_credit_high:,.0f}]",
            'volatilite':      volatilite,
            'fiabilite':       score,
            'anomalies':       anomalies if anomalies else ["Aucune"],
            'n_annees':        len(years_in_month)
        })
    
    # --- 4. BUDGET ANNUEL ---
    df_pred = pd.DataFrame(predictions)
    
    budget_annuel_debit  = df_pred['budget_debit'].sum()
    budget_annuel_credit = df_pred['budget_credit'].sum()
    budget_annuel_total  = budget_annuel_debit + budget_annuel_credit
    
    fiabilite_moyenne = df_pred['fiabilite'].mean()
    
    # --- 5. RAPPORT ---
    print(f"\n  {'Prévisions mensuelles':}")
    print(f"  {'-'*63}")
    for _, row in df_pred.iterrows():
        print(f"  {row['mois']:10s} | Débit: {row['budget_debit']:>12,.0f} DH | "
              f"Crédit: {row['budget_credit']:>12,.0f} DH | Fiab: {row['fiabilite']}%")
    
    print(f"\n  {'Budget Annuel '}{year_target}:")
    print(f"  {'-'*63}")
    print(f"  Débit total   : {budget_annuel_debit:>15,.2f} DH")
    print(f"  Crédit total  : {budget_annuel_credit:>15,.2f} DH")
    print(f"  TOTAL         : {budget_annuel_total:>15,.2f} DH")
    print(f"  Fiabilité moy.: {fiabilite_moyenne:>15.0f} %")
    print(f"{'='*65}\n")
    
    # --- 6. RETOUR ---
    return {
        'account':             account_code,
        'model':               'Moyenne Saisonnière Intelligente',
        'year_target':         year_target,
        'years_used':          list(years_to_use),
        'predictions_monthly': df_pred,
        'budget_annuel': {
            'debit':  round(budget_annuel_debit, 2),
            'credit': round(budget_annuel_credit, 2),
            'total':  round(budget_annuel_total, 2)
        },
        'fiabilite_globale':   round(fiabilite_moyenne, 0)
    }


# --- TEST DIRECT ---
if __name__ == "__main__":
    # Test sur le Chiffre d'Affaires
    result = calculer_budget_previsionnel("COMPTE_7111", year_target=2026)
    
    if "error" in result:
        print(f"Erreur : {result['error']}")
    else:
        print("✅ Calcul terminé avec succès !")
        print(f"\nRésumé :")
        print(f"  Budget annuel 2026 : {result['budget_annuel']['total']:,.0f} DH")
        print(f"  Fiabilité globale  : {result['fiabilite_globale']}%")