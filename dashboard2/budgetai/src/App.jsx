import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import PlaceholderPage from "./pages/Placeholders";
import Predictions from "./pages/Predictions";
import Alerts from "./pages/Alerts";
import Scenarios from "./pages/Scenarios";
import useAuthStore from "./store/authStore";
import Settings from "./pages/Settings";
import CompteSAP from "./pages/CompteSAP";
import "./App.css";
import Reports from "./pages/Reports";
function ProtectedRoute({ children }) {
  const token = useAuthStore((state) => state.token);
  return token ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/predictions" element={<Predictions />} />
        <Route path="/alerts" element={<Alerts />} />
         <Route path="/scenarios" element={<Scenarios />} />
        <Route path="/accounts" element={<CompteSAP />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<PlaceholderPage title="Parametres" />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;