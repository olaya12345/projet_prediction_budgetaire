import "./ui.css";

function Card({ children, className = "", ...props }) {
  return (
    <article className={`ui-card ${className}`.trim()} {...props}>
      {children}
    </article>
  );
}

export default Card;
