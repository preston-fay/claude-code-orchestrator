import React, { useState, useEffect } from 'react';
import { getCurrentUser, updateProviderSettings } from '../api/client';
import { UserPublicProfile, ModelName } from '../api/types';

interface LlmSettingsProps {
  compact?: boolean;
}

const MODEL_OPTIONS: { id: ModelName; name: string; description: string }[] = [
  {
    id: 'claude-sonnet-4-5-20250929',
    name: 'Sonnet 4.5',
    description: 'Premium model - best for complex tasks',
  },
  {
    id: 'claude-haiku-4-5-20251015',
    name: 'Haiku 4.5',
    description: 'Cost-efficient - good for quick tasks',
  },
];

const LlmSettings: React.FC<LlmSettingsProps> = ({ compact = false }) => {
  const [user, setUser] = useState<UserPublicProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      setLoading(true);
      setError(null);
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (err) {
      setError('Failed to load user settings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleModelChange = async (modelId: string) => {
    if (!user) return;

    try {
      setSaving(true);
      setError(null);
      const updated = await updateProviderSettings({
        llm_provider: user.llm_provider,
        default_model: modelId,
      });
      setUser(updated);
    } catch (err) {
      setError('Failed to update model');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="llm-settings">
        <div className="loading-small">Loading model settings...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="llm-settings">
        <div className="error-small">{error || 'Failed to load settings'}</div>
      </div>
    );
  }

  const currentModel = MODEL_OPTIONS.find(m => m.id === user.default_model);

  return (
    <div className={`llm-settings ${compact ? 'compact' : ''}`}>
      <div className="settings-header">
        <h4>LLM Model</h4>
        {user.llm_key_set && (
          <span className="key-badge">API Key Set</span>
        )}
      </div>

      <div className="model-selector">
        <select
          value={user.default_model}
          onChange={(e) => handleModelChange(e.target.value)}
          disabled={saving}
          className="model-select"
        >
          {MODEL_OPTIONS.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
        {saving && <span className="saving-indicator">Saving...</span>}
      </div>

      {currentModel && !compact && (
        <p className="model-description">{currentModel.description}</p>
      )}

      {error && (
        <div className="settings-error">{error}</div>
      )}

      {!compact && (
        <div className="model-info">
          <p className="info-note">
            Sonnet 4.5 is the default for complex tasks.
            Haiku 4.5 is used as fallback for cost efficiency.
          </p>
          {user.token_usage && (
            <div className="token-stats">
              <span>Tokens used: {user.token_usage.total_input_tokens + user.token_usage.total_output_tokens}</span>
              <span>Requests: {user.token_usage.total_requests}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LlmSettings;
