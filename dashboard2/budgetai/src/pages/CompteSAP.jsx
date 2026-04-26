// src/pages/Accounts.jsx
import { useState } from "react";
import { Search, Filter, TrendingUp, TrendingDown, Eye, Calculator } from "lucide-react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import "./page.css";

const ACCOUNTS_MOCK = [
  { code: "COMPTE_7111", name: "Chiffre d'affaires", type: "produit", avgMonthly: 875000, lastTx: "2025-12-15", status: "actif", trend: "+8.3%" },
  { code: "COMPTE_6011", name: "Achats matières premières", type: "dépense", avgMonthly: 92000, lastTx: "2025-12-14", status: "actif", trend: "+4.2%" },
  { code: "COMPTE_6141", name: "Loyers", type: "dépense", avgMonthly: 45000, lastTx: "2025-12-01", status: "actif", trend: "0%" },
  { code: "COMPTE_6161", name: "Assurances", type: "dépense", avgMonthly: 12500, lastTx: "2025-11-28", status: "actif", trend: "+2.1%" },
  { code: "COMPTE_6165", name: "Electricité et eau", type: "dépense", avgMonthly: 28000, lastTx: "2025-12-10", status: "alerte", trend: "+15.4%" },
  { code: "COMPTE_6171", name: "Transport et livraisons", type: "dépense", avgMonthly: 18000, lastTx: "2025-12-12", status: "actif", trend: "-3.2%" },
  { code: "COMPTE_6174", name: "Téléphone et internet", type: "dépense", avgMonthly: 8500, lastTx: "2025-12-05", status: "actif", trend: "+1.5%" },
  { code: "COMPTE_6176", name: "Honoraires consultants", type: "dépense", avgMonthly: 35000, lastTx: "2025-11-20", status: "actif", trend: "+12.0%" },
  { code: "COMPTE_6178", name: "Fournitures de bureau", type: "dépense", avgMonthly: 6200, lastTx: "2025-12-08", status: "inactif", trend: "-8.5%" },
  { code: "COMPTE_6185", name: "Maintenance équipements", type: "dépense", avgMonthly: 22000, lastTx: "2025-10-15", status: "actif", trend: "+5.7%" },
  { code: "COMPTE_6190", name: "Formation du personnel", type: "dépense", avgMonthly: 14000, lastTx: "2025-09-30", status: "actif", trend: "+22.0%" },
  { code: "COMPTE_6200", name: "Salaires", type: "dépense", avgMonthly: 320000, lastTx: "2025-12-01", status: "actif", trend: "+3.5%" },
  { code: "COMPTE_6210", name: "Charges sociales CNSS", type: "dépense", avgMonthly: 89000, lastTx: "2025-12-01", status: "actif", trend: "+3.5%" },
  { code: "COMPTE_7120", name: "Subventions reçues", type: "produit", avgMonthly: 25000, lastTx: "2025-11-15", status: "actif", trend: "0%" },
  { code: "COMPTE_7300", name: "Intérêts bancaires reçus", type: "produit", avgMonthly: 8000, lastTx: "2025-12-20", status: "actif", trend: "-12.3%" },
];

const KPIS = [
  { title: "Total Comptes", value: "15", subLabel: "Tous types", tone: "neutral" },
  { title: "Comptes Actifs", value: "14", subLabel: "93% actifs", trend: "up", trendValue: "+1", tone: "success" },
  { title: "Comptes Dépenses", value: "12", subLabel: "80% du total", tone: "warning" },
  { title: "Comptes Produits", value: "3", subLabel: "20% du total", tone: "info" },
];

