import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import Sidebar from './components/layout/Sidebar';
import TopNav from './components/layout/TopNav';
import Dashboard from './components/features/Dashboard';
import Product from './components/features/Product';

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
            {activeTab === 'product' && <Product />}
          </div>
        </main>
      </div>
    </ThemeProvider>
  );
}

export default App;
