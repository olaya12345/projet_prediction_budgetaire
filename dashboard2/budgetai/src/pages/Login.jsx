import { useMutation } from "@tanstack/react-query";
import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { login } from "../api/endPoints";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import useAuthStore from "../store/authStore";
import "./login.css";

function Login() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const loginMutation = useMutation({
    mutationFn: () => login({ email, password }),
    onSuccess: (data) => {
      const token =
        data?.access_token ||
        data?.token ||
        data?.jwt ||
        data?.data?.access_token ||
        data?.data?.token;

      if (!token) {
        console.error("Login response without token:", data);
        toast.error("Token manquant dans la reponse API (voir console).");
        return;
      }

      setAuth({
        token,
        user: data?.user || data?.data?.user || { name: "Utilisateur", role: "Analyste" },
      });
      toast.success("Connexion reussie.");
      navigate("/dashboard");
    },
    onError: (error) => {
      const message = !error?.response
        ? "API indisponible. Verifie que FastAPI tourne sur http://localhost:8000."
        : error?.response?.data?.detail || "Echec de connexion. Verifie tes identifiants.";
      toast.error(message);
    },
  });

  const handleSubmit = (event) => {
    event.preventDefault();
    loginMutation.mutate();
  };

  return (
    <main className="login-page">
      <Card className="login-card">
        <p className="eyebrow">BudgetAI</p>
        <h1>Bienvenue</h1>
        <p className="subtitle">Connectez-vous a votre espace de prediction.</p>

        <div className="badge-row">
          <Badge tone="info">100% Local</Badge>
          <Badge tone="success">Donnees SAP securisees</Badge>
          <Badge tone="gold">IA integree</Badge>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <Input
            id="email"
            type="email"
            label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="finance@budgetai.ma"
            required
          />

          <div className="password-wrap">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              label="Mot de passe"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="********"
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword((v) => !v)}
              aria-label="Afficher ou masquer le mot de passe"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          <Button type="submit" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "Analyse en cours..." : "Se connecter"}
          </Button>
        </form>
      </Card>
    </main>
  );
}

export default Login;