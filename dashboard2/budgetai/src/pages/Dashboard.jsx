import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, AlertTriangle, ArrowRight, Info } from "lucide-react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import KpiCard from "../components/dashboard/KpiCard";
import BudgetLineChart from "../components/charts/BudgetLineChart";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import {
  consolidate,
  getAccounts,
  getAlerts,
  predictAccount,
  predictBest,
} from "../api/endPoints";
import "./page.css";

const kpiTemplates = [
  {
    key: "budget",
    title: "Budget Total Prevu",
    subLabel: "Projection annuelle",
    trend: "up",
    trendValue: "+4.2%",
  },
  {
    key: "bestMape",
    title: "Meilleur Modele MAPE",
    subLabel: "Random Forest",
    trend: "down",
    trendValue: "-0.4%",
  },
  {
    key: "alertsCrit",
    title: "Alertes Critiques",
    subLabel: "Action requise",
    trend: "up",
    trendValue: "+1",
    defaultTone: "danger",
  },
  {
    key: "accountsAnalysed",
    title: "Comptes Analyses",
    subLabel: "Tous actifs",
    trend: "up",
    trendValue: "+3",
  },
];

function formatDh(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return "—";
  const rounded = Math.round(num);
  return `${new Intl.NumberFormat("fr-FR").format(rounded)} DH`;
}

function formatPct(value, digits = 2) {
  const num = Number(value);
  if (Number.isNaN(num)) return "—";
  return `${num.toFixed(digits)}%`;
}

const budgetSeries = [
  { month: "Jan", historical: 740, predicted: 780, confidence: 30 },
  { month: "Fev", historical: 720, predicted: 765, confidence: 32 },
  { month: "Mar", historical: 760, predicted: 790, confidence: 35 },
  { month: "Avr", historical: 810, predicted: 835, confidence: 36 },
  { month: "Mai", historical: 790, predicted: 820, confidence: 34 },
  { month: "Juin", historical: 850, predicted: 875, confidence: 38 },
  { month: "Juil", historical: 870, predicted: 905, confidence: 40 },
  { month: "Aou", historical: 845, predicted: 890, confidence: 37 },
  { month: "Sep", historical: 880, predicted: 920, confidence: 41 },
  { month: "Oct", historical: 910, predicted: 950, confidence: 42 },
  { month: "Nov", historical: 940, predicted: 980, confidence: 44 },
  { month: "Dec", historical: 970, predicted: 1010, confidence: 45 },
];

const modelRankingFallback = [
  { model: "Random Forest", metric: "MAPE", score: "2.86%", tone: "success" },
  { model: "XGBoost", metric: "MAPE", score: "3.04%", tone: "info" },
  { model: "LSTM", metric: "MAPE", score: "3.25%", tone: "warning" },
  { model: "ARIMA", metric: "MAPE", score: "3.48%", tone: "danger" },
];

