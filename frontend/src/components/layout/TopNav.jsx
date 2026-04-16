import React from 'react';
import { Sun, Moon, Search, Bell } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

const TopNav = ({ activeTab }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <nav className="top-nav">
      <div>
        <h1 className="outfit" style={{ fontSize: '28px' }}>
          {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Welcome back to OrionLedger Forecast System
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div className="surface" style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '10px', borderRadius: '12px' }}>
          <Search size={18} color="var(--text-secondary)" />
          <input 
            type="text" 
            placeholder="Search products..." 
            style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', width: '200px' }}
          />
        </div>

        <button className="btn btn-ghost" onClick={toggleTheme} title="Toggle Theme">
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>

        <button className="btn btn-ghost">
          <Bell size={20} />
        </button>

        <div style={{ width: '40px', height: '40px', borderRadius: 'full', backgroundColor: 'var(--accent-color)', display: 'flex', alignItems: 'center', justify: 'center', fontWeight: 'bold', color: '#0f172a', cursor: 'pointer', borderRadius: '50%' }}>
          JD
        </div>
      </div>
    </nav>
  );
};

export default TopNav;
