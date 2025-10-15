/**
 * Login page for Kearney Data Platform
 *
 * Supports:
 * - API key authentication
 * - OIDC SSO (if enabled)
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../security/AuthContext';

export function Login() {
  const [apiKey, setApiKey] = useState('');
  const [tenant, setTenant] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { loginWithApiKey } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/';

  const handleApiKeyLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await loginWithApiKey(apiKey, tenant || undefined);
      navigate(from, { replace: true });
    } catch (err) {
      setError('Invalid API key. Please check and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOIDCLogin = () => {
    // Redirect to OIDC provider (backend handles flow)
    window.location.href = '/api/auth/oidc/login';
  };

  // Check if OIDC is enabled (could be from config endpoint)
  const oidcEnabled = false; // TODO: Check from config

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#f5f5f5',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        width: '100%',
        maxWidth: '400px'
      }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
          <h1 style={{
            color: '#7823DC',
            fontSize: '1.75rem',
            fontWeight: 600,
            marginBottom: '0.5rem'
          }}>
            Kearney Data Platform
          </h1>
          <p style={{
            color: '#666',
            fontSize: '0.875rem'
          }}>
            Sign in to continue
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div style={{
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: '4px',
            padding: '0.75rem',
            marginBottom: '1rem',
            color: '#c00'
          }}>
            {error}
          </div>
        )}

        {/* API Key Form */}
        <form onSubmit={handleApiKeyLogin} style={{ marginBottom: oidcEnabled ? '1.5rem' : '0' }}>
          <div style={{ marginBottom: '1rem' }}>
            <label
              htmlFor="apiKey"
              style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: 500,
                marginBottom: '0.5rem',
                color: '#333'
              }}
            >
              API Key
            </label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="kdk_..."
              required
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '0.875rem',
                fontFamily: 'monospace'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="tenant"
              style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: 500,
                marginBottom: '0.5rem',
                color: '#333'
              }}
            >
              Tenant (optional)
            </label>
            <input
              id="tenant"
              type="text"
              value={tenant}
              onChange={(e) => setTenant(e.target.value)}
              placeholder="acme-corp"
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '0.875rem'
              }}
            />
            <p style={{
              fontSize: '0.75rem',
              color: '#666',
              marginTop: '0.25rem'
            }}>
              Leave blank to use default tenant
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || !apiKey}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: loading ? '#ccc' : '#7823DC',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.backgroundColor = '#6a1fc9';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.currentTarget.style.backgroundColor = '#7823DC';
              }
            }}
          >
            {loading ? 'Signing in...' : 'Sign in with API Key'}
          </button>
        </form>

        {/* OIDC SSO button */}
        {oidcEnabled && (
          <>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '1.5rem'
            }}>
              <div style={{ flex: 1, height: '1px', backgroundColor: '#ddd' }} />
              <span style={{
                padding: '0 0.75rem',
                fontSize: '0.75rem',
                color: '#999'
              }}>
                OR
              </span>
              <div style={{ flex: 1, height: '1px', backgroundColor: '#ddd' }} />
            </div>

            <button
              onClick={handleOIDCLogin}
              type="button"
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: 'white',
                color: '#333',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f9f9f9';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'white';
              }}
            >
              Sign in with SSO
            </button>
          </>
        )}

        {/* Footer */}
        <div style={{
          marginTop: '2rem',
          paddingTop: '1rem',
          borderTop: '1px solid #eee',
          textAlign: 'center',
          fontSize: '0.75rem',
          color: '#999'
        }}>
          <p>
            Need an API key? Contact your administrator.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
