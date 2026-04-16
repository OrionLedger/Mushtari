import React, { useState } from 'react';
import { 
  LayoutDashboard, TrendingUp, Cpu, Database, PieChart, 
  Settings, ChevronDown, ChevronRight, SlidersHorizontal, 
  Eye, Sparkles, Table as TableIcon, Bell, Library as LibraryIcon, FileText
} from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const mainItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { id: 'alerts',    label: 'Alerts',    icon: <Bell size={20} /> },
    { id: 'vision',    label: 'Vision',    icon: <Eye size={20} /> },
    { id: 'analyst',   label: 'AI Analyst', icon: <Sparkles size={20} /> },
    { id: 'library',   label: 'Library',   icon: <LibraryIcon size={20} /> },
    { id: 'reports',   label: 'Reports',   icon: <FileText size={20} /> },
    { id: 'explorer',  label: 'Data Explorer', icon: <TableIcon size={20} /> },
    { id: 'sources',   label: 'Data Sources', icon: <Database size={20} /> },
  ];

  return (
    <aside className="sidebar glass">
      <div className="logo outfit">
        <TrendingUp size={28} />
        <span>Moshtari</span>
      </div>

      <nav className="nav-links">
        {mainItems.map((item) => (
          <div
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            {item.icon}
            <span>{item.label}</span>
          </div>
        ))}
      </nav>

      <div style={{ marginTop: 'auto' }}>
        <div className="nav-item">
          <Settings size={20} />
          <span>Settings</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
