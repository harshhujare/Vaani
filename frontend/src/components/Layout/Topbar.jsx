import { useLocation, useNavigate } from 'react-router-dom';
import { HiOutlineArrowRightOnRectangle } from 'react-icons/hi2';

const pageTitles = {
  '/': 'Dashboard',
  '/beneficiaries': 'Beneficiaries',
  '/programs': 'Training Programs',
  '/enrollments': 'Enrollments',
  '/analytics': 'Analytics',
};

export default function Topbar() {
  const location = useLocation();
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem('vanisetu_user') || '{}');
  const title = pageTitles[location.pathname] || 'VaniSetu';

  const handleLogout = () => {
    localStorage.removeItem('vanisetu_token');
    localStorage.removeItem('vanisetu_user');
    navigate('/login');
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <h2>{title}</h2>
      </div>

      <div className="topbar-right">
        <div className="topbar-user">
          <div className="avatar">
            {(user.name || 'U').charAt(0).toUpperCase()}
          </div>
          <div className="user-info">
            <span className="user-name">{user.name || 'User'}</span>
            <span className="user-role">{user.role || 'viewer'}</span>
          </div>
        </div>

        <button
          className="btn btn-secondary btn-sm"
          onClick={handleLogout}
          title="Logout"
        >
          <HiOutlineArrowRightOnRectangle />
        </button>
      </div>
    </header>
  );
}
