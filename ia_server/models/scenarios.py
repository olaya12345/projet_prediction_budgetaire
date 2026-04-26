# ============================================
# FICHIER : scenarios.py
# RÔLE    : Calcul de scénarios multiples
# ============================================

import pandas as pd
from models.smart_average_model import calculer_budget_previsionnel
import os

def calculer_scenarios(year_target, variation_pct=10):
    """
    Calcule 3 scénarios budgétaires :
    - Réaliste : prédictions normales
    - Optimiste : +variation_pct% sur les comptes produits (CA, subventions, etc.)
    - Pessimiste : -variation_pct% sur les comptes produits
    
    Paramètres:
        year_target   : int, année cible
        variation_pct : float, pourcentage de variation (défaut 10%)
    
    Retourne:
        dict avec les 3 scénarios + comparaison
    """
    
    print(f"\n{'='*70}")
    print(f"  CALCUL DES SCÉNARIOS — Année {year_target}")
    print(f"  Variation : ±{variation_pct}%")
    print(f"{'='*70}")
    
    # Liste des comptes (détection automatique)
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    data_path = os.path.join(project_root, "data", "data_for_ai.csv")
    df = pd.read_csv(data_path)
    tous_les_comptes = df['num_compte'].unique().tolist()
    
    # Identifier les comptes produits (7xxx) et dépenses (6xxx)
    comptes_produits = [c for c in tous_les_comptes if c.startswith('COMPTE_7')]
    comptes_depenses = [c for c in tous_les_comptes if c.startswith('COMPTE_6')]
    
    print(f"\n  📊 Comptes détectés :")
    print(f"     Produits (7xxx) : {len(comptes_produits)}")
    print(f"     Dépenses (6xxx) : {len(comptes_depenses)}")
    
    # ─── SCÉNARIO RÉALISTE (BASELINE) ─────────────────────────────
    print(f"\n  📈 Calcul scénario RÉALISTE...")
    
    realiste = {
        'nom': 'Réaliste',
        'description': 'Prévisions basées sur la moyenne historique sans ajustement',
        'total_depenses': 0,
        'total_produits': 0,
        'total_net': 0,
        'comptes': {}
    }
    
    for compte in tous_les_comptes:
        try: 
             result = calculer_budget_previsionnel(compte, year_target=year_target)
             if "error" in result:
                 print(f"     [!] Erreur {compte} : {result['error']}")
                 continue
             
             realiste['comptes'][compte] = result['budget_annuel']
             realiste['total_depenses'] += result['budget_annuel']['debit']
             realiste['total_produits'] += result['budget_annuel']['credit']
             print(f"     ✓ {compte} : {result['budget_annuel']['total']:,.0f} DH")
                 
        except Exception as e:
                 print(f"     ❌ Exception {compte} : {str(e)}")
                 continue

    realiste['total_net'] = realiste['total_produits'] - realiste['total_depenses']
    
    print(f"     ✅ Dépenses : {realiste['total_depenses']:,.0f} DH")
    print(f"     ✅ Produits : {realiste['total_produits']:,.0f} DH")
    print(f"     ✅ Net      : {realiste['total_net']:,.0f} DH")
    
    # ─── SCÉNARIO OPTIMISTE (+X% sur produits) ────────────────────
    print(f"\n  📈 Calcul scénario OPTIMISTE (+{variation_pct}% produits)...")
    
    optimiste = {
        'nom': 'Optimiste',
        'description': f'Hausse de {variation_pct}% sur les produits (CA, subventions, intérêts)',
        'total_depenses': realiste['total_depenses'],  # Dépenses identiques
        'total_produits': 0,
        'total_net': 0,
        'comptes': {}
    }
    
    for compte in tous_les_comptes:
        if compte in comptes_produits:
            # Produits : +variation_pct%
            base = realiste['comptes'][compte]
            optimiste['comptes'][compte] = {
                'debit': base['debit'],
                'credit': base['credit'] * (1 + variation_pct / 100),
                'total': (base['credit'] * (1 + variation_pct / 100)) - base['debit']
            }
            optimiste['total_produits'] += optimiste['comptes'][compte]['credit']
        else:
            # Dépenses : inchangées
            optimiste['comptes'][compte] = realiste['comptes'][compte]
    
    optimiste['total_net'] = optimiste['total_produits'] - optimiste['total_depenses']
    
    print(f"     ✅ Dépenses : {optimiste['total_depenses']:,.0f} DH")
    print(f"     ✅ Produits : {optimiste['total_produits']:,.0f} DH")
    print(f"     ✅ Net      : {optimiste['total_net']:,.0f} DH")
    
    # ─── SCÉNARIO PESSIMISTE (-X% sur produits) ───────────────────
    print(f"\n  📉 Calcul scénario PESSIMISTE (-{variation_pct}% produits)...")
    
    pessimiste = {
        'nom': 'Pessimiste',
        'description': f'Baisse de {variation_pct}% sur les produits (perte de clients, crise)',
        'total_depenses': realiste['total_depenses'],
        'total_produits': 0,
        'total_net': 0,
        'comptes': {}
    }
    
    for compte in tous_les_comptes:
        if compte in comptes_produits:
            # Produits : -variation_pct%
            base = realiste['comptes'][compte]
            pessimiste['comptes'][compte] = {
                'debit': base['debit'],
                'credit': base['credit'] * (1 - variation_pct / 100),
                'total': (base['credit'] * (1 - variation_pct / 100)) - base['debit']
            }
            pessimiste['total_produits'] += pessimiste['comptes'][compte]['credit']
        else:
            # Dépenses : inchangées
            pessimiste['comptes'][compte] = realiste['comptes'][compte]
    
    pessimiste['total_net'] = pessimiste['total_produits'] - pessimiste['total_depenses']
    
    print(f"     ✅ Dépenses : {pessimiste['total_depenses']:,.0f} DH")
    print(f"     ✅ Produits : {pessimiste['total_produits']:,.0f} DH")
    print(f"     ✅ Net      : {pessimiste['total_net']:,.0f} DH")
    
    # ─── COMPARAISON ───────────────────────────────────────────────
    print(f"\n  📊 COMPARAISON DES SCÉNARIOS :")
    print(f"  {'-'*68}")
    print(f"  {'Scénario':<15} | {'Produits':>15} | {'Dépenses':>15} | {'Net':>15}")
    print(f"  {'-'*68}")
    
    for sc in [realiste, optimiste, pessimiste]:
        icone = "📈" if sc['nom'] == "Optimiste" else "📉" if sc['nom'] == "Pessimiste" else "📊"
        print(f"  {icone} {sc['nom']:<12} | {sc['total_produits']:>15,.0f} | "
              f"{sc['total_depenses']:>15,.0f} | {sc['total_net']:>15,.0f}")
    
    print(f"  {'-'*68}")
    
    # Écart entre scénarios
    ecart_optimiste = optimiste['total_net'] - realiste['total_net']
    ecart_pessimiste = realiste['total_net'] - pessimiste['total_net']
    
    print(f"\n  💡 Écarts par rapport au scénario réaliste :")
    print(f"     Optimiste  : +{ecart_optimiste:,.0f} DH  ({ecart_optimiste/realiste['total_net']*100:.1f}%)")
    print(f"     Pessimiste : -{ecart_pessimiste:,.0f} DH  ({ecart_pessimiste/realiste['total_net']*100:.1f}%)")
    print(f"{'='*70}\n")
    
    # ─── RETOUR ────────────────────────────────────────────────────
    return {
        'year': year_target,
        'variation_appliquee': variation_pct,
        'scenarios': {
            'realiste': realiste,
            'optimiste': optimiste,
            'pessimiste': pessimiste
        },
        'comparaison': {
            'ecart_optimiste_dh': round(ecart_optimiste, 2),
            'ecart_pessimiste_dh': round(ecart_pessimiste, 2),
            'ecart_optimiste_pct': round(ecart_optimiste / realiste['total_net'] * 100, 2),
            'ecart_pessimiste_pct': round(ecart_pessimiste / realiste['total_net'] * 100, 2)
        }
    }


# ─── TEST DIRECT ───────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nCalcul des scenarios budgetaires")
    annee_choisie = int(input("entrez l'année cible : ") or 10)
    variation = int(input("entrez la variation en % (défaut 10) : "))
    resultats = calculer_scenarios(year_target=annee_choisie, variation_pct=variation)
    
    print("\n✅ Scénarios calculés avec succès !")
    print(f"\nRésumé :")
    print(f"  Réaliste   : {resultats['scenarios']['realiste']['total_net']:,.0f} DH")
    print(f"  Optimiste  : {resultats['scenarios']['optimiste']['total_net']:,.0f} DH")
    print(f"  Pessimiste : {resultats['scenarios']['pessimiste']['total_net']:,.0f} DH")