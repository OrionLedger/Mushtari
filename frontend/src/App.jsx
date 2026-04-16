import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import Sidebar from './components/layout/Sidebar';
import TopNav from './components/layout/TopNav';
import Dashboard from './components/features/Dashboard';
import Vision from './components/features/Vision';
import Analyst from './components/features/Analyst';
import Explorer from './components/features/Explorer';
import Sources from './components/features/Sources';
import Alerts from './components/features/Alerts';
import Library from './components/features/Library';
import Reports from './components/features/Reports';

import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <ThemeProvider>
      <div className="app-container">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="main-content">
          <TopNav activeTab={activeTab} />
          <div className="content-inner">
            {activeTab === 'dashboard' && <Dashboard />}
            {activeTab === 'vision' && <Vision />}
            {activeTab === 'analyst' && <Analyst />}
            {activeTab === 'explorer' && <Explorer />}
            {activeTab === 'sources' && <Sources />}
            {activeTab === 'alerts' && <Alerts />}
            {activeTab === 'library' && <Library />}
            {activeTab === 'reports' && <Reports />}
          </div>
        </main>
      </div>
    </ThemeProvider>
  );
}

export default App;
