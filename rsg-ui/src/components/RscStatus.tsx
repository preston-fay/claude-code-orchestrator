import React from 'react';

/**
 * Ready-Set-Code (RSC) Status Component
 * 
 * Displays the three-stage workflow:
 * - READY: Planning + Architecture
 * - SET: Data + Development setup
 * - CODE: Implementation + QA + Documentation
 */

interface RscStatusProps {
  currentStage: string;
  readyCompleted: boolean;
  setCompleted: boolean;
  codeCompleted: boolean;
  onStartReady?: () => void;
  onStartSet?: () => void;
  onStartCode?: () => void;
  loading?: boolean;
}

const RscStatus: React.FC<RscStatusProps> = ({
  currentStage,
  readyCompleted,
  setCompleted,
  codeCompleted,
  onStartReady,
  onStartSet,
  onStartCode,
  loading = false,
}) => {
  const getStageStatus = (
    stageName: string,
    isCompleted: boolean,
    isPrevCompleted: boolean
  ): 'completed' | 'in-progress' | 'pending' => {
    if (isCompleted) return 'completed';
    if (currentStage === stageName || (isPrevCompleted && !isCompleted)) {
      return 'in-progress';
    }
    return 'pending';
  };

  const readyStatus = getStageStatus('ready', readyCompleted, true);
  const setStatus = getStageStatus('set', setCompleted, readyCompleted);
  const codeStatus = getStageStatus('code', codeCompleted, setCompleted);

  return (
    <div className="rsc-status">
      {/* READY Stage */}
      <div className={`rsc-card rsc-${readyStatus}`}>
        <div className="rsc-card-header">
          <h3>READY</h3>
          <span className={`status-badge status-${readyStatus}`}>
            {readyStatus === 'completed' ? 'Complete' :
             readyStatus === 'in-progress' ? 'In Progress' : 'Pending'}
          </span>
        </div>
        <div className="rsc-card-body">
          <p className="rsc-phases">Planning + Architecture</p>
          <ul className="phase-list">
            <li>System design</li>
            <li>Technical specifications</li>
            <li>Data models</li>
          </ul>
        </div>
        <div className="rsc-card-footer">
          {onStartReady && readyStatus !== 'completed' && (
            <button
              className="button-primary"
              onClick={onStartReady}
              disabled={loading || readyStatus === 'in-progress'}
            >
              {readyStatus === 'in-progress' ? 'Running...' : 'Start Ready'}
            </button>
          )}
          {readyStatus === 'completed' && (
            <span className="completed-check">&#10003; Complete</span>
          )}
        </div>
      </div>

      {/* SET Stage */}
      <div className={`rsc-card rsc-${setStatus}`}>
        <div className="rsc-card-header">
          <h3>SET</h3>
          <span className={`status-badge status-${setStatus}`}>
            {setStatus === 'completed' ? 'Complete' :
             setStatus === 'in-progress' ? 'In Progress' : 'Pending'}
          </span>
        </div>
        <div className="rsc-card-body">
          <p className="rsc-phases">Data + Development Setup</p>
          <ul className="phase-list">
            <li>Data pipelines</li>
            <li>Core scaffolding</li>
            <li>Environment setup</li>
          </ul>
        </div>
        <div className="rsc-card-footer">
          {onStartSet && setStatus !== 'completed' && readyCompleted && (
            <button
              className="button-primary"
              onClick={onStartSet}
              disabled={loading || setStatus === 'in-progress'}
            >
              {setStatus === 'in-progress' ? 'Running...' : 'Start Set'}
            </button>
          )}
          {setStatus === 'completed' && (
            <span className="completed-check">&#10003; Complete</span>
          )}
          {!readyCompleted && setStatus === 'pending' && (
            <span className="waiting-text">Waiting for Ready</span>
          )}
        </div>
      </div>

      {/* CODE Stage */}
      <div className={`rsc-card rsc-${codeStatus}`}>
        <div className="rsc-card-header">
          <h3>CODE</h3>
          <span className={`status-badge status-${codeStatus}`}>
            {codeStatus === 'completed' ? 'Complete' :
             codeStatus === 'in-progress' ? 'In Progress' : 'Pending'}
          </span>
        </div>
        <div className="rsc-card-body">
          <p className="rsc-phases">Implementation + QA + Docs</p>
          <ul className="phase-list">
            <li>Feature development</li>
            <li>Testing & validation</li>
            <li>Documentation</li>
          </ul>
        </div>
        <div className="rsc-card-footer">
          {onStartCode && codeStatus !== 'completed' && setCompleted && (
            <button
              className="button-primary"
              onClick={onStartCode}
              disabled={loading || codeStatus === 'in-progress'}
            >
              {codeStatus === 'in-progress' ? 'Running...' : 'Start Code'}
            </button>
          )}
          {codeStatus === 'completed' && (
            <span className="completed-check">&#10003; Complete</span>
          )}
          {!setCompleted && codeStatus === 'pending' && (
            <span className="waiting-text">Waiting for Set</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default RscStatus;