const MONTH_LABELS = [
  "Jan",
  "Fev",
  "Mar",
  "Avr",
  "Mai",
  "Juin",
  "Juil",
  "Aou",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

const ALERT_CONFIG = {
  CRITIQUE: {
    icon: <AlertTriangle size={16} />,
    cls: "alert-icon-critique",
    badgeCls: "badge-danger",
    label: "Critique",
  },
  HAUTE: {
    icon: <AlertCircle size={16} />,
    cls: "alert-icon-haute",
    badgeCls: "badge-warning",
    label: "Haute",
  },
  MOYENNE: {
    icon: <AlertCircle size={16} />,
    cls: "alert-icon-info",
    badgeCls: "badge-info",
    label: "Moyenne",
  },
  FAIBLE: {
    icon: <Info size={16} />,
    cls: "alert-icon-info",
    badgeCls: "badge-info",
    label: "Faible",
  },
  INFO: {
    icon: <Info size={16} />,
    cls: "alert-icon-info",
    badgeCls: "badge-info",
    label: "Info",
  },
};

function Dashboard() {
  const navigate = useNavigate();
  const [selectedAccount, setSelectedAccount] = useState("COMPTE_7111");
  const [selectedYear, setSelectedYear] = useState(2028);
  const [bestResult, setBestResult] = useState(null);
  const [accountSearch, setAccountSearch] = useState("");
  const [accountsPage, setAccountsPage] = useState(1);

  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: () => getAccounts(),
    retry: false,
  });

  const accountOptions = useMemo(() => {
    const raw = accountsQuery.data?.accounts ?? [];
    return raw
      .map((row) => ({
        code: row.num_compte,
        label: row.nom_compte || row.num_compte,
      }))
      .filter((a) => Boolean(a.code));
  }, [accountsQuery.data]);

  useEffect(() => {
    if (!accountOptions.length) return;
    if (!accountOptions.some((a) => a.code === selectedAccount)) {
      setSelectedAccount(accountOptions[0].code);
    }
  }, [accountOptions, selectedAccount]);

  useEffect(() => {
    setBestResult(null);
  }, [selectedAccount, selectedYear]);

  useEffect(() => {
    setAccountsPage(1);
  }, [accountSearch]);

  const consolidateQuery = useQuery({
    queryKey: ["consolidate", selectedYear],
    queryFn: () => consolidate({ year_target: selectedYear, with_ia_comments: false }),
    retry: false,
  });

  const alertsQuery = useQuery({
    queryKey: ["alerts", selectedYear],
    queryFn: () => getAlerts(selectedYear),
    retry: false,
  });

  const bestMutation = useMutation({
    mutationFn: () =>
      predictBest({ account_code: selectedAccount, year_target: selectedYear }),
    onSuccess: (data) => setBestResult(data),
    onError: (error) => {
      const detail = error?.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : "ML Engine: echec (donnees insuffisantes pour ce compte). Choisis un compte du dataset ou enrichis l historique.";
      toast.error(msg);
    },
  });

  const chartQuery = useQuery({
    queryKey: ["predictAccount", selectedAccount, selectedYear],
    queryFn: () =>
      predictAccount({
        account_code: selectedAccount,
        year_target: selectedYear,
        with_ia_comments: false,
      }),
    enabled: Boolean(selectedAccount),
    retry: false,
  });

  const chartData = useMemo(() => {
    const monthly = chartQuery.data?.predictions?.monthly;
    if (!Array.isArray(monthly) || monthly.length === 0) {
      return budgetSeries;
    }

    return monthly.map((row, index) => {
      const predicted = Number(row?.budget_total ?? 0);
      const trendPct = Number(row?.tendance_pct ?? 0);
      const historical =
        1 + trendPct / 100 === 0 ? predicted : predicted / (1 + trendPct / 100);
      const confidence = predicted * 0.9;

      return {
        month: MONTH_LABELS[index] || `M${index + 1}`,
        historical: Number.isFinite(historical) ? Math.round(historical) : predicted,
        predicted: Math.round(predicted),
        confidence: Math.round(confidence),
      };
    });
  }, [chartQuery.data]);

  const apiOffline = consolidateQuery.isError || alertsQuery.isError;

  const accountBudgetMap = useMemo(() => {
    const comptes = consolidateQuery.data?.comptes;
    if (!comptes) return {};

    return Object.fromEntries(
      Object.entries(comptes).map(([code, payload]) => {
        const annual = payload?.budget_annuel || {};
        const annualTotal = Number(annual.total ?? annual.credit ?? annual.debit ?? 0);
        return [code, { total: annualTotal }];
      })
    );
  }, [consolidateQuery.data]);

  const tableRows = useMemo(() => {
    const q = accountSearch.trim().toLowerCase();
    return accountOptions
      .filter((a) => !q || a.code.toLowerCase().includes(q) || a.label.toLowerCase().includes(q))
      .map((a) => {
        const total = accountBudgetMap[a.code]?.total;
        return {
          code: a.code,
          label: a.label,
          amount: Number.isFinite(total) && total > 0 ? formatDh(total) : "—",
        };
      });
  }, [accountBudgetMap, accountOptions, accountSearch]);

  const accountsPerPage = 8;
  const totalPages = Math.max(1, Math.ceil(tableRows.length / accountsPerPage));
  const safePage = Math.min(accountsPage, totalPages);
  const pagedRows = useMemo(() => {
    const start = (safePage - 1) * accountsPerPage;
    return tableRows.slice(start, start + accountsPerPage);
  }, [safePage, tableRows]);

  const rankingRows = useMemo(() => {
    const ranking = bestResult?.classement;
    if (!Array.isArray(ranking) || ranking.length === 0) {
      return modelRankingFallback;
    }

    return ranking
      .filter((item) => item?.mape != null)
      .map((item) => {
        const mape = Number(item.mape);
        let tone = "danger";
        if (mape < 3) tone = "success";
        else if (mape < 4) tone = "info";
        else if (mape < 5) tone = "warning";

        return {
          model: item.modele || "Modele",
          metric: "MAPE",
          score: formatPct(mape, 2),
          tone,
        };
      });
  }, [bestResult]);

  const alertRows = useMemo(() => {
    const raw = alertsQuery.data?.alertes;
    if (!Array.isArray(raw) || raw.length === 0) return [];

    return raw.slice(0, 5).map((item, index) => {
      const sev = item?.severite || "INFO";
      const type = item?.type || "Alerte";
      const message = item?.message || "Aucune description.";
      const mois = item?.mois || `${selectedYear}`;
      const compteMatch = message.match(/COMPTE_\d+/i);

      return {
        id: `${type}-${index}`,
        severite: sev,
        titre: type.replaceAll("_", " "),
        description: message,
        compte: compteMatch ? compteMatch[0].toUpperCase() : "N/A",
        mois,
      };
    });
  }, [alertsQuery.data, selectedYear]);

  const zoneAKpis = useMemo(() => {
    const budgetNet = consolidateQuery.data?.budget_global?.net_annuel;
    const accountsAnalysed = consolidateQuery.data?.stats?.comptes_traites;
    const alertsCrit = alertsQuery.data?.par_severite?.critique;

    const bestMape = bestResult?.meilleur_mape;
    const bestModelName = bestResult?.meilleur_modele;

    const budgetTone =
      budgetNet === undefined ? "success" : budgetNet >= 0 ? "success" : "danger";

    return [
      {
        ...kpiTemplates[0],
        title: `${kpiTemplates[0].title} ${selectedYear}`,
        value: consolidateQuery.isError
          ? "—"
          : consolidateQuery.isLoading || budgetNet === undefined
            ? "..."
            : formatDh(budgetNet),
        tone: budgetTone,
      },
      {
        ...kpiTemplates[1],
        value: bestResult ? formatPct(bestMape, 2) : "—",
        subLabel: bestModelName || 'Clique sur "Lancer ML Engine"',
        tone: "success",
      },
      {
        ...kpiTemplates[2],
        value: alertsQuery.isError
          ? "—"
          : alertsQuery.isLoading || alertsCrit === undefined
            ? "..."
            : String(alertsCrit),
        tone: alertsCrit > 0 ? "danger" : "success",
      },
      {
        ...kpiTemplates[3],
        value: consolidateQuery.isError
          ? "—"
          : consolidateQuery.isLoading || accountsAnalysed === undefined
            ? "..."
            : String(accountsAnalysed),
        tone: "success",
      },
    ];
  }, [
    alertsQuery.data,
    alertsQuery.isError,
    alertsQuery.isLoading,
    bestResult,
    consolidateQuery.data,
    consolidateQuery.isError,
    consolidateQuery.isLoading,
    selectedYear,
  ]);

  return (
    <section className="page-grid">
      {apiOffline && (
        <div className="dashboard-api-banner" role="alert">
          <strong>API indisponible.</strong> Le proxy Vite ne peut pas joindre{" "}
          <code>http://localhost:8000</code>. Lance ton backend FastAPI (ex.{" "}
          <code>python main.py</code> dans <code>ia_server/api</code>), puis recharge la page.
        </div>
      )}

      <div className="kpi-grid">
        {zoneAKpis.map((kpi) => (
          <KpiCard
            key={kpi.key}
            title={kpi.title}
            value={kpi.value}
            subLabel={kpi.subLabel}
            trend={kpi.trend}
            trendValue={kpi.trendValue}
            tone={kpi.tone}
          />
        ))}
      </div>

      <Card className="chart-card">
        <div className="chart-head">
          <div>
            <h3 className="chart-title">
              Evolution budgetaire mensuelle - {selectedYear}
            </h3>
            <p className="chart-sub">
              {chartQuery.isLoading
                ? "Chargement prediction compte..."
                : chartQuery.isError
                  ? "Prediction API indisponible: fallback mock."
                  : `Prediction API pour ${selectedAccount}`}
            </p>
          </div>

          <div className="chart-controls">
            <select
              className="chart-select"
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              disabled={accountsQuery.isLoading || accountOptions.length === 0}
            >
              {accountOptions.length === 0 ? (
                <option value={selectedAccount}>
                  {accountsQuery.isError ? "Comptes indisponibles" : "Chargement..."}
                </option>
              ) : (
                accountOptions.map((a) => (
                  <option key={a.code} value={a.code}>
                    {a.label !== a.code ? `${a.code} — ${a.label}` : a.code}
                  </option>
                ))
              )}
            </select>
            <select
              className="chart-select"
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
            >
              <option value="2028">2028</option>
              <option value="2029">2029</option>
              <option value="2030">2030</option>
            </select>
            <Button
              disabled={bestMutation.isPending}
              onClick={() => bestMutation.mutate()}
              type="button"
            >
              {bestMutation.isPending ? "Calcul ML Engine..." : "Lancer ML Engine"}
            </Button>
          </div>
        </div>

        <BudgetLineChart data={chartData} />
      </Card>

      <div className="zone-c-grid">
        <Card>
          <div className="zone-c-head">
            <div>
              <h3 className="chart-title">Comptes SAP analyses</h3>
              <p className="chart-sub">
                {accountsQuery.isLoading
                  ? "Chargement comptes..."
                  : `${tableRows.length} compte(s) visibles`}
              </p>
            </div>
            <input
              className="table-search"
              type="search"
              placeholder="Rechercher un compte..."
              aria-label="Rechercher un compte SAP"
              value={accountSearch}
              onChange={(e) => setAccountSearch(e.target.value)}
            />
          </div>

          <div className="table-wrap">
            <table className="sap-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Libelle</th>
                  <th>Budget prevu</th>
                  <th>MAPE</th>
                </tr>
              </thead>
              <tbody>
                {pagedRows.length === 0 ? (
                  <tr>
                    <td colSpan={4}>Aucun compte trouve.</td>
                  </tr>
                ) : (
                  pagedRows.map((account) => (
                    <tr key={account.code}>
                      <td>{account.code}</td>
                      <td>{account.label}</td>
                      <td>{account.amount}</td>
                      <td>{bestResult ? formatPct(bestResult?.meilleur_mape, 2) : "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="table-pagination">
            <span>
              {tableRows.length === 0
                ? "0 compte"
                : `${(safePage - 1) * accountsPerPage + 1}-${Math.min(
                    safePage * accountsPerPage,
                    tableRows.length
                  )} sur ${tableRows.length} comptes`}
            </span>
            <div className="table-pagination-actions">
              <button
                className="pager-btn"
                type="button"
                onClick={() => setAccountsPage((p) => Math.max(1, p - 1))}
                disabled={safePage <= 1}
              >
                Precedent
              </button>
              <button
                className="pager-btn"
                type="button"
                onClick={() => setAccountsPage((p) => Math.min(totalPages, p + 1))}
                disabled={safePage >= totalPages}
              >
                Suivant
              </button>
            </div>
          </div>
        </Card>

        <Card>
          <div className="zone-c-head">
            <div>
              <h3 className="chart-title">Classement modeles</h3>
              <p className="chart-sub">
                {bestResult ? `ML Engine pour ${selectedAccount}` : "Lance ML Engine pour le classement reel"}
              </p>
            </div>
          </div>

          <div className="ranking-list">
            {rankingRows.map((item, index) => (
              <div className="ranking-row" key={item.model}>
                <div className="ranking-left">
                  <span className="ranking-index">#{index + 1}</span>
                  <div>
                    <p className="ranking-model">{item.model}</p>
                    <p className="ranking-metric">{item.metric}</p>
                  </div>
                </div>
                <span className={`ranking-score ranking-score-${item.tone}`}>{item.score}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <div className="zone-d-head">
          <div>
            <h3 className="chart-title">Alertes budgetaires - {selectedYear}</h3>
            <p className="chart-sub">
              {alertsQuery.isLoading
                ? "Chargement alertes..."
                : `${alertRows.length} alerte(s) recente(s)`}
            </p>
          </div>
          <button className="zone-d-link" onClick={() => navigate("/alerts")} type="button">
            Voir toutes les alertes <ArrowRight size={14} />
          </button>
        </div>

        <div className="alerts-list">
          {alertsQuery.isError ? (
            <div className="alert-row">
              <div className="alert-row-body">
                <p className="alert-row-desc">
                  Impossible de charger les alertes depuis l API pour le moment.
                </p>
              </div>
            </div>
          ) : alertRows.length === 0 ? (
            <div className="alert-row">
              <div className="alert-row-body">
                <p className="alert-row-desc">Aucune alerte detectee.</p>
              </div>
            </div>
          ) : (
            alertRows.map((alert) => {
              const cfg = ALERT_CONFIG[alert.severite] || ALERT_CONFIG.INFO;
              return (
                <div key={alert.id} className="alert-row">
                  <div className={`alert-row-icon ${cfg.cls}`}>{cfg.icon}</div>
                  <div className="alert-row-body">
                    <div className="alert-row-top">
                      <span className="alert-row-titre">{alert.titre}</span>
                      <span className={`table-badge ${cfg.badgeCls}`}>{cfg.label}</span>
                    </div>
                    <p className="alert-row-desc">{alert.description}</p>
                    <div className="alert-row-meta">
                      <span className="account-code">{alert.compte}</span>
                      <span className="alert-row-mois">{alert.mois}</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </Card>
    </section>
  );
}

export default Dashboard;
