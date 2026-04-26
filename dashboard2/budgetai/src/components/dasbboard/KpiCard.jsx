import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import Card from "../ui/Card";

function KpiCard({ title, value, subLabel, trend, trendValue, tone = "neutral" }) {
  const isUp = trend === "up";
  const trendClass = tone === "danger" ? "kpi-trend-danger" : "kpi-trend-success";

  return (
    <Card className="kpi-card">
      <p className="kpi-title">{title}</p>
      <p className="kpi-value">{value}</p>
      <div className="kpi-meta-row">
        <span className={`kpi-trend ${trendClass}`}>
          {isUp ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}
          <span>{trendValue}</span>
        </span>
        <span className="kpi-sub">{subLabel}</span>
      </div>
    </Card>
  );

}
export default KpiCard;