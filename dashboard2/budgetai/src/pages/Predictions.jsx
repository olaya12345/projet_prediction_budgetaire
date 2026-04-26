import { useState, useEffect } from "react";
import { Download, Loader2, TrendingUp, TrendingDown, Minus } from "lucide-react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import "./page.css";

import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend
} from "recharts";

const API_BASE = "http://localhost:8000";
const MOIS_SHORT = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun", "Jul", "Aout", "Sep", "Oct", "Nov", "Dec"];

// ── 1. LABELS DES MODÈLES ────────────────────────────────────────
const MODELES = [
    { value: "smart_average",  label: "Moyenne Saisonnière"   },
    { value: "prophet",        label: "Prophet"               },
    { value: "arima",          label: "ARIMA / SARIMA"        },
    { value: "random_forest",  label: "Random Forest"         },
    { value: "xgboost",        label: "XGBoost"               },
    { value: "auto",           label: "Auto — Meilleur MAPE ⚡" },
];

const formatNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return "0";
    return Number(num).toLocaleString("fr-FR", { maximumFractionDigits: 0 });
};

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="pred-tooltip">
            <p className="pred-tooltip-label">{label}</p>
            {payload.map((p, i) => (
                <p key={i} className="pred-tooltip-value" style={{ color: p.color }}>
                    {p.name}: {Number(p.value).toLocaleString("fr-FR")} DH
                </p>
            ))}
        </div>
    );
};

