function KpiCard({ title, value, subLabel, trend, trendValue, tone = "success" }) {
  const trendClass = trend === "up" ? "kpi-trend-success" : "kpi-trend-danger";

  return (
    <div className={`kpi-card kpi-card-${tone}`}>
      <div className="kpi-header">
        <span className="kpi-title">{title}</span>
      </div>
      <div className="kpi-meta-row">
        <span className={`kpi-value kpi-value-${tone}`}>{value}</span>
        {trendValue && (
          <span className={`kpi-trend ${trendClass}`}>
            {trend === "up" ? "↑" : "↓"} {trendValue}
          </span>
        )}
      </div>
      {subLabel && <span className="kpi-sub">{subLabel}</span>}
    </div>
  );
}

export default KpiCard;
