import Card from "../components/ui/Card";
import "./page.css";

function PlaceholderPage({ title }) {
  return (
    <section className="page-grid">
      <Card>
        <h3>{title}</h3>
        <p>Page prete. On l implementera dans les prochaines etapes.</p>
      </Card>
    </section>
  );
}

export default PlaceholderPage;