function Predictions() {
    const [classe,     setClasse]     = useState(6);
    const [yearTarget, setYearTarget] = useState(2027);
    const [modele,         setModele]         = useState("smart_average");
    const [modeleApplique, setModeleApplique] = useState("smart_average");
    const [loading,        setLoading]        = useState(false);
    const [data,       setData]       = useState(null);
    const [selectedCompte, setSelectedCompte] = useState(null);
    const [error,      setError]      = useState(null);

    useEffect(() => {
        fetchPredictions();
    }, [classe, yearTarget]);

    const fetchPredictions = async () => {
        setLoading(true);
        setError(null);
        setData(null);
        setSelectedCompte(null);

        try {
            const response = await fetch(`${API_BASE}/predictions/classe`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    classe:      classe,
                    year_target: yearTarget,
                    modele:      modele,     // ── 3a. ENVOI DU MODÈLE À L'API
                })
            });

            if (!response.ok) throw new Error("Erreur lors de la récupération des données");

            const result = await response.json();
            if (result.success) {
                setData(result.data);
                setModeleApplique(modele);
                if (result.data.comptes?.length > 0) {
                    setSelectedCompte(result.data.comptes[0]);
                }
            }
        } catch (err) {
            setError(err.message);
            console.error("Erreur API:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async () => {
        try {
            const response = await fetch(`${API_BASE}/export/excel/classe`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    classe:      classe,
                    year_target: yearTarget,
                    modele:      modele,     // ── 3b. ENVOI DU MODÈLE À L'EXPORT
                })
            });

            if (!response.ok) throw new Error("Erreur export");

            const blob = await response.blob();
            const url  = window.URL.createObjectURL(blob);
            const a    = document.createElement("a");
            a.href     = url;
            a.download = `predictions_classe${classe}_${modele}_${yearTarget}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            console.error("Erreur download:", err);
        }
    };

    const getChartData = () => {
        if (!selectedCompte || !data) return [];
        return MOIS_SHORT.map((mois, idx) => ({
            mois,
            realise:    selectedCompte.donnees_mensuelles[idx]?.realise    || 0,
            moyenne:    selectedCompte.donnees_mensuelles[idx]?.moyenne    || 0,
            prediction: selectedCompte.donnees_mensuelles[idx]?.prediction || 0,
        }));
    };

    const getVariationClass = (v) => v > 5 ? "var-positive" : v < -5 ? "var-negative" : "var-neutral";
    const getVariationIcon  = (v) =>
        v > 5  ? <TrendingUp   size={12} /> :
        v < -5 ? <TrendingDown size={12} /> :
                 <Minus        size={12} />;

    return (
        <section className="page-grid">
            <div className="pred-layout">

                {/* ── FORMULAIRE ── */}
                <Card className="pred-form-card">
                    <h3 className="chart-title" style={{ marginBottom: 20 }}>
                        Tableau de Prédiction Budgétaire
                    </h3>

                    <div className="pred-field">
                        <label className="ui-input-label">Classe</label>
                        <select className="ui-input" value={classe}
                            onChange={e => setClasse(Number(e.target.value))}>
                            <option value={6}>Classe 6 — Charges</option>
                            <option value={7}>Classe 7 — Produits</option>
                        </select>
                    </div>

                    <div className="pred-field">
                        <label className="ui-input-label">Année de Prédiction</label>
                        <select className="ui-input" value={yearTarget}
                            onChange={e => setYearTarget(Number(e.target.value))}>
                            {[2025, 2026, 2027, 2028, 2029, 2030].map(y => (
                                <option key={y} value={y}>{y}</option>
                            ))}
                        </select>
                    </div>

                    {/* ── SÉLECTEUR MODÈLE ── */}
                    <div className="pred-field">
                        <label className="ui-input-label">Modèle ML</label>
                        <select className="ui-input" value={modele}
                            onChange={e => setModele(e.target.value)}>
                            {MODELES.map(m => (
                                <option key={m.value} value={m.value}>{m.label}</option>
                            ))}
                        </select>
                        {modele === "auto" && (
                            <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
                                ⚡ Compare tous les modèles — peut prendre 2–5 min
                            </p>
                        )}
                        {modele === "arima" && (
                            <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
                                🐢 ARIMA est lent — comptez ~3 min
                            </p>
                        )}
                        {modele !== modeleApplique && (
                            <p style={{
                                fontSize: 11, color: "var(--gold)",
                                marginTop: 6, fontWeight: 600
                            }}>
                                ⚠️ Cliquez sur Actualiser pour appliquer
                            </p>
                        )}
                    </div>

                    <Button className="pred-submit" onClick={fetchPredictions} disabled={loading}>
                        {loading
                            ? <><Loader2 size={15} className="pred-spin" /> Chargement...</>
                            : "Actualiser"
                        }
                    </Button>

                    <Button variant="secondary" className="pred-submit"
                        style={{ marginTop: 12 }} onClick={handleDownload} disabled={!data}>
                        <Download size={15} /> Télécharger Excel
                    </Button>

                    {/* Résumé */}
                    {data && (
                        <div className="pred-summary">
                            {/* Badge modèle utilisé */}
                            <div className="pred-summary-item" style={{ gridColumn: "1 / -1" }}>
                                <span className="pred-summary-label">Modèle utilisé</span>
                                <span className="pred-summary-value" style={{
                                    color: "var(--gold)", fontSize: 12
                                }}>
                                    {data.modele_label}
                                </span>
                            </div>
                            <div className="pred-summary-item">
                                <span className="pred-summary-label">Comptes</span>
                                <span className="pred-summary-value">{data.nb_comptes}</span>
                            </div>
                            <div className="pred-summary-item">
                                <span className="pred-summary-label">Réalisé {data.annee_realise}</span>
                                <span className="pred-summary-value">
                                    {formatNumber(data.totaux_globaux.realise)} DH
                                </span>
                            </div>
                            <div className="pred-summary-item">
                                <span className="pred-summary-label">Prédiction {data.annee_prediction}</span>
                                <span className="pred-summary-value">
                                    {formatNumber(data.totaux_globaux.prediction)} DH
                                </span>
                            </div>
                            <div className="pred-summary-item">
                                <span className="pred-summary-label">Variation</span>
                                <span className={`pred-summary-value ${getVariationClass(data.totaux_globaux.variation)}`}>
                                    {data.totaux_globaux.variation > 0 ? "+" : ""}
                                    {data.totaux_globaux.variation.toFixed(1)}%
                                </span>
                            </div>
                        </div>
                    )}
                </Card>

                {/* ── RÉSULTATS ── */}
                <div className="pred-results">
                    {loading && (
                        <Card className="pred-empty">
                            <div className="pred-empty-inner">
                                <div className="pred-spinner-wrap">
                                    <div className="pred-spinner" />
                                </div>
                                <p className="pred-empty-title">Chargement des prédictions...</p>
                                {(modele === "auto" || modele === "arima") && (
                                    <p className="pred-empty-sub">
                                        {modele === "auto"
                                            ? "Comparaison de tous les modèles en cours..."
                                            : "ARIMA/SARIMA en cours d'entraînement..."}
                                    </p>
                                )}
                            </div>
                        </Card>
                    )}

                    {error && (
                        <Card className="pred-empty">
                            <div className="pred-empty-inner">
                                <p className="pred-empty-title" style={{ color: "var(--red)" }}>Erreur</p>
                                <p className="pred-empty-sub">{error}</p>
                            </div>
                        </Card>
                    )}

                    {!loading && !error && !data && (
                        <Card className="pred-empty">
                            <div className="pred-empty-inner">
                                <div className="pred-empty-icon">📊</div>
                                <p className="pred-empty-title">Sélectionnez une classe</p>
                                <p className="pred-empty-sub">
                                    Choisissez une classe, une année et un modèle, puis cliquez sur Actualiser.
                                </p>
                            </div>
                        </Card>
                    )}

                    {!loading && !error && data && (
                        <>
                            {/* Graphique */}
                            {selectedCompte && (
                                <Card>
                                    <h3 className="chart-title" style={{ marginBottom: 16 }}>
                                        {selectedCompte.account} — {selectedCompte.libelle}
                                        <span style={{
                                            marginLeft: 12, fontSize: 11,
                                            color: "var(--gold)", fontWeight: 400
                                        }}>
                                            [{selectedCompte.modele_utilise || data.modele_label}]
                                        </span>
                                    </h3>
                                    <div className="pred-chart-wrap">
                                        <ResponsiveContainer width="100%" height={280}>
                                            <BarChart data={getChartData()}
                                                margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3"
                                                    stroke="rgba(255,255,255,0.05)" vertical={false} />
                                                <XAxis dataKey="mois"
                                                    tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                                                    axisLine={false} tickLine={false} />
                                                <YAxis
                                                    tickFormatter={v => `${(v / 1000000).toFixed(1)}M`}
                                                    tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                                                    axisLine={false} tickLine={false} />
                                                <Tooltip content={<CustomTooltip />}
                                                    cursor={{ fill: "rgba(226,168,75,0.06)" }} />
                                                <Legend />
                                                <Bar dataKey="realise"
                                                    name={`Réalisé ${data.annee_realise}`}
                                                    fill="#6B7280" radius={[4, 4, 0, 0]} />
                                                <Bar dataKey="moyenne"
                                                    name="Moy 5 ans"
                                                    fill="#3B82F6" radius={[4, 4, 0, 0]} />
                                                <Bar dataKey="prediction"
                                                    name={`Préd. ${data.annee_prediction} (${data.modele_label})`}
                                                    fill="#F59E0B" radius={[4, 4, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </Card>
                            )}

                            {/* Tableau */}
                            <Card>
                                <h3 className="chart-title" style={{ marginBottom: 16 }}>
                                    Détails par Compte
                                </h3>
                                <div className="table-wrap" style={{ overflowX: "auto" }}>
                                    <table className="sap-table" style={{ fontSize: 11, minWidth: 1200 }}>
                                        <thead>
                                            <tr>
                                                <th style={{ position: "sticky", left: 0, background: "var(--bg-secondary)", zIndex: 2 }}>Compte</th>
                                                <th style={{ position: "sticky", left: 80, background: "var(--bg-secondary)", zIndex: 2 }}>Libellé</th>
                                                {MOIS_SHORT.map(mois => (
                                                    <th key={mois} colSpan={4}
                                                        style={{ textAlign: "center", background: "var(--bg-secondary)" }}>
                                                        {mois}
                                                    </th>
                                                ))}
                                                <th colSpan={4} style={{ textAlign: "center", background: "var(--teal)", color: "white" }}>
                                                    TOTAL
                                                </th>
                                            </tr>
                                            <tr>
                                                <th style={{ position: "sticky", left: 0, background: "var(--bg-secondary)", zIndex: 2 }}></th>
                                                <th style={{ position: "sticky", left: 80, background: "var(--bg-secondary)", zIndex: 2 }}></th>
                                                {MOIS_SHORT.map(mois => (
                                                    <DocumentFragment key={mois}>
                                                        <th style={{ fontSize: 9, color: "var(--text-muted)" }}>Réal</th>
                                                        <th style={{ fontSize: 9, color: "var(--text-muted)" }}>Moy 5a</th>
                                                        <th style={{ fontSize: 9, color: "var(--text-muted)" }}>Préd {data.annee_prediction}</th>
                                                        <th style={{ fontSize: 9, color: "var(--text-muted)" }}>Var%</th>
                                                    </DocumentFragment>
                                                ))}
                                                <th style={{ fontSize: 9, background: "var(--teal)", color: "white" }}>Réal</th>
                                                <th style={{ fontSize: 9, background: "var(--teal)", color: "white" }}>Moy 5a</th>
                                                <th style={{ fontSize: 9, background: "var(--teal)", color: "white" }}>Préd {data.annee_prediction}</th>
                                                <th style={{ fontSize: 9, background: "var(--teal)", color: "white" }}>Var%</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.comptes.map((compte) => (
                                                <tr key={compte.account}
                                                    onClick={() => setSelectedCompte(compte)}
                                                    className={selectedCompte?.account === compte.account ? "selected-row" : ""}
                                                    style={{ cursor: "pointer" }}>
                                                    <td style={{ position: "sticky", left: 0, background: "inherit", fontWeight: 600 }}>
                                                        {compte.account}
                                                    </td>
                                                    <td style={{ position: "sticky", left: 80, background: "inherit" }}>
                                                        {compte.libelle}
                                                    </td>
                                                    {compte.donnees_mensuelles.map((m, i) => (
                                                        <DocumentFragment key={i}>
                                                            <td className="mono">{formatNumber(m.realise)}</td>
                                                            <td className="mono" style={{ color: "var(--blue)" }}>{formatNumber(m.moyenne)}</td>
                                                            <td className="mono" style={{ color: "var(--gold)" }}>{formatNumber(m.prediction)}</td>
                                                            <td className={getVariationClass(m.variation)}
                                                                style={{ display: "flex", alignItems: "center", gap: 4 }}>
                                                                {getVariationIcon(m.variation)}
                                                                {m.variation > 0 ? "+" : ""}{m.variation.toFixed(1)}%
                                                            </td>
                                                        </DocumentFragment>
                                                    ))}
                                                    <td className="mono" style={{ fontWeight: 600 }}>{formatNumber(compte.totaux.realise)}</td>
                                                    <td className="mono" style={{ fontWeight: 600, color: "var(--blue)" }}>{formatNumber(compte.totaux.moyenne)}</td>
                                                    <td className="mono" style={{ fontWeight: 600, color: "var(--gold)" }}>{formatNumber(compte.totaux.prediction)}</td>
                                                    <td className={getVariationClass(compte.totaux.variation)}
                                                        style={{ display: "flex", alignItems: "center", gap: 4, fontWeight: 600 }}>
                                                        {getVariationIcon(compte.totaux.variation)}
                                                        {compte.totaux.variation > 0 ? "+" : ""}{compte.totaux.variation.toFixed(1)}%
                                                    </td>
                                                </tr>
                                            ))}

                                            {/* Total Row */}
                                            <tr style={{ fontWeight: 700, background: "var(--navy)" }}>
                                                <td colSpan={2} style={{ position: "sticky", left: 0, background: "var(--navy)", color: "white" }}>
                                                    TOTAL GLOBAL
                                                </td>
                                                {MOIS_SHORT.map((_, i) => (
                                                    <DocumentFragment key={i}>
                                                        <td /><td /><td /><td />
                                                    </DocumentFragment>
                                                ))}
                                                <td style={{ color: "white" }}>{formatNumber(data.totaux_globaux.realise)}</td>
                                                <td style={{ color: "white" }}>{formatNumber(data.totaux_globaux.moyenne)}</td>
                                                <td style={{ color: "white" }}>{formatNumber(data.totaux_globaux.prediction)}</td>
                                                <td style={{ display: "flex", alignItems: "center", gap: 4, color: "white" }}>
                                                    {getVariationIcon(data.totaux_globaux.variation)}
                                                    {data.totaux_globaux.variation > 0 ? "+" : ""}{data.totaux_globaux.variation.toFixed(1)}%
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </Card>
                        </>
                    )}
                </div>
            </div>
        </section>
    );
}

const DocumentFragment = ({ children }) => children;

export default Predictions;
