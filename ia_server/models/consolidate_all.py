# ============================================
# FICHIER : consolidate_all.py
# RÔLE    : Calcule TOUS les comptes + rapport global
# ============================================

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.smart_average_model import calculer_budget_previsionnel
from agent.ollama_agent import generer_commentaire, generer_commentaire_annuel
import pandas as pd
import json

# Liste de tous les comptes SAP
TOUS_LES_COMPTES = [
    "COMPTE_6011",  # Achats matières premières
    "COMPTE_6141",  # Loyers
    "COMPTE_6161",  # Assurances
    "COMPTE_6165",  # Electricité et eau
    "COMPTE_6171",  # Transport
    "COMPTE_6174",  # Téléphone
    "COMPTE_6176",  # Honoraires
    "COMPTE_6178",  # Fournitures bureau
    "COMPTE_6185",  # Maintenance
    "COMPTE_6190",  # Formation
    "COMPTE_6200",  # Salaires
    "COMPTE_6210",  # Charges sociales
    "COMPTE_7111",  # Chiffre d'affaires
    "COMPTE_7120",  # Subventions
    "COMPTE_7300",  # Intérêts bancaires
]

def consolider_tous_les_comptes(year_target=2026, with_ia_comments=True):
    """
    Calcule les prévisions pour TOUS les comptes SAP.
    
    Retourne un rapport complet avec :
    - Prédictions mensuelles par compte
    - Budget annuel par compte
    - Budget net global (produits - dépenses)
    - Commentaires IA (optionnel)
    """
    
    print("\n" + "="*80)
    print(f"  CONSOLIDATION BUDGÉTAIRE COMPLÈTE — Année {year_target}")
    print("="*80)
    
    resultats_par_compte = {}
    budget_global = {
        'depenses_mensuelles': [0] * 12,
        'produits_mensuels': [0] * 12,
        'net_mensuel': [0] * 12,
        'depenses_annuel': 0,
        'produits_annuel': 0,
        'net_annuel': 0
    }
    
    comptes_traites = 0
    comptes_erreurs = 0
    
    # --- 1. CALCULER CHAQUE COMPTE ---
    for compte in TOUS_LES_COMPTES:
        print(f"\n{'─'*80}")
        print(f"  Traitement : {compte}")
        
        result = calculer_budget_previsionnel(compte, year_target=year_target)
        
        if "error" in result:
            print(f"  ⚠️ Erreur : {result['error']}")
            comptes_erreurs += 1
            continue
        
        comptes_traites += 1
        resultats_par_compte[compte] = result
        
        # Accumuler dans le budget global
        df_pred = result['predictions_monthly']
        
        for idx, row in df_pred.iterrows():
            mois_idx = row['mois_num'] - 1
            budget_global['depenses_mensuelles'][mois_idx] += row['budget_debit']
            budget_global['produits_mensuels'][mois_idx] += row['budget_credit']
            budget_global['net_mensuel'][mois_idx] += (row['budget_credit'] - row['budget_debit'])
        
        budget_global['depenses_annuel'] += result['budget_annuel']['debit']
        budget_global['produits_annuel'] += result['budget_annuel']['credit']
        budget_global['net_annuel'] += result['budget_annuel']['credit'] - result['budget_annuel']['debit']
        
        # --- 2. GÉNÉRER COMMENTAIRE IA (optionnel) ---
        if with_ia_comments:
            print(f"\n  🤖 Génération commentaire IA...")
            
            # Prendre le mois le plus représentatif (Janvier)
            janvier = df_pred[df_pred['mois_num'] == 1].iloc[0]
            
            type_compte = "produit" if result['budget_annuel']['credit'] > result['budget_annuel']['debit'] else "dépense"
            
            commentaire = generer_commentaire(
                compte=compte,
                mois="Janvier",
                budget_predit=janvier['budget_total'],
                tendance_pct=janvier['tendance_pct'],
                fiabilite=janvier['fiabilite'],
                volatilite=janvier['volatilite'],
                anomalies=janvier['anomalies'],
                type_compte=type_compte
            )
            
            result['commentaire_ia'] = commentaire
            print(f"  💬 {commentaire[:100]}...")
    
    # --- 3. RAPPORT CONSOLIDÉ ---
    print("\n" + "="*80)
    print(f"  RAPPORT CONSOLIDÉ {year_target}")
    print("="*80)
    print(f"\n  📊 Statistiques :")
    print(f"     Comptes traités : {comptes_traites}/{len(TOUS_LES_COMPTES)}")
    print(f"     Comptes en erreur : {comptes_erreurs}")
    
    print(f"\n  💰 Budget Annuel Global :")
    print(f"     Total Dépenses  : {budget_global['depenses_annuel']:>15,.2f} DH")
    print(f"     Total Produits  : {budget_global['produits_annuel']:>15,.2f} DH")
    print(f"     ───────────────────────────────────")
    
    if budget_global['net_annuel'] >= 0:
        print(f"     EXCÉDENT        : {budget_global['net_annuel']:>15,.2f} DH ✅")
    else:
        print(f"     DÉFICIT         : {budget_global['net_annuel']:>15,.2f} DH ⚠️")
    
    # --- 4. BUDGET NET PAR MOIS ---
    print(f"\n  📅 Budget Net Mensuel :")
    print(f"     {'Mois':<12} | {'Dépenses':>15} | {'Produits':>15} | {'Net':>15} | Statut")
    print(f"     {'-'*75}")
    
    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    
    for i in range(12):
        dep = budget_global['depenses_mensuelles'][i]
        prod = budget_global['produits_mensuels'][i]
        net = budget_global['net_mensuel'][i]
        statut = "✅" if net >= 0 else "⚠️"
        
        print(f"     {mois_noms[i]:<12} | {dep:>15,.0f} | {prod:>15,.0f} | {net:>15,.0f} | {statut}")
    
    print("\n" + "="*80)
    
    # --- 5. GÉNÉRER COMMENTAIRE GLOBAL IA ---
    if with_ia_comments:
        print(f"\n  🤖 Génération synthèse globale IA...")
        
        mois_max = mois_noms[budget_global['net_mensuel'].index(max(budget_global['net_mensuel']))]
        mois_min = mois_noms[budget_global['net_mensuel'].index(min(budget_global['net_mensuel']))]
        
        commentaire_global = generer_commentaire_annuel(
            compte="Consolidation globale",
            annee=year_target,
            budget_total=budget_global['net_annuel'],
            fiabilite_moyenne=95,
            mois_le_plus_haut=mois_max,
            mois_le_plus_bas=mois_min,
            type_compte="net"
        )
        
        print(f"\n  💬 Synthèse globale :")
        print(f"     {commentaire_global}")
    
    # --- 6. RETOUR ---
    return {
        'year': year_target,
        'comptes': resultats_par_compte,
        'budget_global': budget_global,
        'stats': {
            'comptes_traites': comptes_traites,
            'comptes_erreurs': comptes_erreurs
        }
    }


def exporter_json(resultats, filename="budget_consolide.json"):
    """Exporte les résultats en JSON."""
    # Convertir les DataFrames en dict
    export = {
        'year': resultats['year'],
        'budget_global': resultats['budget_global'],
        'stats': resultats['stats'],
        'comptes': {}
    }
    
    for compte, data in resultats['comptes'].items():
        export['comptes'][compte] = {
            'model': data['model'],
            'budget_annuel': data['budget_annuel'],
            'fiabilite_globale': data['fiabilite_globale'],
            'predictions_monthly': data['predictions_monthly'].to_dict('records'),
            'commentaire_ia': data.get('commentaire_ia', '')
        }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2, ensure_ascii=False)
    
    print(f"\n  💾 Export JSON : {filename}")


# --- LANCEMENT ---
if __name__ == "__main__":
    print("\n" + "🚀 DÉMARRAGE CONSOLIDATION COMPLÈTE")
    
    resultats = consolider_tous_les_comptes(year_target=2026, with_ia_comments=True)
    
    # Exporter en JSON
    exporter_json(resultats, "../../data/budget_consolide_2026.json")
    
    print("\n✅ CONSOLIDATION TERMINÉE !")