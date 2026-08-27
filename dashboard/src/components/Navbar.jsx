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
          <Search size={14} className="search-icon" />
          <input placeholder="Search inventory..." />
        </div>
      </div>
      <div className="navbar-actions">
        <div className="navbar-clock">
          <Clock size={12} style={{ marginRight: 5, opacity: 0.5, verticalAlign: -1 }} />
          {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
        <div className="navbar-badge" title="Notifications">
          <Bell size={16} />
          <span className="badge-dot" />
        </div>
        <div className="navbar-badge" title="Profile">
          <User size={16} />
        </div>
      </div>
    </header>
  );
}
