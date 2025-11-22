import React from 'react';

interface RsgStatusProps {
  currentStage: string;
  readyCompleted: boolean;
  setCompleted: boolean;
  goCompleted: boolean;
  onStartReady?: () => void;
  onStartSet?: () => void;
  onStartGo?: () => void;
  loading?: boolean;
}

const RsgStatus: React.FC<RsgStatusProps> = ({
  currentStage,
  readyCompleted,
  setCompleted,
  goCompleted,
  onStartReady,
  onStartSet,
  onStartGo,
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
  const goStatus = getStageStatus('go', goCompleted, setCompleted);

  return (
    <div className="rsg-status">
      <div className={`rsg-card rsg-${readyStatus}`}>
        <div className="rsg-card-header">
          <h3>READY</h3>
          <span className={`status-badge status-${readyStatus}`}>
            {readyStatus === 'completed' ? 'Complete' :
             readyStatus === 'in-progress' ? 'In Progress' : 'Pending'}
          </span>
        </div>
        <div className="rsg-card-body">
          <p className="rsg-phases">Planning + Architecture</p>
          <ul className="phase-list">
            <li>System design</li>
            <li>Technical specifications</li>
            <li>Data models</li>
          </ul>
        </div>
        <div className="rsg-card-footer">
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

      <div className={`rsg-card rsg-${setStatus}`}>
        <div className="rsg-card-header">
          <h3>SET</h3>
          <span className={`status-badge status-${setStatus}`}>
            {setStatus === 'completed' ? 'Complete' :
             setStatus === 'in-progress' ? 'In Progress' : 'Pending'}
          </span>
        </div>
        <div className="rsg-card-body">
          <p className="rsg-phases">Data + Development</p>
          <ul className="phase-list">
            <li>Data pipelines</li>
            <li>Core implementation</li>
            <li>Feature development</li>
          </ul>
        </div>
        <div className="rsg-card-footer">
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

      <div className={`rsg-card rsg-${goStatus}`}>
        <div className="rsg-card-header">
          <h3>GO</h3>
          <span className={`status-badge status-${goStatus}`}>
            {goStatus === 'completed' ? 'Complete' :
             goStatus === 'in-progress' ? 'In Progress' : 'Pending'}
          </span>
        </div>
        <div className="rsg-card-body">
          <p className="rsg-phases">QA + Documentation</p>
          <ul className="phase-list">
            <li>Testing & validation</li>
            <li>Documentation</li>
            <li>Final review</li>
          </ul>
        </div>
        <div className="rsg-card-footer">
          {onStartGo && goStatus !== 'completed' && setCompleted && (
            <button
              className="button-primary"
              onClick={onStartGo}
              disabled={loading || goStatus === 'in-progress'}
            >
              {goStatus === 'in-progress' ? 'Running...' : 'Start Go'}
            </button>
          )}
          {goStatus === 'completed' && (
            <span className="completed-check">&#10003; Complete</span>
          )}
          {!setCompleted && goStatus === 'pending' && (
            <span className="waiting-text">Waiting for Set</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default RsgStatus;
