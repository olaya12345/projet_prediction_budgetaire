import { useQuery } from "@tanstack/react-query";
import Card from "../components/ui/Card";
import Badge from "../components/ui/Badge";
import useAuthStore from "../store/authStore";
import { healthCheck } from "../api/endPoints";
import "./page.css";
function Settings(){
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);
  const {
    data: apiData,
    isLoading: isHealthLoading,
    isError: isHealthError,
    error,
  } = useQuery({
    queryKey: ["apiStatus"],
    queryFn: healthCheck,
    retry: false,
  });

  const apiStatusText = isHealthLoading
    ? "En cours..."
    : isHealthError
      ? "Hors ligne"
      : "OK";

  const apiBadgeTone = isHealthError ? "danger" : "success";
  
  return(
    <section className="page-grid">
      <div className="settings-grid">
        <Card>
          <h3 className="settings-title">Profil</h3>
          <div className="settings-row">
            <div className="settings-label">Nom</div>
            <div className="settings-value">{user?.name || "—"}</div>
          </div>
          <div className="settings-row">
            <div className="settings-label">Rôle</div>
            <div className="settings-value">{user?.role || "—"}</div>
          </div>
          <div className="settings-row">
            <div className="settings-label">Session</div>
            <div className="settings-value">{token ? "Active" : "Inexistante"}</div>
          </div>
        </Card>

        <Card>
          <h3 className="settings-title">Statut API</h3>
          <div className="settings-row">
            <div className="settings-label">Etat</div>
            <div className="settings-value">
              <Badge tone={apiBadgeTone}>{apiStatusText}</Badge>
            </div>
          </div>

          {isHealthLoading ? (
            <p className="settings-help">Vérification du backend...</p>
          ) : isHealthError ? (
            <p className="settings-help">
              Impossible d’appeler <code>/health</code>.
              {error?.message ? ` (${error.message})` : ""}
            </p>
          ) : (
            <div className="settings-help">
              <div className="settings-help-title">Réponse</div>
              <pre className="settings-pre">
                {apiData ? JSON.stringify(apiData, null, 2) : "—"}
              </pre>
            </div>
          )}
        </Card>

        <Card className="settings-about-card">
          <h3 className="settings-title">À propos</h3>
          <p className="settings-paragraph">
            BudgetAI est une interface React qui consomme le backend FastAPI.
            Cette page sert à afficher le profil courant et vérifier rapidement
            la disponibilité de l’API.
          </p>
          <div className="settings-about-links">
            <div className="settings-about-item">
              Endpoint santé : <code>/health</code>
            </div>
            <div className="settings-about-item">
              Auth : <code>/auth/login</code>
            </div>
          </div>
          <p className="settings-paragraph muted">
            Mode dev: données/sections Dashboard mises en place par zones (UI-first).
          </p>
        </Card>
      </div>
    </section>
  );

}
export default Settings;
