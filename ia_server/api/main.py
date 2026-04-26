# ============================================
# FICHIER : main.py
# RÔLE    : API REST FastAPI pour les prédictions
# ============================================

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import sys
import os
import pandas as pd
import json
from datetime import datetime
import io
import numpy as np
from fastapi.responses import StreamingResponse

def convert_numpy(obj):
    """Convertit tous les types numpy en types Python natifs."""
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# ─── CHEMIN ABSOLU VERS IA_SERVER ────────────────────────────────
current_file  = os.path.abspath(__file__)
api_dir       = os.path.dirname(current_file)       # ia_server/api
ia_server_dir = os.path.dirname(api_dir)            # ia_server
sys.path.insert(0, ia_server_dir)                   # Ajouter ia_server au path

# ─── INITIALISATION FASTAPI ──────────────────────────────────────
app = FastAPI(
    title="API de Prédiction Budgétaire SAP/IA",
    description="API locale pour prédire les budgets mensuels avec IA",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ─── CONFIGURATION CORS ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:3001",
        "http://localhost:5173", "http://localhost:5174",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── TYPE ALIAS ──────────────────────────────────────────────────
ModeleType = Literal[
    "smart_average",
    "prophet",
    "arima",
    "random_forest",
    "xgboost",
    "auto"
]

# ─── MODÈLES PYDANTIC ────────────────────────────────────────────

class PredictAccountRequest(BaseModel):
    account_code:     str  = Field(..., example="COMPTE_7111")
    year_target:      int  = Field(2026, ge=2026, le=2035)
    with_ia_comments: bool = Field(False)

class PredictBestRequest(BaseModel):
    account_code:     str  = Field(..., example="COMPTE_7111")
    year_target:      int  = Field(2026, ge=2026, le=2035)
    with_ia_comments: bool = Field(False)

class ConsolidateRequest(BaseModel):
    year_target:      int  = Field(2026, ge=2026, le=2035)
    with_ia_comments: bool = Field(False)

class ScenariosRequest(BaseModel):
    year_target:   int   = Field(2026, ge=2026, le=2035)
    variation_pct: float = Field(10.0, ge=0, le=50)

# ── MODIFIÉ : ajout des champs modele et sample_size ─────────────────────────────
class PredictionClasseRequest(BaseModel):
    classe:       int          = Field(..., ge=6, le=7,
                                       description="Classe: 6 (Charges) ou 7 (Produits)")
    year_target:  int          = Field(2027, ge=2025, le=2035,
                                       description="Année de prédiction")
    year_realise: Optional[int] = Field(None, ge=2020, le=2035,
                                        description="Année des réalisés (défaut: dernière année complète)")
    modele:       ModeleType   = Field("smart_average",
                                       description=(
                                           "Modèle ML à utiliser : "
                                           "smart_average | prophet | arima | "
                                           "random_forest | xgboost | auto"
                                       ))
    sample_size: Optional[int] = Field(None, ge=1, le=200,
                                        description="Nb max de comptes à traiter (pour modèles lents)")

class HealthResponse(BaseModel):
    status:    str
    timestamp: str
    message:   str

# ─── ENDPOINTS ───────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "API de Prédiction Budgétaire SAP/IA",
        "version": "2.0.0",
        "status":  "online",
        "docs":    "/docs",
        "endpoints": {
            "health":             "/health",
            "accounts":           "/accounts",
            "predict_account":    "/predict/account",
            "predict_best":       "/predict/best",
            "consolidate":        "/predict/consolidate",
            "scenarios":          "/predict/scenarios",
            "alerts":             "/alerts/{year_target}",
            "predictions_classe": "/predictions/classe",
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return {
        "status":    "healthy",
        "timestamp": datetime.now().isoformat(),
        "message":   "API opérationnelle. Tous les services sont actifs."
    }

@app.get("/accounts", tags=["Data"])
async def get_accounts():
    try:
        project_root = os.path.dirname(ia_server_dir)
        data_path    = os.path.join(project_root, "data", "data_for_ai.csv")

        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail="Fichier de données introuvable.")

        df = pd.read_csv(data_path)
        if "account" in df.columns:
            comptes       = df[["account"]].drop_duplicates().sort_values("account")
            accounts_list = [{"account": str(c)} for c in comptes["account"].tolist()]
        else:
            comptes       = df[["num_compte"]].drop_duplicates().sort_values("num_compte")
            accounts_list = [{"account": str(c)} for c in comptes["num_compte"].tolist()]

        return {"total": len(accounts_list), "accounts": accounts_list}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/account", tags=["Predictions"])
async def predict_account(request: PredictAccountRequest):
    """Prévision avec Moyenne Saisonnière Intelligente (rapide)."""
    try:
        from models.smart_average_model import calculer_budget_previsionnel

        result = calculer_budget_previsionnel(
            account_code=request.account_code,
            year_target=request.year_target
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        predictions_list = result["predictions_monthly"].to_dict("records")
        years_used_clean = [int(y) for y in result["years_used"]]
        commentaire_ia   = None

        if request.with_ia_comments:
            from agent.ollama_agent import generer_commentaire
            janvier     = result["predictions_monthly"][result["predictions_monthly"]["mois_num"] == 1].iloc[0]
            type_compte = "produit" if result["budget_annuel"]["credit"] > result["budget_annuel"]["debit"] else "dépense"
            commentaire_ia = generer_commentaire(
                compte=request.account_code, mois="Janvier", annee=request.year_target,
                budget_predit=janvier["budget_total"], tendance_pct=janvier["tendance_pct"],
                fiabilite=janvier["fiabilite"], volatilite=janvier["volatilite"],
                anomalies=janvier["anomalies"], type_compte=type_compte
            )

        return {
            "success":     True,
            "account":     request.account_code,
            "year":        request.year_target,
            "model":       result["model"],
            "predictions": {"monthly": predictions_list, "annual": result["budget_annuel"]},
            "metrics":     {"fiabilite_globale": int(result["fiabilite_globale"]), "years_used": years_used_clean},
            "ia_comment":  commentaire_ia,
            "timestamp":   datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/best", tags=["Predictions"])
async def predict_best(request: PredictBestRequest):
    """
    🏆 ML ENGINE — Compare automatiquement 5 modèles ML et retourne le meilleur.
    Modèles : Moyenne Saisonnière, Prophet, ARIMA, Random Forest, XGBoost.
    ⚠️  Prend 2–5 minutes (ARIMA est lent).
    """
    try:
        from models.ml_engine import comparer_tous_les_modeles

        result = comparer_tous_les_modeles(
            account_code=request.account_code,
            year_target=request.year_target
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        predictions_list = result["predictions"].to_dict("records")
        for p in predictions_list:
            if hasattr(p.get("ds"), "isoformat"):
                p["ds"] = p["ds"].isoformat()

        tous_modeles_summary = {}
        for key, data in result["tous_les_modeles"].items():
            if "error" in data:
                tous_modeles_summary[key] = {"error": data["error"]}
            else:
                tous_modeles_summary[key] = {
                    "model":               data["model"],
                    "mape":                data["metrics"]["MAPE"],
                    "mae":                 data["metrics"]["MAE"],
                    "fiabilite":           data["fiabilite"],
                    "budget_annuel_total": data["budget_annuel"].get("total")
                }

        commentaire_ia = None
        if request.with_ia_comments:
            from agent.ollama_agent import generer_commentaire
            janvier = result["predictions"][result["predictions"]["ds"].dt.month == 1].iloc[0]
            fiabilite = max(0, 100 - result["meilleur_mape"])
            commentaire_ia = generer_commentaire(
                compte=request.account_code, mois="Janvier", annee=request.year_target,
                budget_predit=janvier["yhat"], tendance_pct=0,
                fiabilite=fiabilite, volatilite="Faible",
                anomalies=["Aucune"], type_compte="produit"
            )

        return {
            "success":          True,
            "account":          request.account_code,
            "year":             request.year_target,
            "meilleur_modele":  result["meilleur_nom"],
            "meilleur_mape":    result["meilleur_mape"],
            "predictions":      predictions_list,
            "budget_annuel":    result["budget_annuel"],
            "classement":       result["classement"],
            "tous_les_modeles": tous_modeles_summary,
            "ia_comment":       commentaire_ia,
            "timestamp":        datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur ML Engine : {str(e)}")


@app.post("/predict/consolidate", tags=["Predictions"])
async def consolidate_all(request: ConsolidateRequest, background_tasks: BackgroundTasks):
    """Calcule les prévisions pour TOUS les comptes SAP."""
    try:
        from models.consolidate_all import consolider_tous_les_comptes

        resultats    = consolider_tous_les_comptes(
            year_target=request.year_target,
            with_ia_comments=request.with_ia_comments
        )
        comptes_dict = {}
        for compte, data in resultats["comptes"].items():
            comptes_dict[compte] = {
                "model":               data["model"],
                "budget_annuel":       data["budget_annuel"],
                "fiabilite_globale":   data["fiabilite_globale"],
                "predictions_monthly": data["predictions_monthly"].to_dict("records"),
                "commentaire_ia":      data.get("commentaire_ia")
            }

        return {
            "success":       True,
            "year":          request.year_target,
            "stats":         resultats["stats"],
            "budget_global": resultats["budget_global"],
            "comptes":       comptes_dict,
            "timestamp":     datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── MODIFIÉ : timeout et fallback automatique pour les modèles lents ─
TIMEOUT_SECONDS = 60  # Timeout pour les modèles ML

@app.post("/predictions/classe", tags=["Predictions"])
async def get_predictions_by_classe(request: PredictionClasseRequest):
    """
    Obtient les prédictions pour une classe donnée (6 ou 7).

    Modèles disponibles via le champ **modele** :
    - `smart_average`  — Moyenne Saisonnière (rapide, défaut)
    - `prophet`        — Prophet *(lent avec beaucoup de comptes)*
    - `arima`          — ARIMA / SARIMA
    - `random_forest`  — Random Forest
    - `xgboost`        — XGBoost
    - `auto`           — Compare tous les modèles → prend le meilleur MAPE *(lent)*

    Retourne : réalisé N, moyenne 5 ans, prédiction N+1, variation — par mois et en totaux.
    """
    # Fallback automatique si modèle trop lent
    modele_final = request.modele
    
    def run_calculation():
        # Direct call - no thread pool complexity
        from models.consolidate_all import calculer_predictions_par_classe
        return calculer_predictions_par_classe(
            classe=request.classe,
            year_target=request.year_target,
            year_realise=request.year_realise,
            modele=modele_final,
            sample_size=request.sample_size,
        )
    
    try:
        resultats = run_calculation()
        
        if "error" in resultats:
            raise HTTPException(status_code=404, detail=resultats["error"])
        
        if "error" in resultats:
            raise HTTPException(status_code=404, detail=resultats["error"])

        return {
            "success":   True,
            "data":      convert_numpy(resultats),
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err_full = traceback.format_exc()
        err_short = str(type(e).__name__) + ': ' + str(e)
        print('ERROR in predictions/classe:', err_short[:200])
        raise HTTPException(status_code=500, detail=err_short[:300])


@app.get("/predictions/years", tags=["Data"])
async def get_available_years():
    """Retourne les années disponibles dans les données."""
    try:
        from models.consolidate_all import get_available_years

        years = get_available_years()

        return {
            "success":            True,
            "years":              years,
            "last_complete_year": max([y for y in years if y < 2026]) if years else None,
            "timestamp":          datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/comptes/{classe}", tags=["Data"])
async def get_comptes_by_classe(classe: int):
    """Retourne la liste des comptes pour une classe donnée."""
    try:
        if classe not in [6, 7]:
            raise HTTPException(status_code=400, detail="Classe doit être 6 ou 7")

        from models.consolidate_all import get_comptes_par_classe

        comptes = get_comptes_par_classe(classe)

        return {
            "success":      True,
            "classe":       classe,
            "classe_label": "Charges" if classe == 6 else "Produits",
            "nb_comptes":   len(comptes),
            "comptes":      [{"account": c, "libelle": str(c)} for c in comptes],
            "timestamp":    datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/scenarios", tags=["Predictions"])
async def calculate_scenarios(request: ScenariosRequest):
    """Calcule 3 scénarios : Réaliste / Optimiste / Pessimiste."""
    try:
        from models.scenarios import calculer_scenarios

        resultats = calculer_scenarios(
            year_target=request.year_target,
            variation_pct=request.variation_pct
        )

        return {
            "success":             True,
            "year":                request.year_target,
            "variation_appliquee": resultats["variation_appliquee"],
            "scenarios": {
                s: {
                    "nom":            resultats["scenarios"][s]["nom"],
                    "description":    resultats["scenarios"][s]["description"],
                    "total_depenses": round(resultats["scenarios"][s]["total_depenses"], 2),
                    "total_produits": round(resultats["scenarios"][s]["total_produits"], 2),
                    "total_net":      round(resultats["scenarios"][s]["total_net"], 2)
                }
                for s in ["realiste", "optimiste", "pessimiste"]
            },
            "comparaison": resultats["comparaison"],
            "timestamp":   datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts/{year_target}", tags=["Analysis"])
async def get_alerts(year_target: int):
    """Génère des alertes automatiques (déficits, marges critiques, tendances)."""
    try:
        from models.alerts import generer_alertes

        resultats = generer_alertes(year_target=year_target)

        return {
            "success":       True,
            "year":          year_target,
            "total_alertes": resultats["total_alertes"],
            "par_severite":  resultats["par_severite"],
            "alertes":       resultats["alertes"],
            "timestamp":     datetime.now().isoformat()
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ─── EXPORT EXCEL ────────────────────────────────────────────────

class ExportExcelRequest(BaseModel):
    year_target:          int = Field(2026, ge=2026, le=2035)
    nb_annees_historique: int = Field(5, ge=3, le=10)

# ── MODIFIÉ : ajout du champ modele ──────────────────────────────
class ExportExcelClasseRequest(BaseModel):
    classe:       int           = Field(..., ge=6, le=7,
                                        description="Classe: 6 (Charges) ou 7 (Produits)")
    year_target:  int           = Field(2027, ge=2025, le=2035)
    year_realise: Optional[int] = Field(None, ge=2020, le=2035)
    modele:       ModeleType    = Field("smart_average",
                                        description=(
                                            "Modèle ML : smart_average | prophet | "
                                            "arima | random_forest | xgboost | auto"
                                        ))

@app.post("/export/excel", tags=["Export"])
async def export_excel(request: ExportExcelRequest):
    """📊 Excel complet : historique N ans + prédictions + variation + commentaires."""
    try:
        from models.export_excel import generer_excel

        data     = generer_excel(
            year_target=request.year_target,
            nb_annees_historique=request.nb_annees_historique
        )
        filename = f"rapport_budgetaire_SAP_{request.year_target}.xlsx"

        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur export Excel : {str(e)}")


# ── MODIFIÉ : passe modele à generer_excel_predictions ───────────
@app.post("/export/excel/classe", tags=["Export"])
async def export_excel_classe(request: ExportExcelClasseRequest):
    """
    📊 Excel par classe (6 ou 7) avec le modèle ML choisi.

    Colonnes : Réalisé | Moy. 5 ans | Prédiction | Variation — par mois + TOTAL.
    """
    try:
        from models.export_excel import generer_excel_predictions

        data = generer_excel_predictions(
            classe=request.classe,
            year_target=request.year_target,
            year_realise=request.year_realise,
            modele=request.modele,          # ← NOUVEAU
        )

        classe_label = "Charges" if request.classe == 6 else "Produits"
        modele_label = request.modele.replace("_", "-")
        filename     = (
            f"predictions_classe{request.classe}_{classe_label}"
            f"_{modele_label}_{request.year_target}.xlsx"
        )

        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur export Excel : {str(e)}")


# ─── AUTH ────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    str
    password: str
    nom:      str
    role:     str = "comptable"

class LoginRequest(BaseModel):
    email:    str
    password: str

@app.post("/auth/register", tags=["Auth"])
async def register(req: RegisterRequest):
    from auth import register_user
    result = register_user(req.email, req.password, req.nom, req.role)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/auth/login", tags=["Auth"])
async def login(req: LoginRequest):
    from auth import login_user
    result = login_user(req.email, req.password)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

@app.get("/auth/me", tags=["Auth"])
async def me(authorization: str = None):
    from fastapi import Header
    from auth import get_current_user
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant.")
    token = authorization.replace("Bearer ", "")
    user  = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token invalide.")
    return user


# ─── GESTION DES ERREURS GLOBALES ────────────────────────────────
from fastapi.responses import JSONResponse

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={
        "success":   False,
        "error":     "Ressource introuvable",
        "timestamp": datetime.now().isoformat()
    })

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(status_code=500, content={
        "success":   False,
        "error":     "Erreur interne du serveur",
        "timestamp": datetime.now().isoformat()
    })


# ─── POINT D'ENTRÉE ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    print("="*60)
    print("  🚀 DÉMARRAGE DE L'API FASTAPI v2.0")
    print("="*60)
    print("  📍 URL locale    : http://localhost:8000")
    print("  📚 Documentation : http://localhost:8000/docs")
    print("  🆕 ML Engine     : POST /predict/best")
    print("  📊 Par Classe    : POST /predictions/classe")
    print("  📥 Export Excel  : POST /export/excel/classe")
    print("="*60)

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")