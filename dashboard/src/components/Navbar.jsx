import { useLocation } from 'react-router-dom';

const pageTitles = {
  '/': 'Dashboard',
  '/inventory': 'Inventory Management',
  '/environment': 'Environment Monitoring',
  '/alerts': 'Alert Center',
};

export default function Navbar() {
  const location = useLocation();

  // Handle dynamic routes like /inventory/:id
  const title = pageTitles[location.pathname]
    || (location.pathname.startsWith('/inventory/') ? 'Item Detail' : 'Stock Shield');

  return (
    <header className="navbar">
      <h2 className="navbar-title">{title}</h2>
      <div className="navbar-actions">
        <div className="navbar-badge" title="Notifications">
          🔔
          <span className="badge-dot"></span>
        </div>
        <div className="navbar-badge" title="Admin">
          👤
        </div>
      </div>
    </header>
  );
}
