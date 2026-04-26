import { useState } from "react";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import Card from "../components/ui/Card";
import "./page.css";

const ANNEES    = [2026, 2027, 2028, 2029, 2030];
const SEVERITES = ["Toutes", "CRITIQUE", "HAUTE", "INFO"];


const MOCK_ALERTS = [
  {
    severite: "CRITIQUE",
    titre: "Déficit prévu en Juin 2028",
    description: "Le compte COMPTE_6310 présente un déficit prévu de -76 121 DH. Une révision budgétaire est recommandée.",
    compte: "COMPTE_6310",
    mois: "Juin 2028",
  },
  {
    severite: "CRITIQUE",
    titre: "Déficit prévu en Décembre 2028",
    description: "Le compte COMPTE_6500 présente un déficit prévu de -46 218 DH. Action immédiate requise.",
    compte: "COMPTE_6500",
    mois: "Décembre 2028",
  },
  {
    severite: "HAUTE",
    titre: "Marge très serrée en Février",
    description: "Le compte COMPTE_6200 affiche une marge de seulement 10 353 DH en Février 2028.",
    compte: "COMPTE_6200",
    mois: "Février 2028",
  },
  {
    severite: "HAUTE",
    titre: "Hausse inhabituelle des charges",
    description: "Les charges du compte COMPTE_6420 progressent de +12% par rapport à l'année précédente.",
    compte: "COMPTE_6420",
    mois: "Mars 2028",
  },
  {
    severite: "HAUTE",
    titre: "Marge serrée en Janvier",
    description: "Le compte COMPTE_6200 affiche une marge de 41 940 DH en Janvier 2028. À surveiller.",
    compte: "COMPTE_6200",
    mois: "Janvier 2028",
  },
  {
    severite: "INFO",
    titre: "Tendance haussière confirmée",
    description: "Le compte COMPTE_7111 affiche une tendance haussière stable de +8.3% sur 5 ans.",
    compte: "COMPTE_7111",
    mois: "Annuel 2028",
  },
  {
    severite: "INFO",
    titre: "Prédiction stable sur COMPTE_7130",
    description: "Le compte COMPTE_7130 montre une évolution linéaire sans anomalie détectée.",
    compte: "COMPTE_7130",
    mois: "Annuel 2028",
  },
];
const ALERT_CFG = {
  CRITIQUE: { icon: <AlertTriangle size={16} />, iconCls: "alert-icon-critique", badgeCls: "badge-danger",  label: "Critique" },
  HAUTE:    { icon: <AlertCircle   size={16} />, iconCls: "alert-icon-haute",    badgeCls: "badge-warning", label: "Haute"    },
  INFO:     { icon: <Info          size={16} />, iconCls: "alert-icon-info",     badgeCls: "badge-info",    label: "Info"     },
};
const KPI_DATA = (alerts) => [
  { label: "Total Alertes",    value: alerts.length,                                           tone: "gold"    },
  { label: "Critiques",        value: alerts.filter(a => a.severite === "CRITIQUE").length,    tone: "danger"  },
  { label: "Haute Priorité",   value: alerts.filter(a => a.severite === "HAUTE").length,       tone: "warning" },
  { label: "Informations",     value: alerts.filter(a => a.severite === "INFO").length,        tone: "info"    },
];
export default function Alerts(){
    const [annee,    setAnnee]    = useState(2028);
      const [severite, setSeverite] = useState("Toutes");
    
      const filtered = MOCK_ALERTS.filter(
        a => severite === "Toutes" || a.severite === severite
      );
    
      const kpis = KPI_DATA(MOCK_ALERTS);
    
      return(
         <section className="page-grid">
           <div className="alerts-page-head">
             <div>
          <h2 className="chart-title">Alertes Budgétaires</h2>
          <p className="chart-sub">Détection automatique des déficits, marges critiques et tendances</p>
        </div>
        <div className="alerts-filters">
            <select
            className="chart-select"
            value={annee}
            onChange={e => setAnnee(Number(e.target.value))}
          >
            {ANNEES.map(a => <option key={a} value={a}>{a}</option>)}
          </select>

           <select
            className="chart-select"
            value={severite}
            onChange={e => setSeverite(e.target.value)}
          >
            {SEVERITES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

        </div>
           </div>

            {/* KPI cards */}
                 <div className="kpi-grid">
                   {kpis.map((k) => (
                     <Card key={k.label} className="kpi-card">
                       <p className="kpi-title">{k.label}</p>
                       <p className={`kpi-value kpi-value-${k.tone}`}>{k.value}</p>
                       <p className="kpi-sub">Pour {annee}</p>
                     </Card>
                   ))}
                 </div>
           
           <Card>
            <div className="alerts-list-head">
                <h3 className="chart-title">
                   {severite === "Toutes" ? "Toutes les alertes" : `Alertes — ${severite}`}
                </h3>
                 <span className="table-badge badge-neutral">{filtered.length} alerte{filtered.length > 1 ? "s" : ""}</span>
            </div>

            {filtered.length === 0 ? (
                 <div className="table-empty">Aucune alerte pour ce filtre.</div>
            ) : (
                <div className="alerts-full-list">
                    {["CRITIQUE", "HAUTE", "INFO"].map(sev => {
                         const group = filtered.filter(a => a.severite === sev);
              if (group.length === 0) return null;
              const cfg = ALERT_CFG[sev];
              return(
               <div className="alerts-group">
                <div className="alerts-group-label">
                     <span className={`table-badge ${cfg.badgeCls}`}>
                      {cfg.label}
                    </span>
                    <span className="alerts-group-count">{group.length} alerte{group.length > 1 ? "s" : ""}</span>
                    </div>  
                     {group.map((alert, i) => (
                    <div key={i} className="alert-row">
                      <div className={`alert-row-icon ${cfg.iconCls}`}>
                        {cfg.icon}
                      </div>
                      <div className="alert-row-body">
                        <div className="alert-row-top">
                          <span className="alert-row-titre">{alert.titre}</span>
                        </div>
                        <p className="alert-row-desc">{alert.description}</p>
                        <div className="alert-row-meta">
                          <span className="account-code">{alert.compte}</span>
                          <span className="alert-row-mois">{alert.mois}</span>
                        </div>
                      </div>
                    </div>
                  ))}    
                 </div>
              );
                    })}
                </div>
            )}
           </Card>
         </section>
      );
}