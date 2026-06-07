import React from 'react';
import { TrendingUp, LayoutDashboard, Package, Settings } from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const mainItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { id: 'product',   label: 'Products',  icon: <Package size={20} /> },
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
