# ============================================
# FICHIER : ollama_agent.py
# RÔLE    : Génération de commentaires IA locaux (Techniques & Transparents)
# ============================================

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:4b"  # Ton modèle local


def generer_commentaire(
    compte,
    mois,
    annee,
    budget_predit,
    tendance_pct,
    fiabilite,
    volatilite,
    anomalies,
    type_compte="produit"
):
    # --- 1. PRÉPARATION DES VARIABLES ---
    type_fr = "recette" if type_compte == "produit" else "dépense"
    anomalies_txt = "Aucune anomalie historique détectée." if anomalies == ["Aucune"] else f"Anomalies historiques corrigées lors du lissage : {', '.join(anomalies)}."
    
    tendance_txt = ""
    if tendance_pct > 5:
        tendance_txt = f"croissance annuelle moyenne de +{tendance_pct:.1f}%"
    elif tendance_pct < -5:
        tendance_txt = f"décroissance annuelle moyenne de {tendance_pct:.1f}%"
    else:
        tendance_txt = f"stagnation relative ({tendance_pct:.1f}%)"

    # --- 2. CONSTRUIRE UN PROMPT TRÈS TECHNIQUE ---
    # C'est ici que la magie opère. On force l'IA à expliquer la méthodologie.
    prompt = f"""Tu es un Ingénieur Financier et Data Analyst Senior chez ATLANTIC HARVEST GROUP.
Ton rôle est d'expliquer avec précision et transparence le résultat généré par notre algorithme de prévision budgétaire. 

--- DONNÉES TECHNIQUES DU CALCUL ---
- Compte : {compte} ({type_fr})
- Période ciblée : {mois} {annee}
- Montant calculé : {budget_predit:,.0f} DH
- Tendance identifiée : {tendance_txt}
- Volatilité de la série temporelle : {volatilite}
- Taux de fiabilité du modèle (Basé sur le MAPE) : {fiabilite}%
- Données sources : Historique SAP de 2021 à 2025 (5 ans)
- Méthodologie : Modèle AutoML sélectionnant dynamiquement le meilleur algorithme (Prophet, SARIMA ou XGBoost) après apprentissage de la saisonnalité.
- {anomalies_txt}
------------------------------------

Rédige une analyse technique et experte (environ 5 phrases).
Tu DOIS IMPÉRATIVEMENT suivre cette structure :
1. Transparence du calcul : Commence par annoncer le montant exact et explique qu'il a été projeté en analysant les cycles historiques de 2021 à 2025 de ce mois spécifique.
2. Tendance & Saisonnalité : Explique l'impact de la tendance ({tendance_txt}) sur ce calcul.
3. Risque statistique : Analyse ce que la volatilité ({volatilite}) signifie pour l'écart-type de cette prédiction.
4. Fiabilité : Justifie techniquement le score de {fiabilite}% (ex: le modèle a-t-il bien capté la saisonnalité ?).
5. Recommandation : Donne un conseil concret pour le contrôle de gestion face à ce chiffre.

Adopte un ton mathématique, analytique et direct. Ne dis pas "il est important de", donne les faits bruts."""

    # --- 3. APPELER OLLAMA ---
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Très bas pour éviter qu'il invente (hallucination)
                "num_predict": 800   # Permet un texte un peu plus long et détaillé
            }
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            return f"⚠️ Erreur API Ollama ({response.status_code})."
            
    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama hors ligne."
    except Exception as e:
        return f"⚠️ Erreur : {str(e)}"


def generer_commentaire_annuel(
    compte,
    annee,
    budget_total,
    fiabilite_moyenne,
    mois_le_plus_haut,
    mois_le_plus_bas,
    type_compte="produit"
):
    type_fr = "recettes" if type_compte == "produit" else "dépenses"
    
    prompt = f"""Tu es le Directeur du Contrôle de Gestion de ATLANTIC HARVEST GROUP. 
Rédige une synthèse technique de la prédiction budgétaire annuelle.

--- DONNÉES GLOBALES ---
- Compte : {compte} ({type_fr})
- Année budgétaire : {annee}
- Total annuel projeté : {budget_total:,.0f} DH
- Pic saisonnier (Maximum) : {mois_le_plus_haut}
- Creux saisonnier (Minimum) : {mois_le_plus_bas}
- Fiabilité moyenne annuelle : {fiabilite_moyenne:.0f}%
- Historique d'entraînement : 2021 à 2025.

L'analyse doit :
1. Valider le chiffre total en mentionnant l'extrapolation sur la base 2021-2025.
2. Analyser l'écart type de la saisonnalité (contraste entre le mois de {mois_le_plus_haut} et {mois_le_plus_bas}).
3. Tirer une conclusion sur la robustesse globale du modèle (Fiabilité : {fiabilite_moyenne:.0f}%).
4. Émettre une directive pour l'allocation des flux de trésorerie sur cette année.

Ton ton doit être strict, financier et axé sur les mathématiques de prévision."""

    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 800
            }
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            return "Erreur Ollama."
            
    except Exception as e:
        return f"Erreur : {str(e)}"

# --- TEST DIRECT ---
if __name__ == "__main__":
    print("="*65)
    print("  TEST DE L'AGENT IA OLLAMA (VERSION EXPERT TECHNIQUE)")
    print("="*65)
    
    print("\n📊 Test mensuel :\n")
    comm = generer_commentaire(
        compte="COMPTE_6011",
        mois="Novembre",
        annee=2028,
        budget_predit=2450000,
        tendance_pct=4.2,
        fiabilite=92,
        volatilite="Moyenne",
        anomalies=["Aucune"],
        type_compte="dépense"
    )
    print(comm)