import { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import SettingsPanel from './components/SettingsPanel';
import ProjectListPage from './pages/ProjectListPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import ProjectAppBuildPage from './pages/ProjectAppBuildPage';
import { getApiConfig } from './api/client';

function App() {
  const [showSettings, setShowSettings] = useState(false);
  const [config, setConfig] = useState(getApiConfig());

  useEffect(() => {
    setConfig(getApiConfig());
  }, []);

  const handleConfigUpdate = () => {
    setConfig(getApiConfig());
    setShowSettings(false);
  };

  return (
    <div className="app">
      <Header
        userId={config.userId}
        userEmail={config.userEmail}
        onSettingsClick={() => setShowSettings(true)}
      />

      <main className="main-content">
        <Routes>
          <Route path="/" element={<ProjectListPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/projects/:projectId/build" element={<ProjectAppBuildPage />} />
        </Routes>
      </main>

      {showSettings && (
        <SettingsPanel
          onClose={() => setShowSettings(false)}
          onSave={handleConfigUpdate}
        />
      )}
    </div>
  );
}

export default App;
