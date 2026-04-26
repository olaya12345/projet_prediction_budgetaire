import {
  Area,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function BudgetLineChart({data}){
    return (
      <div className="budget-chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
             <LineChart data={data}>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false}/>
                <XAxis 
                dataKey="month"
                stroke="var(--text-muted)"
                tick={{ fill: "var(--text-muted)", fontSize: 11, fontFamily: "var(--font-mono)" }}
                axisLine={false}
                tickLine={false}
                />
                <YAxis
                   stroke="var(--text-muted)"
                   tick={{ fill: "var(--text-muted)", fontSize: 11, fontFamily: "var(--font-mono)" }}
                   axisLine={false}
                   tickLine={false}
                   width={60}
                />
                <Tooltip
                  contentStyle={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-strong)",
                  borderRadius: 8,
                  color: "var(--text-primary)",
                }}
                />
                <Legend/>
                <Area
                  type="monotone"
                  dataKey="confidence"
                  stroke="none"
                  fill="rgba(226,168,75,0.18)"
                  name="Intervalle confiance"
                />
                <Line
                  type="monotone"
                  dataKey="historical"
                  stroke="var(--teal)"
                  strokeWidth={2}
                  dot={false}
                  name="Reel historique"
                  animationDuration={800}
                />
                <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="var(--gold)"
                    strokeWidth={2}
                    strokeDasharray="6 6"
                    dot={false}
                    name="Prediction 2028"
                    animationDuration={800}
                />

             </LineChart>
        </ResponsiveContainer>
      </div>
    );
}
export default BudgetLineChart;
