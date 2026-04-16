import React, { useState, useMemo } from 'react';
import { 
  Bell, AlertTriangle, Activity, Settings, 
  ChevronRight, Filter, CheckCircle2, X,
  Clock, ArrowRight
} from 'lucide-react';

const MOCK_ALERTS = [
  { id: 1, type: 'anomaly', status: 'active', message: 'Sudden 40% spike in Demand for SKU-204', time: '12m ago', level: 'high', details: 'The system detected an unusual volume of orders from North Regency region. Possible social media trend or bulk order.' },
  { id: 2, type: 'threshold', status: 'active', message: 'Inventory for "Vase #102" below safety stock (5)', time: '1h ago', level: 'medium', details: 'Current stock is 4 units. Previous average lead time from Fakhoury Intl is 14 days.' },
  { id: 3, type: 'system', status: 'resolved', message: 'Database sync successfully completed', time: '3h ago', level: 'low', details: 'Nightly batch job #802 (PostgreSQL -> Warehouse) finished without errors. 40,200 records processed.' },
  { id: 4, type: 'anomaly', status: 'active', message: 'Negative price variance detected in Organic channel', time: '5h ago', level: 'high', details: 'Transaction ID #9021 showed a sales price significantly lower than market value. Investigative audit recommended.' },
  { id: 5, type: 'threshold', status: 'resolved', message: 'CAC exceeds limit ($45.00) in Facebook Ads', time: '1d ago', level: 'medium', details: 'Daily spend reached $1,200 with conversion rate below 1.2%.' },
  { id: 6, type: 'system', status: 'active', message: 'Partial failure in API response (3rd party)', time: '2d ago', level: 'low', details: 'External currency exchange API returned 503 errors for 15 minutes.' },
];

const Alerts = () => {
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedAlert, setSelectedAlert] = useState(null);

  const filteredAlerts = useMemo(() => {
    return MOCK_ALERTS.filter(alert => {
      const matchType = filterType === 'all' || alert.type === filterType;
      const matchStatus = filterStatus === 'all' || alert.status === filterStatus;
      return matchType && matchStatus;
    });
  }, [filterType, filterStatus]);

  const getLevelColor = (level) => {
    switch(level) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#3b82f6';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedAlert ? '1fr 400px' : '1fr', gap: '32px', transition: 'all 0.3s ease' }}>
      
      {/* ── Main List ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Header & Filters */}
        <div className="surface glass" style={{ padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 className="outfit" style={{ fontSize: '28px', marginBottom: '4px' }}>System Alerts</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Real-time monitoring and anomaly detection ledger.</p>
          </div>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ display: 'flex', background: 'var(--bg-color)', borderRadius: '10px', padding: '4px', border: '1px solid var(--border-color)' }}>
               {['all', 'anomaly', 'threshold', 'system'].map(t => (
                 <button 
                    key={t}
                    onClick={() => setFilterType(t)}
                    style={{ padding: '6px 12px', fontSize: '11px', border: 'none', borderRadius: '7px', cursor: 'pointer', background: filterType === t ? 'var(--accent-color)' : 'transparent', color: filterType === t ? '#000' : 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 'bold' }}
                 >{t}</button>
               ))}
            </div>
            
            <select 
              value={filterStatus} 
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{ background: 'var(--surface-hover)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '0 16px', fontSize: '13px', outline: 'none' }}
            >
               <option value="all">All Status</option>
               <option value="active">Active</option>
               <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>

        {/* Alerts List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {filteredAlerts.length > 0 ? filteredAlerts.map(alert => (
            <div 
              key={alert.id}
              onClick={() => setSelectedAlert(alert)}
              className="surface"
              style={{ 
                padding: '20px 24px', display: 'flex', alignItems: 'center', gap: '20px', 
                cursor: 'pointer', transition: 'all 0.2s', 
                borderLeft: `4px solid ${getLevelColor(alert.level)}`,
                opacity: alert.status === 'resolved' ? 0.6 : 1,
                background: selectedAlert?.id === alert.id ? 'var(--surface-hover)' : 'var(--surface-color)'
              }}
              onMouseOver={e => e.currentTarget.style.transform = 'translateX(4px)'}
              onMouseOut={e => e.currentTarget.style.transform = 'translateX(0)'}
            >
              <div style={{ padding: '10px', borderRadius: '12px', background: 'var(--bg-color)', color: getLevelColor(alert.level) }}>
                 {alert.type === 'anomaly' && <Activity size={20} />}
                 {alert.type === 'threshold' && <AlertTriangle size={20} />}
                 {alert.type === 'system' && <Settings size={20} />}
              </div>
              
              <div style={{ flex: 1 }}>
                 <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '14px', fontWeight: '600' }}>{alert.message}</span>
                    <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'var(--border-color)', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{alert.type}</span>
                 </div>
                 <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Clock size={12} /> {alert.time} • Status: {alert.status}
                 </div>
              </div>

              <ChevronRight size={20} color="var(--text-secondary)" />
            </div>
          )) : (
            <div style={{ padding: '60px', textAlign: 'center', border: '2px dashed var(--border-color)', borderRadius: '20px', color: 'var(--text-secondary)' }}>
               <CheckCircle2 size={40} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
               <p className="outfit" style={{ fontSize: '18px' }}>All clear. No alerts found for these filters.</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Details Panel ── */}
      {selectedAlert && (
        <div className="surface glass" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px', position: 'sticky', top: '32px', height: 'fit-content' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
             <h3 className="outfit" style={{ fontSize: '20px' }}>Alert Details</h3>
             <button onClick={() => setSelectedAlert(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}><X size={22} /></button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ padding: '20px', borderRadius: '16px', background: 'var(--bg-color)', border: '1px solid var(--border-color)' }}>
                 <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>Event Message</label>
                 <div style={{ fontSize: '16px', fontWeight: '600', lineHeight: '1.5' }}>{selectedAlert.message}</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                 <div>
                    <label style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: 'bold' }}>SEVERITY</label>
                    <div style={{ color: getLevelColor(selectedAlert.level), fontWeight: 'bold', textTransform: 'uppercase', fontSize: '13px' }}>{selectedAlert.level}</div>
                 </div>
                 <div>
                    <label style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: 'bold' }}>DETECTED</label>
                    <div style={{ fontSize: '13px' }}>{selectedAlert.time}</div>
                 </div>
              </div>

              <div>
                 <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>Technical Context</label>
                 <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>{selectedAlert.details}</p>
              </div>
          </div>

          <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
             <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                <CheckCircle2 size={18} style={{ marginRight: '8px' }} /> Mark as Resolved
             </button>
             <button className="btn btn-ghost" style={{ width: '100%', border: '1px solid var(--border-color)', justifyContent: 'center' }}>
                <ArrowRight size={18} style={{ marginRight: '8px' }} /> View in Data Explorer
             </button>
          </div>
        </div>
      )}

    </div>
  );
};

export default Alerts;
