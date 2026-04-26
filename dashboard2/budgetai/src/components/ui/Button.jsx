import "./ui.css";

const variantClass = {
  primary: "ui-button-primary",
  secondary: "ui-button-secondary",
  ghost: "ui-button-ghost",
};

function Button({ children, variant = "primary", className = "", ...props }) {
  const safeVariant = variantClass[variant] || variantClass.primary;
  return (
    <button className={`ui-button ${safeVariant} ${className}`.trim()} {...props}>
      {children}
    </button>
  );
}

export default Button;