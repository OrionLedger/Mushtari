import React from 'react';
import { TrendingUp, LayoutDashboard, Package, Bell, Settings, Upload } from 'lucide-react';
import { useI18n } from '../../i18n';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const { t } = useI18n();

  const mainItems = [
    { id: 'dashboard', labelKey: 'sidebar.dashboard', icon: <LayoutDashboard size={20} /> },
    { id: 'product',   labelKey: 'sidebar.product',   icon: <Package size={20} /> },
    { id: 'import',    labelKey: 'sidebar.import',    icon: <Upload size={20} /> },
    { id: 'alerts',    labelKey: 'sidebar.alerts',    icon: <Bell size={20} /> },
  ];

  return (
    <aside className="sidebar glass">
      <div className="logo outfit">
        <TrendingUp size={28} />
        <div>
          <span>Moshtari</span>
          <div style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: '400', marginTop: '-2px', lineHeight: '1.2' }}>
            {t('sidebar.tagline')}
          </div>
        </div>
      </div>

      <nav className="nav-links">
        {mainItems.map((item) => (
          <div
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            {item.icon}
            <span>{t(item.labelKey)}</span>
          </div>
        ))}
      </nav>

      <div style={{ marginTop: 'auto' }}>
        <div className="nav-item">
          <Settings size={20} />
          <span>{t('sidebar.settings')}</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
