import React, { useState } from 'react';
import { 
  Database, Plus, Trash2, RefreshCw, CheckCircle2, 
  AlertCircle, Link2, Server, HardDrive, X, ShieldCheck,
  ExternalLink, Play
} from 'lucide-react';

const MOCK_SOURCES = [
  { id: 1, name: 'Main PostgreSQL', type: 'Database', status: 'active', lastSync: '12m ago', conn: 'postgresql://prod-db:5432/warehouse' },
  { id: 2, name: 'AWS S3 Logs', type: 'Storage', status: 'syncing', lastSync: 'Now', conn: 's3://orion-ledger-backups/ingress/' },
  { id: 3, name: 'Kafka Sales Stream', type: 'Stream', status: 'error', lastSync: '4h ago', conn: 'kafka://broker:9092/topics/orders' },
  { id: 4, name: 'Local CSV Dump', type: 'File', status: 'active', lastSync: '1d ago', conn: '/mnt/storage/csv/raw_demand.csv' },
];

const Sources = () => {
  const [sources, setSources] = useState(MOCK_SOURCES);
  const [showAddForm, setShowAddForm] = useState(false);
  const [testStatus, setTestStatus] = useState(null); // 'testing', 'success', 'fail'
  const [newSource, setNewSource] = useState({ name: '', type: 'Database', conn: '' });

  const getStatusStyle = (status) => {
    switch(status) {
      case 'active': return { color: '#10b981', bg: '#10b98115', icon: <CheckCircle2 size={14} /> };
      case 'syncing': return { color: '#3b82f6', bg: '#3b82f615', icon: <RefreshCw size={14} className="spin" /> };
      case 'error': return { color: '#ef4444', bg: '#ef444415', icon: <AlertCircle size={14} /> };
      default: return { color: 'var(--text-secondary)', bg: 'var(--surface-hover)', icon: null };
    }
  };

  const handleAddSource = (e) => {
    e.preventDefault();
    const source = {
      ...newSource,
      id: Date.now(),
      status: 'active',
      lastSync: 'Just now'
    };
    setSources([...sources, source]);
    setShowAddForm(false);
    setNewSource({ name: '', type: 'Database', conn: '' });
  };

  const handleDelete = (id) => {
    setSources(sources.filter(s => s.id !== id));
  };

  const testConnection = () => {
    setTestStatus('testing');
    setTimeout(() => {
      setTestStatus(Math.random() > 0.2 ? 'success' : 'fail');
    }, 1500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* ── Header ── */}
      <div className="surface glass" style={{ padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <nav style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.1em', marginBottom: '8px' }}>Infrastructure / Connections</nav>
          <h1 className="outfit" style={{ fontSize: '28px', marginBottom: '4px' }}>Data Sources</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Connect and orchestrate your raw data ingestion pipelines.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAddForm(true)} style={{ display: 'flex', gap: '8px' }}>
          <Plus size={18} /> Add New Source
        </button>
      </div>

      {/* ── Sources List ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '24px' }}>
        {sources.map(source => {
          const style = getStatusStyle(source.status);
          return (
            <div key={source.id} className="surface" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', transition: 'transform 0.2s', border: source.status === 'error' ? '1px solid #ef444430' : '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'var(--bg-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border-color)' }}>
                    {source.type === 'Database' && <Server size={22} color="var(--accent-color)" />}
                    {source.type === 'Storage' && <HardDrive size={22} color="#a855f7" />}
                    {source.type === 'Stream' && <RefreshCw size={22} color="#3b82f6" />}
                    {source.type === 'File' && <Database size={22} color="#f59e0b" />}
                  </div>
                  <div>
                    <h3 className="outfit" style={{ fontSize: '18px', marginBottom: '4px' }}>{source.name}</h3>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', fontSize: '12px', color: 'var(--text-secondary)' }}>
                       <Link2 size={12} /> {source.type} • Last synced {source.lastSync}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 10px', borderRadius: '20px', background: style.bg, color: style.color, fontSize: '11px', fontWeight: 'bold', textTransform: 'uppercase' }}>
                  {style.icon} {source.status}
                </div>
              </div>

              <div style={{ background: 'var(--bg-color)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', position: 'relative' }}>
                 <code style={{ fontSize: '12px', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{source.conn}</code>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                 <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: '12px', border: '1px solid var(--border-color)' }}>Configure</button>
                    <button className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: '12px', border: '1px solid var(--border-color)' }}>
                      <Play size={14} style={{ marginRight: '6px' }} /> Sync Now
                    </button>
                 </div>
                 <button onClick={() => handleDelete(source.id)} className="btn btn-ghost" style={{ color: '#ef4444', padding: '8px' }}>
                    <Trash2 size={18} />
                 </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Add Source Modal ── */}
      {showAddForm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <form onSubmit={handleAddSource} className="surface" style={{ width: '480px', padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
               <h2 className="outfit" style={{ fontSize: '22px' }}>New Data Connection</h2>
               <button type="button" onClick={() => setShowAddForm(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}><X size={24} /></button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>Source Name</label>
                <input required style={{ background: 'var(--bg-color)', border: '1px solid var(--border-color)', padding: '12px', borderRadius: '10px', color: 'var(--text-primary)' }} value={newSource.name} onChange={e => setNewSource({...newSource, name: e.target.value})} placeholder="e.g. Prod Database" />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>Connection Type</label>
                <select style={{ background: 'var(--bg-color)', border: '1px solid var(--border-color)', padding: '12px', borderRadius: '10px', color: 'var(--text-primary)' }} value={newSource.type} onChange={e => setNewSource({...newSource, type: e.target.value})}>
                  <option>Database</option>
                  <option>Storage</option>
                  <option>Stream</option>
                  <option>File</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>Connection String / URI</label>
                <textarea required style={{ background: 'var(--bg-color)', border: '1px solid var(--border-color)', padding: '12px', borderRadius: '10px', color: 'var(--text-primary)', minHeight: '80px', fontFamily: 'monospace', fontSize: '12px' }} value={newSource.conn} onChange={e => setNewSource({...newSource, conn: e.target.value})} placeholder="postgresql://user:pass@host:5432/db" />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
               <button type="button" onClick={testConnection} className="btn btn-ghost" style={{ flex: 1, border: '1px solid var(--border-color)', display: 'flex', justifyContent: 'center', gap: '10px' }}>
                  {testStatus === 'testing' ? <RefreshCw size={18} className="spin" /> : <><ShieldCheck size={18} /> Test Connection</>}
               </button>
               <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Deploy Source</button>
            </div>

            {testStatus === 'success' && (
              <div style={{ padding: '12px', borderRadius: '8px', background: '#10b98115', color: '#10b981', fontSize: '13px', textAlign: 'center' }}>
                Connection valid. Ready to ingress data.
              </div>
            )}
            {testStatus === 'fail' && (
              <div style={{ padding: '12px', borderRadius: '8px', background: '#ef444415', color: '#ef4444', fontSize: '13px', textAlign: 'center' }}>
                Connection failed. Please check your credentials.
              </div>
            )}
          </form>
        </div>
      )}

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default Sources;
