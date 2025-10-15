/**
 * PrivateRoute wrapper component
 *
 * Protects routes requiring authentication.
 * Redirects to /login if not authenticated.
 */

import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

interface PrivateRouteProps {
  children: ReactNode;
  requireAdmin?: boolean;
  requireEditor?: boolean;
}

export function PrivateRoute({
  children,
  requireAdmin = false,
  requireEditor = false,
}: PrivateRouteProps) {
  const { isAuthenticated, isAdmin, isEditor } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to login, preserving the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role requirements
  if (requireAdmin && !isAdmin) {
    return (
      <div style={{
        padding: '2rem',
        fontFamily: 'Arial, sans-serif',
        maxWidth: '600px',
        margin: '0 auto'
      }}>
        <h1 style={{ color: '#7823DC', marginBottom: '1rem' }}>Access Denied</h1>
        <p style={{ marginBottom: '1rem' }}>
          This page requires administrator privileges.
        </p>
        <p style={{ color: '#666' }}>
          Contact your administrator if you believe you should have access.
        </p>
      </div>
    );
  }

  if (requireEditor && !isEditor) {
    return (
      <div style={{
        padding: '2rem',
        fontFamily: 'Arial, sans-serif',
        maxWidth: '600px',
        margin: '0 auto'
      }}>
        <h1 style={{ color: '#7823DC', marginBottom: '1rem' }}>Access Denied</h1>
        <p style={{ marginBottom: '1rem' }}>
          This page requires editor or administrator privileges.
        </p>
        <p style={{ color: '#666' }}>
          Contact your administrator if you believe you should have access.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}

export default PrivateRoute;
