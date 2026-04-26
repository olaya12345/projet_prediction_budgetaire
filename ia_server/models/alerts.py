# ============================================
# FICHIER : alerts.py
# RÔLE    : Détection automatique d'alertes
# ============================================

import pandas as pd
import sys
import os

# Ajouter le chemin parent pour importer les modules

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from models.smart_average_model import calculer_budget_previsionnel
from models.consolidate_all import consolider_tous_les_comptes

def generer_alertes(year_target):
    """
    Génère automatiquement des alertes sur le budget.
    
    Types d'alertes :
    1. Marge critique (< 50k DH)
    2. Tendance négative (baisse > 5%)
    3. Volatilité élevée
    4. Déficit prévu
    
    Args:
        year_target: int, année à analyser
    
    Returns:
        Dict avec liste d'alertes et statistiques
    """
    
    print(f"\n{'='*70}")
    print(f"  GÉNÉRATION D'ALERTES AUTOMATIQUES — Année {year_target}")
    print(f"{'='*70}")
    
    alertes = []
    
    # --- 1. CONSOLIDATION ---
    print(f"\n  📊 Calcul du budget consolidé...")
    resultats = consolider_tous_les_comptes(year_target=year_target, with_ia_comments=False)
    
    budget_global = resultats['budget_global']
    
    # --- 2. ALERTES SUR LE BUDGET NET MENSUEL ---
    print(f"\n  🔍 Analyse des mois critiques...")
    
    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    
    for i, mois in enumerate(mois_noms):
        net = budget_global['net_mensuel'][i]
        
        # Alerte CRITIQUE : Marge < 50k
        if 0 < net < 50000:
            alertes.append({
                'type': 'MARGE_CRITIQUE',
                'severite': 'HAUTE',
                'mois': mois,
                'valeur': round(net, 0),
                'seuil': 50000,
                'message': f"⚠️ {mois} : Marge très faible ({net:,.0f} DH). Risque de déficit en cas d'imprévu."
            })
        
        # Alerte DÉFICIT : Net négatif
        if net < 0:
            alertes.append({
                'type': 'DEFICIT',
                'severite': 'CRITIQUE',
                'mois': mois,
                'valeur': round(net, 0),
                'seuil': 0,
                'message': f"🔴 {mois} : DÉFICIT prévu de {abs(net):,.0f} DH !"
            })
    
    # --- 3. ALERTES SUR LES COMPTES INDIVIDUELS ---
    print(f"\n  🔍 Analyse des comptes individuels...")
    
    for compte, data in resultats['comptes'].items():
        df_pred = data['predictions_monthly']
        
        # Calcul de la tendance moyenne
        tendance_moy = df_pred['tendance_pct'].mean()
        
        # Alerte TENDANCE NÉGATIVE
        if tendance_moy < -5:
            alertes.append({
                'type': 'TENDANCE_NEGATIVE',
                'severite': 'MOYENNE',
                'compte': compte,
                'valeur': round(tendance_moy, 2),
                'seuil': -5,
                'message': f"📉 {compte} : Tendance négative forte ({tendance_moy:.1f}% par an)"
            })
        
        # Alerte VOLATILITÉ ÉLEVÉE
        mois_volatiles = df_pred[df_pred['volatilite'] == 'Élevée']
        if len(mois_volatiles) >= 3:
            alertes.append({
                'type': 'VOLATILITE_ELEVEE',
                'severite': 'FAIBLE',
                'compte': compte,
                'valeur': len(mois_volatiles),
                'seuil': 3,
                'message': f"📊 {compte} : {len(mois_volatiles)} mois avec volatilité élevée. Prédictions moins fiables."
            })
        
        # Alerte FIABILITÉ FAIBLE
        fiabilite_moy = df_pred['fiabilite'].mean()
        if fiabilite_moy < 70:
            alertes.append({
                'type': 'FIABILITE_FAIBLE',
                'severite': 'MOYENNE',
                'compte': compte,
                'valeur': round(fiabilite_moy, 0),
                'seuil': 70,
                'message': f"⚠️ {compte} : Fiabilité faible ({fiabilite_moy:.0f}%). Prédictions incertaines."
            })
    
    # --- 4. ALERTES SUR LE BUDGET ANNUEL ---
    print(f"\n  🔍 Analyse du budget annuel...")
    
    # Alerte DÉFICIT ANNUEL
    if budget_global['net_annuel'] < 0:
        alertes.append({
            'type': 'DEFICIT_ANNUEL',
            'severite': 'CRITIQUE',
            'valeur': round(budget_global['net_annuel'], 0),
            'seuil': 0,
            'message': f"🔴 Budget {year_target} : DÉFICIT ANNUEL de {abs(budget_global['net_annuel']):,.0f} DH !"
        })
    
    # Alerte MARGE FAIBLE ANNUELLE
    elif budget_global['net_annuel'] < 500000:
        alertes.append({
            'type': 'MARGE_FAIBLE_ANNUELLE',
            'severite': 'HAUTE',
            'valeur': round(budget_global['net_annuel'], 0),
            'seuil': 500000,
            'message': f"⚠️ Budget {year_target} : Marge annuelle faible ({budget_global['net_annuel']:,.0f} DH). Peu de réserve."
        })
    
    # --- 5. TRI PAR SÉVÉRITÉ ---
    severite_order = {'CRITIQUE': 0, 'HAUTE': 1, 'MOYENNE': 2, 'FAIBLE': 3}
    alertes_triees = sorted(alertes, key=lambda x: severite_order[x['severite']])
    
    # --- 6. STATISTIQUES ---
    nb_critique = len([a for a in alertes if a['severite'] == 'CRITIQUE'])
    nb_haute = len([a for a in alertes if a['severite'] == 'HAUTE'])
    nb_moyenne = len([a for a in alertes if a['severite'] == 'MOYENNE'])
    nb_faible = len([a for a in alertes if a['severite'] == 'FAIBLE'])
    
    # --- 7. RAPPORT ---
    print(f"\n{'='*70}")
    print(f"  RAPPORT D'ALERTES — Année {year_target}")
    print(f"{'='*70}")
    print(f"\n  📊 Résumé :")
    print(f"     Total alertes   : {len(alertes_triees)}")
    print(f"     🔴 Critiques    : {nb_critique}")
    print(f"     [!] Hautes       : {nb_haute}")
    print(f"     📊 Moyennes     : {nb_moyenne}")
    print(f"     💡 Faibles      : {nb_faible}")
    
    print(f"\n  🚨 Détail des alertes :")
    print(f"  {'-'*68}")
    
    if len(alertes_triees) == 0:
        print(f"     ✅ Aucune alerte ! Le budget semble sain.")
    else:
        for alerte in alertes_triees:
            print(f"\n  [{alerte['severite']}] {alerte['type']}")
            print(f"     {alerte['message']}")
    
    print(f"\n{'='*70}\n")
    
    # --- 8. RETOUR ---
    return {
        'year': year_target,
        'total_alertes': len(alertes_triees),
        'par_severite': {
            'critique': nb_critique,
            'haute': nb_haute,
            'moyenne': nb_moyenne,
            'faible': nb_faible
        },
        'alertes': alertes_triees
    }


# --- TEST DIRECT ---
if __name__ == "__main__":
    print("\n🚨 SYSTÈME D'ALERTES BUDGÉTAIRES")
    annee_choisie = int(input("Entrez l'année à analyser : "))
    
    resultats = generer_alertes(year_target=annee_choisie)
    
    print(f"\n✅ Génération d'alertes terminée !")
    print(f"\nRésumé :")
    print(f"  Total alertes : {resultats['total_alertes']}")
    print(f"  Critiques     : {resultats['par_severite']['critique']}")
    print(f"  Hautes        : {resultats['par_severite']['haute']}")
    print(f"  Moyennes      : {resultats['par_severite']['moyenne']}")
    print(f"  Faibles       : {resultats['par_severite']['faible']}")