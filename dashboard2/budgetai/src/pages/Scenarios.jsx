import { useState } from "react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import "./page.css";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from "recharts";

const ANNEES = [2026, 2027, 2028, 2029, 2030];

const MOCK_SCENARIOS = {
  pessimiste: {
    label: "Pessimiste",
    icon: "📉",
    description: "Baisse de 10% des produits, dépenses stables",
    depenses: 8990000,
    produits: 9500000,
    net: 510000,
    color: "var(--danger)",
  },
  realiste: {
    label: "Réaliste",
    icon: "📊",
    description: "Prévision baseline, tendance historique",
    depenses: 8990000,
    produits: 10560000,
    net: 1570000,
    color: "var(--info)",
  },
  optimiste: {
    label: "Optimiste",
    icon: "📈",
    description: "Hausse de 10% des produits, dépenses stables",
    depenses: 8990000,
    produits: 11610000,
    net: 2620000,
    color: "var(--success)",
  },
};

const CHART_DATA = [
  { name: "Dépenses",     Pessimiste: 8990, Réaliste: 8990, Optimiste: 8990 },
  { name: "Produits",     Pessimiste: 9500, Réaliste: 10560, Optimiste: 11610 },
  { name: "Résultat Net", Pessimiste: 510,  Réaliste: 1570,  Optimiste: 2620 },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="pred-tooltip">
      <p className="pred-tooltip-label">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, fontFamily: "var(--font-mono)", fontSize: 13, marginTop: 3 }}>
          {p.name} : {Number(p.value).toLocaleString("fr-FR")} k DH
        </p>
      ))}
    </div>
  );
};

export default function Scenarios() {
  const [annee,     setAnnee]     = useState(2028);
  const [variation, setVariation] = useState(10);
  const [shown,     setShown]     = useState(false);

  const handleCalculer = () => setShown(true);

  const fmt = (n) => n.toLocaleString("fr-FR") + " DH";

  return (
    <section className="page-grid">

      {/* En-tête + formulaire */}
      <Card>
        <div className="scen-form-head">
          <div>
            <h3 className="chart-title">Analyse de Scénarios</h3>
            <p className="chart-sub">Comparez les projections budgétaires selon 3 hypothèses</p>
          </div>
          <div className="scen-form-controls">
            <div className="scen-form-field">
              <label className="ui-input-label">Année cible</label>
              <select
                className="chart-select"
                value={annee}
                onChange={e => setAnnee(Number(e.target.value))}
              >
                {ANNEES.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <div className="scen-form-field">
              <label className="ui-input-label">Variation ± {variation}%</label>
              <input
                type="range"
                min={1} max={30}
                value={variation}
                onChange={e => setVariation(Number(e.target.value))}
                className="scen-range"
              />
            </div>
            <Button onClick={handleCalculer}>
              Calculer les scénarios
            </Button>
          </div>
        </div>
      </Card>

      {/* 3 cartes scénarios */}
      {shown && (
        <>
          <div className="scen-cards-grid">
            {Object.entries(MOCK_SCENARIOS).map(([key, sc]) => (
              <Card
                key={key}
                className={`scen-card ${key === "realiste" ? "scen-card-active" : ""}`}
              >
                <div className="scen-icon">{sc.icon}</div>
                <h3 className="scen-name" style={{ color: sc.color }}>{sc.label}</h3>
                <p className="scen-desc">{sc.description}</p>

                <div className="scen-net" style={{ color: sc.color }}>
                  +{fmt(sc.net)}
                </div>

                <div className="scen-rows">
                  <div className="scen-row">
                    <span>Dépenses</span>
                    <span className="mono" style={{ color: "var(--danger)" }}>
                      {fmt(sc.depenses)}
                    </span>
                  </div>
                  <div className="scen-row">
                    <span>Produits</span>
                    <span className="mono" style={{ color: "var(--success)" }}>
                      {fmt(sc.produits)}
                    </span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Graphique comparatif */}
          <Card>
            <h3 className="chart-title" style={{ marginBottom: 16 }}>
              Comparaison visuelle — {annee}
            </h3>
            <div className="pred-chart-wrap" style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={CHART_DATA} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tickFormatter={v => `${v}k`} tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                  <Legend wrapperStyle={{ fontSize: 12, color: "var(--text-secondary)" }} />
                  <Bar dataKey="Pessimiste" fill="var(--danger)"  radius={[4,4,0,0]} />
                  <Bar dataKey="Réaliste"   fill="var(--info)"    radius={[4,4,0,0]} />
                  <Bar dataKey="Optimiste"  fill="var(--success)" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Tableau comparatif */}
          <Card>
            <h3 className="chart-title" style={{ marginBottom: 14 }}>
              Tableau comparatif détaillé
            </h3>
            <div className="table-wrap">
              <table className="sap-table">
                <thead>
                  <tr>
                    <th>Scénario</th>
                    <th>Total Dépenses</th>
                    <th>Total Produits</th>
                    <th>Résultat Net</th>
                    <th>Variation vs Réaliste</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(MOCK_SCENARIOS).map(([key, sc]) => {
                    const diff = sc.net - MOCK_SCENARIOS.realiste.net;
                    const isRealiste = key === "realiste";
                    return (
                      <tr key={key}>
                        <td>
                          <span style={{ marginRight: 6 }}>{sc.icon}</span>
                          <span style={{ fontWeight: 600, color: sc.color }}>{sc.label}</span>
                        </td>
                        <td className="mono" style={{ color: "var(--danger)" }}>
                          {fmt(sc.depenses)}
                        </td>
                        <td className="mono" style={{ color: "var(--success)" }}>
                          {fmt(sc.produits)}
                        </td>
                        <td className="mono" style={{ color: sc.color, fontWeight: 700 }}>
                          +{fmt(sc.net)}
                        </td>
                        <td>
                          {isRealiste ? (
                            <span className="table-badge badge-neutral">Référence</span>
                          ) : (
                            <span className={`table-badge ${diff > 0 ? "badge-success" : "badge-danger"}`}>
                              {diff > 0 ? "+" : ""}{fmt(diff)}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      {/* État vide */}
      {!shown && (
        <Card className="pred-empty">
          <div className="pred-empty-inner">
            <div className="pred-empty-icon">📋</div>
            <p className="pred-empty-title">Aucun scénario calculé</p>
            <p className="pred-empty-sub">
              Sélectionnez une année et une variation,<br />
              puis cliquez sur "Calculer les scénarios".
            </p>
          </div>
        </Card>
      )}

    </section>
  );
}
