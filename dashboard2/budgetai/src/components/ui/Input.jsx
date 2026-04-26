import "./ui.css";

function Input({ label, id, className = "", ...props }) {
  return (
    <div className={`ui-input-wrap ${className}`.trim()}>
      {label ? <label className="ui-input-label" htmlFor={id}>{label}</label> : null}
      <input id={id} className="ui-input" {...props} />
    </div>
  );
}

export default Input;