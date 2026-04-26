import { Activity, BellRing, RefreshCw } from "lucide-react";

function Topbar(){
    return(
    <header className="topbar">
      <div>
        <h2 className="topbar-title">BudgetAI Platform</h2>
        <p className="topbar-sub">Predire. Planifier. Performer.</p>
      </div>
       <div className="topbar-right">
        <div className="api-status">
          <Activity size={14} />
          <span>API active</span>
        </div>
        <button className="icon-btn" type="button" aria-label="refresh">
          <RefreshCw size={16} />
        </button>
        <button className="icon-btn" type="button" aria-label="notifications">
          <BellRing size={16} />
        </button>
      </div>
      </header>
    );


}
export default Topbar;