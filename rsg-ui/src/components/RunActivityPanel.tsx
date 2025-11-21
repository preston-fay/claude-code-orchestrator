import React, { useState, useEffect, useRef } from 'react';
import { getProjectEvents } from '../api/client';
import { OrchestratorEvent } from '../api/types';

interface RunActivityPanelProps {
  projectId: string;
  isRunning: boolean;
}

// Map event types to display icons/colors
const eventTypeConfig: Record<string, { icon: string; className: string }> = {
  workflow_started: { icon: '▶', className: 'event-workflow' },
  workflow_completed: { icon: '✓', className: 'event-success' },
  workflow_failed: { icon: '✗', className: 'event-error' },
  phase_started: { icon: '◉', className: 'event-phase' },
  phase_completed: { icon: '●', className: 'event-success' },
  phase_failed: { icon: '○', className: 'event-error' },
  agent_started: { icon: '→', className: 'event-agent' },
  agent_completed: { icon: '←', className: 'event-success' },
  agent_failed: { icon: '✗', className: 'event-error' },
  governance_check_started: { icon: '◇', className: 'event-governance' },
  governance_check_passed: { icon: '◆', className: 'event-success' },
  governance_check_failed: { icon: '◇', className: 'event-error' },
  checkpoint_created: { icon: '◫', className: 'event-checkpoint' },
  checkpoint_passed: { icon: '◧', className: 'event-success' },
  checkpoint_failed: { icon: '◨', className: 'event-error' },
  llm_request_started: { icon: '⟳', className: 'event-llm' },
  llm_request_completed: { icon: '⟲', className: 'event-success' },
  llm_request_failed: { icon: '⟳', className: 'event-error' },
  info: { icon: 'ℹ', className: 'event-info' },
  warning: { icon: '⚠', className: 'event-warning' },
  error: { icon: '✗', className: 'event-error' },
};

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function formatRelativeTime(timestamp: string): string {
  const now = new Date();
  const eventTime = new Date(timestamp);
  const diffMs = now.getTime() - eventTime.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return formatTimestamp(timestamp);
}

const RunActivityPanel: React.FC<RunActivityPanelProps> = ({
  projectId,
  isRunning,
}) => {
  const [events, setEvents] = useState<OrchestratorEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const panelRef = useRef<HTMLDivElement>(null);
  const previousEventsLengthRef = useRef(0);

  // Fetch events
  const fetchEvents = async () => {
    try {
      const data = await getProjectEvents(projectId, 100);
      // Events come sorted newest first, reverse for display
      setEvents(data.reverse());
      setError(null);
    } catch (e) {
      console.error('Failed to fetch events:', e);
      setError('Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchEvents();
  }, [projectId]);

  // Poll for updates when running
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(fetchEvents, 2000);
    return () => clearInterval(interval);
  }, [projectId, isRunning]);

  // Auto-scroll when new events arrive
  useEffect(() => {
    if (autoScroll && panelRef.current && events.length > previousEventsLengthRef.current) {
      panelRef.current.scrollTop = panelRef.current.scrollHeight;
    }
    previousEventsLengthRef.current = events.length;
  }, [events, autoScroll]);

  // Handle manual scroll to detect if user scrolled up
  const handleScroll = () => {
    if (panelRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = panelRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setAutoScroll(isAtBottom);
    }
  };

  if (loading) {
    return (
      <div className="activity-panel">
        <div className="activity-header">
          <h3>Run Activity</h3>
        </div>
        <div className="activity-body">
          <div className="activity-loading">Loading events...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="activity-panel">
        <div className="activity-header">
          <h3>Run Activity</h3>
        </div>
        <div className="activity-body">
          <div className="activity-error">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="activity-panel">
      <div className="activity-header">
        <h3>Run Activity</h3>
        <div className="activity-meta">
          {isRunning && <span className="activity-running">Running</span>}
          <span className="activity-count">{events.length} events</span>
        </div>
      </div>
      <div
        className="activity-body"
        ref={panelRef}
        onScroll={handleScroll}
      >
        {events.length === 0 ? (
          <div className="activity-empty">
            No events yet. Start a phase to see activity.
          </div>
        ) : (
          <ul className="event-list">
            {events.map((event) => {
              const config = eventTypeConfig[event.event_type] || {
                icon: '•',
                className: 'event-default',
              };

              return (
                <li key={event.id} className={`event-item ${config.className}`}>
                  <span className="event-icon">{config.icon}</span>
                  <span className="event-time" title={new Date(event.timestamp).toLocaleString()}>
                    {formatRelativeTime(event.timestamp)}
                  </span>
                  <span className="event-message">{event.message}</span>
                  {event.phase && (
                    <span className="event-phase-tag">{event.phase}</span>
                  )}
                  {event.agent_id && (
                    <span className="event-agent-tag">{event.agent_id}</span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
      {!autoScroll && events.length > 0 && (
        <button
          className="scroll-to-bottom"
          onClick={() => {
            setAutoScroll(true);
            if (panelRef.current) {
              panelRef.current.scrollTop = panelRef.current.scrollHeight;
            }
          }}
        >
          ↓ Scroll to latest
        </button>
      )}
    </div>
  );
};

export default RunActivityPanel;
