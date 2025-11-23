import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArtifactContent } from '../api/types';

interface ArtifactViewerModalProps {
  artifact: ArtifactContent;
  onClose: () => void;
}

type TabType = 'preview' | 'raw' | 'metadata';

export function ArtifactViewerModal({ artifact, onClose }: ArtifactViewerModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('preview');

  const renderPreview = () => {
    switch (artifact.artifact_type) {
      case 'markdown':
        return (
          <div className="artifact-markdown">
            <ReactMarkdown>{artifact.content}</ReactMarkdown>
          </div>
        );
      case 'json':
        try {
          const parsed = JSON.parse(artifact.content);
          return (
            <pre className="artifact-json">
              {JSON.stringify(parsed, null, 2)}
            </pre>
          );
        } catch {
          return <pre className="artifact-text">{artifact.content}</pre>;
        }
      case 'code':
        return (
          <pre className="artifact-code">
            <code>{artifact.content}</code>
          </pre>
        );
      case 'yaml':
        return (
          <pre className="artifact-yaml">
            {artifact.content}
          </pre>
        );
      default:
        return (
          <pre className="artifact-text">
            {artifact.content}
          </pre>
        );
    }
  };

  const renderRaw = () => {
    return (
      <pre className="artifact-raw">
        {artifact.content}
      </pre>
    );
  };

  const renderMetadata = () => {
    const metadataEntries = Object.entries(artifact.metadata).filter(
      ([_, value]) => value !== undefined && value !== null
    );

    return (
      <div className="artifact-metadata">
        <table>
          <tbody>
            <tr>
              <td><strong>ID</strong></td>
              <td>{artifact.id}</td>
            </tr>
            <tr>
              <td><strong>Name</strong></td>
              <td>{artifact.name}</td>
            </tr>
            <tr>
              <td><strong>Phase</strong></td>
              <td>{artifact.phase}</td>
            </tr>
            <tr>
              <td><strong>Type</strong></td>
              <td>{artifact.artifact_type}</td>
            </tr>
            <tr>
              <td><strong>Path</strong></td>
              <td className="metadata-path">{artifact.path}</td>
            </tr>
            {metadataEntries.map(([key, value]) => (
              <tr key={key}>
                <td><strong>{key.replace(/_/g, ' ')}</strong></td>
                <td>
                  {typeof value === 'object'
                    ? JSON.stringify(value)
                    : String(value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="artifact-modal" onClick={(e) => e.stopPropagation()}>
        <div className="artifact-modal-header">
          <h2>{artifact.name}</h2>
          <span className="artifact-phase-badge">{artifact.phase}</span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="artifact-tabs">
          <button
            className={`tab ${activeTab === 'preview' ? 'active' : ''}`}
            onClick={() => setActiveTab('preview')}
          >
            Preview
          </button>
          <button
            className={`tab ${activeTab === 'raw' ? 'active' : ''}`}
            onClick={() => setActiveTab('raw')}
          >
            Raw
          </button>
          <button
            className={`tab ${activeTab === 'metadata' ? 'active' : ''}`}
            onClick={() => setActiveTab('metadata')}
          >
            Metadata
          </button>
        </div>

        <div className="artifact-content">
          {activeTab === 'preview' && renderPreview()}
          {activeTab === 'raw' && renderRaw()}
          {activeTab === 'metadata' && renderMetadata()}
        </div>
      </div>
    </div>
  );
}

export default ArtifactViewerModal;
