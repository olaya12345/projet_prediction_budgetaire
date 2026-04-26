import "./ui.css";

const toneClass = {
  success: "ui-badge-success",
  danger: "ui-badge-danger",
  warning: "ui-badge-warning",
  info: "ui-badge-info",
  gold: "ui-badge-gold",
};

function Badge({ children, tone = "info", className = "", ...props }) {
  const safeTone = toneClass[tone] || toneClass.info;
  return (
    <span className={`ui-badge ${safeTone} ${className}`.trim()} {...props}>
      {children}
    </span>
  );
}

export default Badge;