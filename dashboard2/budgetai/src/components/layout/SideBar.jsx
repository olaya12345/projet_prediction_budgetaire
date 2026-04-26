import { BarChart3, Bell, Brain, Database, FileText, Layers, LogOut, Settings } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import useAuthStore from "../../store/authStore";

const navItems = [
  { to: "/dashboard", label: "Tableau de bord", icon: BarChart3 },
  { to: "/predictions", label: "Predictions", icon: Brain },
  { to: "/accounts", label: "Comptes SAP", icon: Database },
  { to: "/alerts", label: "Alertes", icon: Bell },
  { to: "/scenarios", label: "Scenarios", icon: Layers },
  { to: "/reports", label: "Rapports", icon: FileText },
];
function SideBar(){
    const navigate = useNavigate();
    const { user, logout } = useAuthStore();
    const onLogout = () => {
        logout();
        navigate("/login");
    }

    return(
     <aside className="sidebar">
         <div>
            <p className="logo-mini">BUDGETAI</p>
            <nav className="sidebar-nav">
        {navItems.map((item) => {
            const Icon = item.icon;
            return (
                <NavLink key={item.to} to={item.to} className="nav-link">
                <Icon size={16} />
                <span>{item.label}</span>
                </NavLink>
            );
        })}
            </nav>
         </div>

         <div className="Sidebar-footer">
            <div className="user-card">
                <p>{user?.name || "Utilisateur"}</p>
                <small>{user?.role || "Analyste"}</small>
            </div>
            <NavLink to="Settings" className="nav-link">
                <Settings size={16}/>
                <span>Parametres</span>
            </NavLink>
            <button className="logout-btn" onClick={onLogout}>
                <LogOut size={16}/>
                <span>Deconnexion</span>
            </button>
         </div>
     </aside>
    );
}
export default SideBar;