# ============================================
# FICHIER : main.py
# RÔLE    : API REST FastAPI pour les prédictions
# ============================================

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import sys
import os

# Ajouter le chemin parent pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.smart_average_model import calculer_budget_previsionnel
from models.consolidate_all import consolider_tous_les_comptes
import pandas as pd
import json
from datetime import datetime

# ─── INITIALISATION FASTAPI ──────────────────────────────────────
app = FastAPI(
    title="API de Prédiction Budgétaire SAP/IA",
    description="API locale pour prédire les budgets mensuels avec IA",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # Documentation alternative
)

# ─── CONFIGURATION CORS (pour React) ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── MODÈLES PYDANTIC (validation des requêtes) ─────────────────

class PredictAccountRequest(BaseModel):
    """Requête pour prédire un compte spécifique."""
    account_code: str = Field(..., example="COMPTE_7111", description="Code du compte SAP")
    year_target: int = Field(2026, ge=2026, le=2030, description="Année cible de prédiction")
    with_ia_comments: bool = Field(True, description="Générer les commentaires IA ?")

class ConsolidateRequest(BaseModel):
    """Requête pour consolider tous les comptes."""
    year_target: int = Field(2026, ge=2026, le=2030, description="Année cible")
    with_ia_comments: bool = Field(True, description="Générer les commentaires IA ?")

class HealthResponse(BaseModel):
    """Réponse du health check."""
    status: str
    timestamp: str
    message: str

# ─── ENDPOINTS ───────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API."""
    return {
        "message": "API de Prédiction Budgétaire SAP/IA",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "accounts": "/accounts",
            "predict_account": "/predict/account",
            "consolidate": "/predict/consolidate"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Vérifie que l'API fonctionne correctement.
    
    Returns:
        Status de l'API et timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "API opérationnelle. Tous les services sont actifs."
    }

@app.get("/accounts", tags=["Data"])
async def get_accounts():
    """
    Récupère la liste de tous les comptes SAP disponibles.
    
    Returns:
        Liste des comptes avec leurs noms
    """
    try:
        # Lire les données
        data_path = "../data/data_for_ai.csv"
        if not os.path.exists(data_path):
            raise HTTPException(
                status_code=404,
                detail="Fichier de données introuvable. Générez d'abord les données."
            )
        
        df = pd.read_csv(data_path)
        
        # Extraire les comptes uniques
        comptes = df[['num_compte']].drop_duplicates().sort_values('num_compte')
        
        # Ajouter les noms si disponibles
        if 'nom_compte' in df.columns:
            comptes = df[['num_compte', 'nom_compte']].drop_duplicates().sort_values('num_compte')
            accounts_list = comptes.to_dict('records')
        else:
            accounts_list = [{"num_compte": code} for code in comptes['num_compte'].tolist()]
        
        return {
            "total": len(accounts_list),
            "accounts": accounts_list
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des comptes : {str(e)}")

@app.post("/predict/account", tags=["Predictions"])
async def predict_account(request: PredictAccountRequest):
    """
    Calcule les prévisions budgétaires pour UN compte spécifique.
    
    Args:
        request: Requête contenant le code du compte et les paramètres
    
    Returns:
        Prédictions mensuelles, budget annuel, métriques, commentaires IA
    """
    try:
        print(f"\n🔍 Requête reçue : Prédiction pour {request.account_code}")
        
        # Appeler le modèle
        result = calculer_budget_previsionnel(
            account_code=request.account_code,
            year_target=request.year_target
        )
        
        # Vérifier les erreurs
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Convertir DataFrame en dict pour JSON
        predictions_list = result['predictions_monthly'].to_dict('records')
        
        # Générer commentaire IA si demandé
        commentaire_ia = None
        if request.with_ia_comments:
            from agent.ollama_agent import generer_commentaire
            
            # Prendre Janvier comme mois représentatif
            janvier = result['predictions_monthly'][result['predictions_monthly']['mois_num'] == 1].iloc[0]
            
            type_compte = "produit" if result['budget_annuel']['credit'] > result['budget_annuel']['debit'] else "dépense"
            
            commentaire_ia = generer_commentaire(
                compte=request.account_code,
                mois="Janvier",
                budget_predit=janvier['budget_total'],
                tendance_pct=janvier['tendance_pct'],
                fiabilite=janvier['fiabilite'],
                volatilite=janvier['volatilite'],
                anomalies=janvier['anomalies'],
                type_compte=type_compte
            )
        
        # Convertir numpy types en Python natifs
        years_used_clean = [int(y) for y in result['years_used']]
        
        # Réponse structurée
        return {
            "success": True,
            "account": request.account_code,
            "year": request.year_target,
            "model": result['model'],
            "predictions": {
                "monthly": predictions_list,
                "annual": result['budget_annuel']
            },
            "metrics": {
                "fiabilite_globale": int(result['fiabilite_globale']),
                "years_used": years_used_clean
            },
            "ia_comment": commentaire_ia,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction : {str(e)}")

@app.post("/predict/consolidate", tags=["Predictions"])
async def consolidate_all(request: ConsolidateRequest, background_tasks: BackgroundTasks):
    """
    Calcule les prévisions pour TOUS les comptes SAP et génère un rapport consolidé.
    
    ⚠️ Cette opération peut prendre 5-10 minutes si les commentaires IA sont activés.
    
    Args:
        request: Paramètres de consolidation
    
    Returns:
        Budget global consolidé avec détail par compte
    """
    try:
        print(f"\n🔍 Consolidation demandée pour l'année {request.year_target}")
        print(f"   Commentaires IA : {'Activés' if request.with_ia_comments else 'Désactivés'}")
        
        # Lancer la consolidation
        resultats = consolider_tous_les_comptes(
            year_target=request.year_target,
            with_ia_comments=request.with_ia_comments
        )
        
        # Convertir les DataFrames en dict
        comptes_dict = {}
        for compte, data in resultats['comptes'].items():
            comptes_dict[compte] = {
                'model': data['model'],
                'budget_annuel': data['budget_annuel'],
                'fiabilite_globale': data['fiabilite_globale'],
                'predictions_monthly': data['predictions_monthly'].to_dict('records'),
                'commentaire_ia': data.get('commentaire_ia', None)
            }
        
        # Réponse structurée
        return {
            "success": True,
            "year": request.year_target,
            "stats": resultats['stats'],
            "budget_global": resultats['budget_global'],
            "comptes": comptes_dict,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la consolidation : {str(e)}")

# ─── GESTION DES ERREURS GLOBALES ───────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "success": False,
        "error": "Ressource introuvable",
        "detail": str(exc.detail) if hasattr(exc, 'detail') else "Non trouvé",
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "success": False,
        "error": "Erreur interne du serveur",
        "detail": str(exc.detail) if hasattr(exc, 'detail') else "Erreur inconnue",
        "timestamp": datetime.now().isoformat()
    }

# ─── POINT D'ENTRÉE ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    print("="*60)
    print("  🚀 DÉMARRAGE DE L'API FASTAPI")
    print("="*60)
    print(f"  📍 URL locale    : http://localhost:8000")
    print(f"  📚 Documentation : http://localhost:8000/docs")
    print(f"  🔄 Rechargement  : Activé (mode dev)")
    print("="*60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en dev
        log_level="info"
    )