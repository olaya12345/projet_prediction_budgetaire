  import { useState } from "react";
import { FileSpreadsheet, Download, FileText, Clock, CheckCircle } from "lucide-react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import "./page.css";

const COMPTES = [
  "Tous les comptes",
  "COMPTE_7111", "COMPTE_7121", "COMPTE_7130",
  "COMPTE_6011", "COMPTE_6141", "COMPTE_6200",
  "COMPTE_6310", "COMPTE_6420", "COMPTE_6500",
];

const ANNEES  = [2026, 2027, 2028, 2029, 2030];
const FORMATS = ["Excel (.xlsx)", "PDF (.pdf)"];

const MOCK_HISTORY = [
  { id: 1, nom: "rapport_budgetaire_SAP_2028.xlsx", compte: "Tous les comptes", annee: 2028, format: "Excel", date: "19/03/2026 09:47", statut: "success" },
  { id: 2, nom: "rapport_budgetaire_SAP_2027.xlsx", compte: "COMPTE_7111",      annee: 2027, format: "Excel", date: "18/03/2026 14:22", statut: "success" },
  { id: 3, nom: "rapport_budgetaire_SAP_2026.pdf",  compte: "Tous les comptes", annee: 2026, format: "PDF",   date: "17/03/2026 10:05", statut: "success" },
];

export default function Reports() {
  const [compte,   setCompte]   = useState("Tous les comptes");
  const [annee,    setAnnee]    = useState(2028);
  const [format,   setFormat]   = useState("Excel (.xlsx)");
  const [loading,  setLoading]  = useState(false);
  const [history,  setHistory]  = useState(MOCK_HISTORY);

  const isExcel = format.includes("Excel");

  const handleGenerate = async () => {
    setLoading(true);
    try {
      // Appel réel API export Excel
      const res = await fetch("http://localhost:8000/export/excel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("budgetai_token")}`,
        },
        body: JSON.stringify({ year_target: annee, nb_annees_historique: 5 }),
      });

      if (!res.ok) throw new Error("Erreur serveur");

      const blob = await res.blob();
      const url  = window.URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `rapport_budgetaire_SAP_${annee}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);

      // Ajouter à l'historique
      const newEntry = {
        id:      history.length + 1,
        nom:     `rapport_budgetaire_SAP_${annee}.xlsx`,
        compte,
        annee,
        format:  "Excel",
        date:    new Date().toLocaleDateString("fr-FR") + " " + new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }),
        statut:  "success",
      };
      setHistory(prev => [newEntry, ...prev]);

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page-grid">

      {/* En-tête */}
      <div>
        <h2 className="chart-title">Rapports</h2>
        <p className="chart-sub">Générez et téléchargez vos rapports budgétaires SAP</p>
      </div>

      {/* Formulaire génération */}
      <Card>
        <h3 className="chart-title" style={{ marginBottom: 20 }}>
          Générer un rapport
        </h3>

        <div className="reports-form-grid">
          <div className="scen-form-field">
            <label className="ui-input-label">Compte SAP</label>
            <select
              className="chart-select"
              value={compte}
              onChange={e => setCompte(e.target.value)}
            >
              {COMPTES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="scen-form-field">
            <label className="ui-input-label">Année</label>
            <select
              className="chart-select"
              value={annee}
              onChange={e => setAnnee(Number(e.target.value))}
            >
              {ANNEES.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>

          <div className="scen-form-field">
            <label className="ui-input-label">Format</label>
            <select
              className="chart-select"
              value={format}
              onChange={e => setFormat(e.target.value)}
            >
              {FORMATS.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
        </div>

        {/* Aperçu du rapport */}
        <div className="reports-preview">
          <div className="reports-preview-icon">
            {isExcel ? <FileSpreadsheet size={28} color="var(--success)" /> : <FileText size={28} color="var(--danger)" />}
          </div>
          <div>
            <p className="reports-preview-name">
              rapport_budgetaire_SAP_{annee}{isExcel ? ".xlsx" : ".pdf"}
            </p>
            <p className="reports-preview-sub">
              {compte} · {annee} · {isExcel ? "3 feuilles (Résumé, Historique, Évolution)" : "Rapport complet mis en page"}
            </p>
          </div>
        </div>

        <Button
          onClick={handleGenerate}
          disabled={loading || !isExcel}
          style={{ marginTop: 4 }}
        >
          {loading
            ? <><div className="pred-spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Génération...</>
            : <><Download size={15} /> Télécharger le rapport</>
          }
        </Button>

        {!isExcel && (
          <p className="reports-pdf-note">
            ⚠ L'export PDF sera disponible prochainement. Utilisez Excel pour l'instant.
          </p>
        )}
      </Card>

      {/* Historique */}
      <Card>
        <div className="alerts-list-head">
          <h3 className="chart-title">Historique des rapports</h3>
          <span className="table-badge badge-neutral">{history.length} rapport{history.length > 1 ? "s" : ""}</span>
        </div>

        {history.length === 0 ? (
          <div className="table-empty">Aucun rapport généré pour l'instant.</div>
        ) : (
          <div className="table-wrap">
            <table className="sap-table">
              <thead>
                <tr>
                  <th>Fichier</th>
                  <th>Compte</th>
                  <th>Année</th>
                  <th>Format</th>
                  <th>Date</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {history.map(r => (
                  <tr key={r.id}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        {r.format === "Excel"
                          ? <FileSpreadsheet size={14} color="var(--success)" />
                          : <FileText size={14} color="var(--danger)" />
                        }
                        <span className="mono" style={{ fontSize: 12, color: "var(--text-primary)" }}>
                          {r.nom}
                        </span>
                      </div>
                    </td>
                    <td><span className="account-code">{r.compte}</span></td>
                    <td className="mono">{r.annee}</td>
                    <td>
                      <span className={`table-badge ${r.format === "Excel" ? "badge-success" : "badge-danger"}`}>
                        {r.format}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 5, color: "var(--text-muted)", fontSize: 12 }}>
                        <Clock size={12} /> {r.date}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 5, color: "var(--success)", fontSize: 12 }}>
                        <CheckCircle size={13} /> Généré
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

    </section>
  );
}
