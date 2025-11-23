import { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import SettingsPanel from './components/SettingsPanel';
import LaunchpadPage from './pages/LaunchpadPage';
import ProjectListPage from './pages/ProjectListPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import ProjectDashboardPage from './pages/ProjectDashboardPage';
import ProjectAppBuildPage from './pages/ProjectAppBuildPage';
import ProjectFeaturesPage from './pages/ProjectFeaturesPage';
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
          <Route path="/" element={<LaunchpadPage />} />
          <Route path="/projects" element={<ProjectListPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/projects/:projectId/dashboard" element={<ProjectDashboardPage />} />
          <Route path="/projects/:projectId/app-build" element={<ProjectAppBuildPage />} />
          <Route path="/projects/:projectId/features" element={<ProjectFeaturesPage />} />
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
