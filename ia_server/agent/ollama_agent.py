# ============================================
# FICHIER : ollama_agent.py
# RÔLE    : Génération de commentaires IA locaux
# ============================================

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"  # ou "mistral", "phi3", selon ce que tu as installé


def generer_commentaire(
    compte,
    mois,
    budget_predit,
    tendance_pct,
    fiabilite,
    volatilite,
    anomalies,
    type_compte="produit"
):
    """
    Génère un commentaire analytique en français avec Ollama.
    
    Paramètres:
        compte        : str, ex: "COMPTE_7111"
        mois          : str, ex: "Janvier"
        budget_predit : float, montant prédit
        tendance_pct  : float, tendance en %
        fiabilite     : int, score 0-100
        volatilite    : str, "Faible", "Moyenne", "Élevée"
        anomalies     : list, anomalies détectées
        type_compte   : str, "produit" ou "dépense"
    
    Retourne:
        str : commentaire généré par l'IA
    """
    
    # --- 1. CONSTRUIRE LE PROMPT ---
    type_fr = "recette" if type_compte == "produit" else "dépense"
    
    anomalies_txt = "Aucune anomalie détectée." if anomalies == ["Aucune"] else f"Attention : anomalies détectées en {', '.join(anomalies)}."
    
    tendance_txt = ""
    if tendance_pct > 5:
        tendance_txt = f"une hausse de {tendance_pct:.1f}%"
    elif tendance_pct < -5:
        tendance_txt = f"une baisse de {abs(tendance_pct):.1f}%"
    else:
        tendance_txt = "une stabilité"
    
    fiabilite_txt = ""
    if fiabilite >= 90:
        fiabilite_txt = "La fiabilité de cette prévision est excellente"
    elif fiabilite >= 70:
        fiabilite_txt = "La fiabilité de cette prévision est bonne"
    else:
        fiabilite_txt = "La fiabilité de cette prévision est modérée"
    
    prompt = f"""Tu es un analyste financier expert travaillant pour une entreprise marocaine. 
Rédige une analyse professionnelle et concise en français (maximum 4 phrases) pour le budget prévisionnel suivant :

Compte : {compte}
Type : {type_fr}
Mois : {mois} 2026
Budget prévu : {budget_predit:,.0f} DH
Tendance observée : {tendance_txt} par rapport aux années précédentes
Volatilité : {volatilite}
Fiabilité : {fiabilite}%
{anomalies_txt}

Ton analyse doit :
1. Commencer par le montant prévu
2. Expliquer la tendance de manière claire
3. Mentionner la fiabilité
4. Donner une recommandation si nécessaire

Réponds UNIQUEMENT avec l'analyse, sans introduction ni conclusion générique."""

    # --- 2. APPELER OLLAMA ---
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Peu créatif = plus factuel
                "num_predict": 200   # Limite à ~50 mots
            }
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            commentaire = result.get("response", "").strip()
            return commentaire
        else:
            return f"⚠️ Erreur Ollama ({response.status_code}). Commentaire non disponible."
    
    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama non disponible. Assurez-vous qu'Ollama est lancé (ollama serve)."
    except Exception as e:
        return f"⚠️ Erreur génération commentaire : {str(e)}"


def generer_commentaire_annuel(
    compte,
    annee,
    budget_total,
    fiabilite_moyenne,
    mois_le_plus_haut,
    mois_le_plus_bas,
    type_compte="produit"
):
    """
    Génère un commentaire sur le budget annuel complet.
    """
    
    type_fr = "recettes" if type_compte == "produit" else "dépenses"
    
    prompt = f"""Tu es un analyste financier expert. Rédige une synthèse professionnelle en français (maximum 5 phrases) :

Compte : {compte}
Année : {annee}
Budget annuel prévu : {budget_total:,.0f} DH ({type_fr})
Fiabilité moyenne : {fiabilite_moyenne:.0f}%
Mois le plus élevé : {mois_le_plus_haut}
Mois le plus faible : {mois_le_plus_bas}

La synthèse doit :
1. Présenter le budget annuel total
2. Identifier la saisonnalité (mois forts/faibles)
3. Mentionner la fiabilité globale
4. Donner une recommandation stratégique

Réponds UNIQUEMENT avec l'analyse."""

    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 250
            }
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            return f"⚠️ Erreur Ollama ({response.status_code})"
    
    except Exception as e:
        return f"⚠️ Erreur : {str(e)}"


# --- TEST DIRECT ---
if __name__ == "__main__":
    print("="*65)
    print("  TEST DE L'AGENT IA OLLAMA")
    print("="*65)
    
    # Test 1 : Commentaire mensuel
    print("\n📊 Test 1 — Commentaire mensuel :\n")
    comm = generer_commentaire(
        compte="COMPTE_7111",
        mois="Janvier",
        budget_predit=1043261,
        tendance_pct=8.3,
        fiabilite=100,
        volatilite="Faible",
        anomalies=["Aucune"],
        type_compte="produit"
    )
    print(comm)
    
    # Test 2 : Commentaire annuel
    print("\n\n📊 Test 2 — Commentaire annuel :\n")
    comm_annuel = generer_commentaire_annuel(
        compte="COMPTE_7111",
        annee=2026,
        budget_total=10117162,
        fiabilite_moyenne=99,
        mois_le_plus_haut="Janvier",
        mois_le_plus_bas="Juin",
        type_compte="produit"
    )
    print(comm_annuel)
    
    print("\n" + "="*65)