import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface HeaderProps {
  userId: string;
  userEmail: string;
  onSettingsClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ userId, userEmail, onSettingsClick }) => {
  const location = useLocation();

  return (
    <header className="header">
      <div className="header-left">
        <Link to="/" style={{ textDecoration: 'none' }}>
          <h1 className="header-title">Kearney Ready-Set-Code</h1>
        </Link>
        <nav className="header-nav">
          <Link
            to="/"
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Projects
          </Link>
        </nav>
      </div>
      <div className="header-right">
        <div className="user-info">
          <span className="user-id">{userId}</span>
          <span className="user-email">{userEmail}</span>
        </div>
        <button className="settings-button" onClick={onSettingsClick}>
          Settings
        </button>
      </div>
    </header>
  );
};

export default Header;
