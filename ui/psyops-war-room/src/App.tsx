import { Link, Outlet, useLocation } from 'react-router-dom';
import './theme/global.css';
import { prefetchRoute } from '@/utils/prefetch';

export default function App() {
  if (!document.documentElement.getAttribute('data-theme')) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
  const loc = useLocation();
  return (
    <div>
      <nav>
        <h1>🛰️ PsyOps War Room</h1>
        <div className="links">
          <Link to="/" onMouseEnter={() => prefetchRoute('overview')} aria-current={loc.pathname === '/' ? 'page' : undefined}>Overview</Link>
          <Link to="/endpoints" onMouseEnter={() => prefetchRoute('endpoints')} aria-current={loc.pathname.startsWith('/endpoints') ? 'page' : undefined}>Endpoints</Link>
          <Link to="/actions" onMouseEnter={() => prefetchRoute('actions')} aria-current={loc.pathname.startsWith('/actions') ? 'page' : undefined}>Runbook Actions</Link>
        </div>
      </nav>
      <main className="container">
        <Outlet />
      </main>
    </div>
  );
}
