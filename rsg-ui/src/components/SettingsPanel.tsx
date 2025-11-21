import React, { useState } from 'react';
import { getApiConfig, updateApiConfig } from '../api/client';

interface SettingsPanelProps {
  onClose: () => void;
  onSave: () => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onClose, onSave }) => {
  const config = getApiConfig();
  const [baseUrl, setBaseUrl] = useState(config.baseUrl);
  const [userId, setUserId] = useState(config.userId);
  const [userEmail, setUserEmail] = useState(config.userEmail);

  const handleSave = () => {
    updateApiConfig(baseUrl, userId, userEmail);
    onSave();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Settings</h2>
          <button className="close-button" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="baseUrl">API Base URL</label>
            <input
              id="baseUrl"
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:8000"
            />
            <small>Orchestrator API endpoint (local or App Runner)</small>
          </div>

          <div className="form-group">
            <label htmlFor="userId">User ID</label>
            <input
              id="userId"
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="dev-user"
            />
            <small>Your unique identifier (maps to X-User-Id header)</small>
          </div>

          <div className="form-group">
            <label htmlFor="userEmail">User Email</label>
            <input
              id="userEmail"
              type="email"
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
              placeholder="dev@example.com"
            />
            <small>Your email (maps to X-User-Email header)</small>
          </div>
        </div>

        <div className="modal-footer">
          <button className="button-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="button-primary" onClick={handleSave}>
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
