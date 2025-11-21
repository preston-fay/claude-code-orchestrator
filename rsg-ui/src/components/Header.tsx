import React from 'react';

interface HeaderProps {
  userId: string;
  userEmail: string;
  onSettingsClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ userId, userEmail, onSettingsClick }) => {
  return (
    <header className="header">
      <div className="header-left">
        <h1 className="header-title">Kearney Ready-Set-Go!</h1>
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
