import React, { useState, useEffect } from 'react';
import {
  getApiConfig,
  updateApiConfig,
  getCurrentUser,
  updateProviderSettings,
  testProviderConnection,
} from '../api/client';
import { UserPublicProfile, ProviderTestResult } from '../api/types';

interface SettingsPanelProps {
  onClose: () => void;
  onSave: () => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onClose, onSave }) => {
  const config = getApiConfig();

  // API Config state
  const [baseUrl, setBaseUrl] = useState(config.baseUrl);
  const [userId, setUserId] = useState(config.userId);
  const [userEmail, setUserEmail] = useState(config.userEmail);

  // User profile state
  const [userProfile, setUserProfile] = useState<UserPublicProfile | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(false);

  // LLM Provider settings
  const [llmProvider, setLlmProvider] = useState<string>('anthropic');
  const [apiKey, setApiKey] = useState<string>('');
  const [defaultModel, setDefaultModel] = useState<string>('claude-sonnet-4-5-20250929');

  // Model options per provider
  const modelOptions: Record<string, { value: string; label: string; tooltip?: string }[]> = {
    anthropic: [
      { value: 'claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5 (default)', tooltip: 'Recommended for most tasks' },
      { value: 'claude-haiku-4-5-20251015', label: 'Claude Haiku 4.5 (cost-efficient)', tooltip: 'Use for cost-efficient mode' },
    ],
    bedrock: [
      { value: 'claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5 (default)', tooltip: 'Recommended for most tasks' },
      { value: 'claude-haiku-4-5-20251015', label: 'Claude Haiku 4.5 (cost-efficient)', tooltip: 'Use for cost-efficient mode' },
    ],
  };

  // Test connection state
  const [testStatus, setTestStatus] = useState<ProviderTestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isSavingProvider, setIsSavingProvider] = useState(false);

  // Load user profile when settings open
  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      setLoadingProfile(true);
      const profile = await getCurrentUser();
      setUserProfile(profile);
      setLlmProvider(profile.llm_provider);
      setDefaultModel(profile.default_model);
      // Don't set apiKey from backend - we never get the full key
    } catch (e) {
      console.error('Failed to load user profile:', e);
    } finally {
      setLoadingProfile(false);
    }
  };

  const handleSaveApiConfig = () => {
    updateApiConfig(baseUrl, userId, userEmail);
    onSave();
  };

  const handleTestConnection = async () => {
    try {
      setIsTesting(true);
      setTestStatus(null);
      const result = await testProviderConnection({
        llm_provider: llmProvider,
        api_key: apiKey || undefined,
        default_model: defaultModel || undefined,
      });
      setTestStatus(result);
    } catch (e) {
      setTestStatus({
        success: false,
        provider: llmProvider,
        model: defaultModel,
        message: 'Error testing provider connection',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveProviderSettings = async () => {
    try {
      setIsSavingProvider(true);
      const updated = await updateProviderSettings({
        llm_provider: llmProvider,
        api_key: apiKey || undefined,
        default_model: defaultModel || undefined,
      });
      setUserProfile(updated);
      setApiKey(''); // Clear local field after save
      setTestStatus(null);
    } catch (e) {
      console.error('Failed to save provider settings:', e);
    } finally {
      setIsSavingProvider(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Settings</h2>
          <button className="close-button" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          {/* API Configuration Section */}
          <section className="settings-section">
            <h3>API Configuration</h3>
            <p className="settings-description">
              Configure connection to the RSC Engine backend.
            </p>

            <div className="form-group">
              <label htmlFor="baseUrl">API Base URL</label>
              <input
                id="baseUrl"
                type="text"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="http://localhost:8000"
              />
              <small>RSC API endpoint (local or App Runner)</small>
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

            <div className="button-row">
              <button className="button-primary" onClick={handleSaveApiConfig}>
                Save API Settings
              </button>
            </div>
          </section>

          {/* LLM Access Section */}
          <section className="settings-section">
            <h3>LLM Access</h3>
            <p className="settings-description">
              Configure how Ready-Set-Code connects to your LLM provider.
              Use an Anthropic API key (BYOK) or AWS Bedrock.
            </p>

            {loadingProfile ? (
              <div className="loading-inline">Loading profile...</div>
            ) : (
              <>
                <div className="form-group">
                  <label htmlFor="llmProvider">Provider</label>
                  <select
                    id="llmProvider"
                    value={llmProvider}
                    onChange={(e) => {
                      const newProvider = e.target.value;
                      setLlmProvider(newProvider);
                      // Reset to provider's default model
                      const providerModels = modelOptions[newProvider];
                      if (providerModels && providerModels.length > 0) {
                        setDefaultModel(providerModels[0].value);
                      }
                    }}
                  >
                    <option value="anthropic">Anthropic API (BYOK)</option>
                    <option value="bedrock">AWS Bedrock (IAM)</option>
                  </select>
                </div>

                {llmProvider === 'anthropic' && (
                  <div className="form-group">
                    <label htmlFor="apiKey">Anthropic API Key</label>
                    <input
                      id="apiKey"
                      type="password"
                      placeholder={
                        userProfile?.llm_key_set
                          ? `API key is set (••••${userProfile.llm_key_suffix ?? ''})`
                          : 'Enter your sk-ant-... key'
                      }
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      autoComplete="off"
                    />
                    <small>
                      Key is stored securely in the backend and never shown in full.
                    </small>
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="defaultModel">Default Model</label>
                  <select
                    id="defaultModel"
                    value={defaultModel}
                    onChange={(e) => setDefaultModel(e.target.value)}
                    title="Recommended default: Sonnet 4.5. Use Haiku 4.5 for cost-efficient mode."
                  >
                    {(modelOptions[llmProvider] || []).map((option) => (
                      <option key={option.value} value={option.value} title={option.tooltip}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <small>Recommended default: Sonnet 4.5. Use Haiku 4.5 for cost-efficient mode.</small>
                </div>

                <div className="button-row">
                  <button
                    className="button-secondary"
                    type="button"
                    disabled={isTesting}
                    onClick={handleTestConnection}
                  >
                    {isTesting ? 'Testing...' : 'Test Connection'}
                  </button>
                  <button
                    className="button-primary"
                    type="button"
                    disabled={isSavingProvider}
                    onClick={handleSaveProviderSettings}
                  >
                    {isSavingProvider ? 'Saving...' : 'Save Provider Settings'}
                  </button>
                </div>

                {testStatus && (
                  <div
                    className={`test-status ${
                      testStatus.success ? 'test-status-success' : 'test-status-error'
                    }`}
                  >
                    <strong>{testStatus.success ? 'Success' : 'Error'}:</strong>{' '}
                    {testStatus.message}
                  </div>
                )}
              </>
            )}
          </section>

          {/* Usage Section */}
          {userProfile && (
            <section className="settings-section">
              <h3>Token Usage</h3>
              <p className="settings-description">
                Approximate token usage tracked by Ready-Set-Code.
              </p>
              <div className="usage-grid">
                <div className="usage-card">
                  <span className="usage-label">Input Tokens</span>
                  <span className="usage-value">
                    {userProfile.token_usage.total_input_tokens.toLocaleString()}
                  </span>
                </div>
                <div className="usage-card">
                  <span className="usage-label">Output Tokens</span>
                  <span className="usage-value">
                    {userProfile.token_usage.total_output_tokens.toLocaleString()}
                  </span>
                </div>
                <div className="usage-card">
                  <span className="usage-label">Total Requests</span>
                  <span className="usage-value">
                    {userProfile.token_usage.total_requests.toLocaleString()}
                  </span>
                </div>
              </div>
            </section>
          )}
        </div>

        <div className="modal-footer">
          <button className="button-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
