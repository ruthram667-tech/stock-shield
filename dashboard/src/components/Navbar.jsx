import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Search, Bell, User, Clock } from 'lucide-react';

const pageTitles = {
  '/': 'Dashboard',
  '/inventory': 'Inventory Management',
  '/environment': 'Environment Monitoring',
  '/alerts': 'Alert Center',
};

export default function Navbar() {
  const location = useLocation();
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 30000);
    return () => clearInterval(interval);
  }, []);

  const title = pageTitles[location.pathname]
    || (location.pathname.startsWith('/inventory/') ? 'Item Detail' : 'Stock Shield');

  return (
    <header className="navbar">
      <div className="navbar-left">
        <h2 className="navbar-title">{title}</h2>
        <div className="navbar-search">
          <Search size={14} className="search-icon" strokeWidth={2} />
          <input placeholder="Search inventory..." />
        </div>
      </div>
      <div className="navbar-actions">
        <div className="navbar-clock">
          <Clock size={14} style={{ marginRight: 6, opacity: 0.7, verticalAlign: -2 }} strokeWidth={2} />
          {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
        <div className="navbar-badge" title="Notifications">
          <Bell size={18} strokeWidth={2} />
          <span className="badge-count">3</span>
        </div>
        <div className="navbar-badge" title="Profile">
          <User size={18} strokeWidth={2} />
        </div>
      </div>
    </header>
  );
}