function Accounts() {
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("tous");
  const [selectedAccount, setSelectedAccount] = useState(null);

  const filteredAccounts = ACCOUNTS_MOCK.filter((acc) => {
    const matchesSearch = acc.name.toLowerCase().includes(search.toLowerCase()) || 
                          acc.code.toLowerCase().includes(search.toLowerCase());
    const matchesType = filterType === "tous" || acc.type === filterType;
    return matchesSearch && matchesType;
  });

  const getStatusBadge = (status) => {
    const classes = {
      actif: "ui-badge-success",
      alerte: "ui-badge-danger", 
      inactif: "ui-badge-warning",
    };
    return <span className={`ui-badge ${classes[status]}`}>{status.toUpperCase()}</span>;
  };

  const getTrendIcon = (trend) => {
    const isPositive = trend.startsWith("+");
    return isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />;
  };

  return (
    <section className="page-grid">
      {/* KPIs */}
      <div className="kpi-grid">
        {KPIS.map((kpi) => (
          <Card key={kpi.title} className="kpi-card">
            <p className="kpi-title">{kpi.title}</p>
            <p className="kpi-value">{kpi.value}</p>
            <div className="kpi-meta-row">
              <span className={`kpi-trend kpi-trend-${kpi.tone}`}>
                {kpi.trend && getTrendIcon(kpi.trendValue)}
                {kpi.trendValue || kpi.subLabel}
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* Filtres */}
      <Card>
        <div className="accounts-filters">
          <div className="accounts-search">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              placeholder="Rechercher un compte (code ou nom)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="accounts-search-input"
            />
          </div>
          <div className="accounts-filter-group">
            <Filter size={16} />
            <select 
              value={filterType} 
              onChange={(e) => setFilterType(e.target.value)}
              className="chart-select"
            >
              <option value="tous">Tous les types</option>
              <option value="dépense">Dépenses</option>
              <option value="produit">Produits</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Tableau */}
      <Card className="accounts-table-card">
        <div className="accounts-table-header">
          <h3 className="chart-title">Liste des comptes SAP</h3>
          <span className="accounts-count">{filteredAccounts.length} compte(s)</span>
        </div>
        
        <div className="accounts-table-wrap">
          <table className="sap-table accounts-table">
            <thead>
              <tr>
                <th>Code compte</th>
                <th>Nom du compte</th>
                <th>Type</th>
                <th>Budget moyen/mois</th>
                <th>Dernière transaction</th>
                <th>Tendance</th>
                <th>Statut</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredAccounts.map((acc) => (
                <tr key={acc.code} className={acc.status === "alerte" ? "row-alert" : ""}>
                  <td>
                    <span className="account-code">{acc.code}</span>
                  </td>
                  <td className="account-name">{acc.name}</td>
                  <td>
                    <span className={`type-badge type-${acc.type}`}>
                      {acc.type}
                    </span>
                  </td>
                  <td className="mono-cell">{acc.avgMonthly.toLocaleString()} DH</td>
                  <td>{acc.lastTx}</td>
                  <td>
                    <span className={`trend-value ${acc.trend.startsWith("+") ? "up" : "down"}`}>
                      {getTrendIcon(acc.trend)}
                      {acc.trend}
                    </span>
                  </td>
                  <td>{getStatusBadge(acc.status)}</td>
                  <td>
                    <div className="accounts-actions">
                      <button 
                        className="action-btn view"
                        onClick={() => setSelectedAccount(acc)}
                        title="Voir détails"
                      >
                        <Eye size={16} />
                      </button>
                      <button 
                        className="action-btn predict"
                        title="Prédire budget"
                      >
                        <Calculator size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Drawer détail (simplifié pour l'instant) */}
      {selectedAccount && (
        <div className="account-drawer-overlay" onClick={() => setSelectedAccount(null)}>
          <div className="account-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span className="account-code-lg">{selectedAccount.code}</span>
                <h2 className="drawer-title">{selectedAccount.name}</h2>
              </div>
              <button className="drawer-close" onClick={() => setSelectedAccount(null)}>×</button>
            </div>
            <div className="drawer-body">
              <div className="drawer-stats">
                <div className="drawer-stat">
                  <span className="drawer-stat-label">Type</span>
                  <span className={`type-badge type-${selectedAccount.type}`}>
                    {selectedAccount.type}
                  </span>
                </div>
                <div className="drawer-stat">
                  <span className="drawer-stat-label">Budget moyen mensuel</span>
                  <span className="drawer-stat-value">
                    {selectedAccount.avgMonthly.toLocaleString()} DH
                  </span>
                </div>
                <div className="drawer-stat">
                  <span className="drawer-stat-label">Tendance</span>
                  <span className={`trend-value ${selectedAccount.trend.startsWith("+") ? "up" : "down"}`}>
                    {selectedAccount.trend}
                  </span>
                </div>
              </div>
              <div className="drawer-chart-placeholder">
                <p>📊 Graphique historique 5 ans (à brancher sur API)</p>
              </div>
              <Button className="drawer-predict-btn">
                <Calculator size={18} />
                Lancer une prédiction pour ce compte
              </Button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default Accounts;