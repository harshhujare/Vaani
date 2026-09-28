import { NavLink, useLocation } from 'react-router-dom';
import {
  HiOutlineHome, HiOutlineUsers, HiOutlineAcademicCap,
  HiOutlineClipboardDocumentList, HiOutlineChartBar,
  HiOutlineCog6Tooth
} from 'react-icons/hi2';

const navItems = [
  { section: 'Overview' },
  { path: '/', label: 'Dashboard', icon: HiOutlineHome },
  { section: 'Management' },
  { path: '/beneficiaries', label: 'Beneficiaries', icon: HiOutlineUsers },
  { path: '/programs', label: 'Training Programs', icon: HiOutlineAcademicCap },
  { path: '/enrollments', label: 'Enrollments', icon: HiOutlineClipboardDocumentList },
  { section: 'Insights' },
  { path: '/analytics', label: 'Analytics', icon: HiOutlineChartBar },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">V</div>
        <div>
          <h1>VaniSetu</h1>
          <span>Platform Dashboard</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item, i) => {
          if (item.section) {
            return (
              <div key={i} className="sidebar-section-title">
                {item.section}
              </div>
            );
          }
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''}`
              }
              end={item.path === '/'}
            >
              <item.icon />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
