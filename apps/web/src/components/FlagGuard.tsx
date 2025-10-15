/**
 * FlagGuard Component
 *
 * Conditionally renders children based on feature flag status.
 * Fetches flag state from governance API.
 */

import React, { useEffect, useState, ReactNode } from 'react';

interface FlagGuardProps {
  flag: string;
  children: ReactNode;
  fallback?: ReactNode;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function FlagGuard({ flag, children, fallback = null }: FlagGuardProps) {
  const [isEnabled, setIsEnabled] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchFlagStatus();
  }, [flag]);

  const fetchFlagStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/gov/flags`);
      if (res.ok) {
        const data = await res.json();
        const flagValue = data.flags[flag];
        setIsEnabled(flagValue === true);
      }
    } catch (err) {
      console.error(`Failed to fetch flag ${flag}:`, err);
      setIsEnabled(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <>{fallback}</>;
  }

  if (!isEnabled) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
