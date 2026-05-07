import React, { useState, useEffect, useCallback } from 'react';
import { 
  Database, Plus, Trash2, RefreshCw, CheckCircle2, 
  AlertCircle, Link2, Server, HardDrive, X, ShieldCheck,
  Play, Wifi, WifiOff, Clock
} from 'lucide-react';
import dataService from '../../services/dataService';

const TYPE_ICONS = {
  Database: <Server size={22} color="var(--accent-color)" />,
  Storage:  <HardDrive size={22} color="#a855f7" />,
  Stream:   <RefreshCw size={22} color="#3b82f6" />,
  File:     <Database size={22} color="#f59e0b" />,
};

const STATUS_STYLE = {
  active:  { color: '#10b981', bg: '#10b98115', label: 'Active',   Icon: CheckCircle2 },
  syncing: { color: '#3b82f6', bg: '#3b82f615', label: 'Syncing',  Icon: RefreshCw    },
  error:   { color: '#ef4444', bg: '#ef444415', label: 'Error',    Icon: AlertCircle  },
  default: { color: 'var(--text-secondary)', bg: 'var(--surface-hover)', label: 'Unknown', Icon: Clock },
};

const statusStyle = (s) => STATUS_STYLE[s] ?? STATUS_STYLE.default;

const EMPTY_FORM = { name: '', source_type: 'Database', conn_uri: '' };

const Sources = () => {
  const [sources,     setSources]     = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [showModal,   setShowModal]   = useState(false);
  const [form,        setForm]        = useState(EMPTY_FORM);
  const [testStatus,  setTestStatus]  = useState(null);
  const [saving,      setSaving]      = useState(false);
  const [syncingId,   setSyncingId]   = useState(null);
  const [error,       setError]       = useState(null);

  // Mapping states
  const [showMappingModal, setShowMappingModal] = useState(false);
  const [mapSource,       setMapSource]       = useState(null);
  const [targetTable,     setTargetTable]     = useState('Sales');
  const [sourceTables,    setSourceTables]    = useState([]);
  const [discoveredCols,  setDiscoveredCols]  = useState([]);
  const [mapping,         setMapping]         = useState({});
  const [inspecting,      setInspecting]      = useState(false);
  
  const [itemsSourceType, setItemsSourceType] = useState('json_column');
  const [itemsTableName,  setItemsTableName]  = useState('');
  const [syncInterval,    setSyncInterval]    = useState(6);

  // ── Load ──────────────────────────────────────────────────────────────────
  const loadSources = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dataService.getSources();
      setSources(data ?? []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSources(); }, [loadSources]);

  // ── Mapping Logic ──────────────────────────────────────────────────────────
  const openMapping = async (source) => {
    setMapSource(source);
    setTargetTable(source.source_table || '');
    setMapping(source.column_mapping || {});
    setItemsSourceType(source.items_source_type || 'json_column');
    setItemsTableName(source.items_table_name || '');
    setSyncInterval(source.sync_interval_hours || 6);
    setDiscoveredCols([]);
    setSourceTables([]);
    setShowMappingModal(true);
    
    // Auto-load tables
    try {
      const tables = await dataService.getSourceTables(source.id);
      setSourceTables(tables);
      if (source.source_table) {
        handleInspect(source.id, source.source_table);
      }
    } catch (err) {
      console.error("Failed to load tables", err);
    }
  };

  const handleInspect = async (id, tableName) => {
    const sid = id || mapSource?.id;
    const tname = tableName || targetTable;
    if (!tname || !sid) return;
    
    setInspecting(true);
    setTestStatus(null);
    try {
      const cols = await dataService.getSourceSchema(sid, tname);
      setDiscoveredCols(cols);
    } catch (err) {
      setTestStatus({ ok: false, message: `Failed to inspect table: ${err.message}` });
    } finally {
      setInspecting(false);
    }
  };

  const saveMapping = async () => {
    setSaving(true);
    try {
      await dataService.updateSourceMapping(
        mapSource.id, 
        targetTable, 
        mapping, 
        itemsSourceType, 
        itemsTableName, 
        syncInterval
      );
      setShowMappingModal(false);
      loadSources();
    } catch (err) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  // ── Test connection ────────────────────────────────────────────────────────
  const handleTest = async () => {
    const uri = form.conn_uri.trim();
    if (!uri) return;
    setTestStatus('testing');
    try {
      const result = await dataService.testConnection(uri);
      setTestStatus(result);
    } catch {
      setTestStatus({ ok: false, message: 'Network error — is the backend running?' });
    }
  };

  // ── Save new source ────────────────────────────────────────────────────────
  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await dataService.addSource({
        name:        form.name,
        source_type: form.source_type,
        conn_uri:    form.conn_uri.trim(),
      });
      loadSources();
      setShowModal(false);
      setForm(EMPTY_FORM);
      setTestStatus(null);
    } catch (err) {
      setTestStatus({ ok: false, message: err.message });
    } finally {
      setSaving(false);
    }
  };

  // ── Delete ────────────────────────────────────────────────────────────────
  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this source?")) return;
    try {
      await dataService.deleteSource(id);
      setSources(prev => prev.filter(s => s.id !== id));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  // ── Sync ──────────────────────────────────────────────────────────────────
  const handleSync = async (id) => {
    setSyncingId(id);
    setSources(prev => prev.map(s => s.id === id ? { ...s, status: 'syncing' } : s));
    try {
      const res = await dataService.syncSource(id);
      if (res.ok) {
        setTimeout(() => loadSources(), 2000);
      } else {
        alert(`Sync failed: ${res.message}`);
        loadSources();
      }
    } catch (err) {
      alert(`Sync failed: ${err.message}`);
      loadSources();
    } finally {
      setSyncingId(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>

      {/* Header */}
      <div className="surface glass" style={{ padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <nav style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.1em', marginBottom: '8px' }}>
            Infrastructure / Connections
          </nav>
          <h1 className="outfit" style={{ fontSize: '28px', marginBottom: '4px' }}>Data Sources</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Connect and orchestrate your raw data ingestion pipelines.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-ghost" onClick={loadSources} style={{ border: '1px solid var(--border-color)', display: 'flex', gap: '8px', alignItems: 'center' }}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => { setShowModal(true); setTestStatus(null); }} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Plus size={18} /> Add New Source
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '16px', borderRadius: '12px', background: '#ef444415', border: '1px solid #ef444430', color: '#ef4444', fontSize: '14px' }}>
          <strong>Backend Error:</strong> {error}
        </div>
      )}

      {loading && (
        <div style={{ padding: '80px', textAlign: 'center' }}>
          <RefreshCw size={40} className="spin" style={{ margin: '0 auto 16px', color: 'var(--accent-color)' }} />
          <p className="outfit">Loading secure data connections...</p>
        </div>
      )}

      {!loading && sources.length === 0 && !error && (
        <div className="surface" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          <Database size={48} style={{ opacity: 0.15, marginBottom: '16px' }} />
          <p style={{ marginBottom: '8px', fontSize: '16px', fontWeight: '600' }}>No data sources connected yet.</p>
          <p style={{ fontSize: '13px' }}>Click "Add New Source" and paste your connection URI to get started.</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(420px, 1fr))', gap: '24px' }}>
        {sources.map(source => {
          const st = statusStyle(source.status);
          const isSourceSyncing = syncingId === source.id || source.status === 'syncing';
          return (
            <div key={source.id} className="surface"
              style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px',
                border: source.status === 'error' ? '1px solid #ef444430' : '1px solid var(--border-color)',
                transition: 'transform 0.2s, box-shadow 0.2s' }}>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'var(--bg-color)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border-color)', flexShrink: 0 }}>
                    {TYPE_ICONS[source.type] ?? TYPE_ICONS.Database}
                  </div>
                  <div>
                    <h3 className="outfit" style={{ fontSize: '17px', marginBottom: '4px' }}>{source.name}</h3>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', fontSize: '12px', color: 'var(--text-secondary)' }}>
                      <Link2 size={12} /> {source.type} &bull; <Clock size={12} /> {source.last_sync}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 12px',
                  borderRadius: '20px', background: st.bg, color: st.color,
                  fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', flexShrink: 0 }}>
                  <st.Icon size={13} className={isSourceSyncing ? 'spin' : ''} />
                  {st.label}
                </div>
              </div>

              <div style={{ background: 'var(--bg-color)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
                <code style={{ fontSize: '11px', color: 'var(--text-secondary)', wordBreak: 'break-all', lineHeight: 1.6 }}>
                  {source.uri}
                </code>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Link2 size={14} color={source.source_table ? 'var(--accent-color)' : '#666'} />
                {source.source_table ? `Mapped to ${source.source_table}` : 'No table mapped yet'}
              </div>

              <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: 'auto' }}>
                <button
                  className="btn btn-primary"
                  onClick={() => handleSync(source.id)}
                  disabled={isSourceSyncing || !source.source_table}
                  style={{ flex: 2, fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', opacity: (isSourceSyncing || !source.source_table) ? 0.6 : 1 }}>
                  <Play size={14} />
                  {isSourceSyncing ? 'Syncing...' : 'Sync Now'}
                </button>
                <button
                  className="btn btn-ghost"
                  onClick={() => openMapping(source)}
                  style={{ flex: 1, border: '1px solid var(--border-color)', fontSize: '12px' }}>
                  Config
                </button>
                <button onClick={() => handleDelete(source.id)} className="btn btn-ghost"
                  style={{ color: '#ef4444', padding: '8px' }}>
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <form onSubmit={handleSave} className="surface"
            style={{ width: '500px', padding: '36px', display: 'flex', flexDirection: 'column', gap: '24px',
              boxShadow: '0 25px 60px rgba(0,0,0,0.4)' }}>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 className="outfit" style={{ fontSize: '22px' }}>New Data Connection</h2>
              <button type="button" onClick={() => { setShowModal(false); setTestStatus(null); }}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                <X size={24} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={labelStyle}>Source Name</label>
                <input required style={inputStyle} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="ERP Database" />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={labelStyle}>Connection Type</label>
                <select style={inputStyle} value={form.source_type} onChange={e => setForm({ ...form, source_type: e.target.value })}>
                  <option>Database</option>
                  <option>Storage</option>
                  <option>Stream</option>
                  <option>File</option>
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={labelStyle}>Connection URI</label>
                <textarea required style={{ ...inputStyle, minHeight: '80px', fontFamily: 'monospace' }} value={form.conn_uri}
                  onChange={e => { setForm({ ...form, conn_uri: e.target.value }); setTestStatus(null); }}
                  placeholder="postgresql://user:pass@host:5432/db" />
              </div>
            </div>

            {testStatus && (
              <div style={{ padding: '12px', borderRadius: '8px', background: testStatus.ok ? '#10b98115' : '#ef444415', border: `1px solid ${testStatus.ok ? '#10b98130' : '#ef444430'}`, color: testStatus.ok ? '#10b981' : '#ef4444', fontSize: '13px' }}>
                {testStatus.message}
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button type="button" onClick={handleTest} className="btn btn-ghost" disabled={testStatus === 'testing' || !form.conn_uri.trim()} style={{ flex: 1, border: '1px solid var(--border-color)' }}>
                {testStatus === 'testing' ? 'Testing...' : 'Test Connection'}
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving} style={{ flex: 1 }}>
                Deploy Source
              </button>
            </div>
          </form>
        </div>
      )}

      {showMappingModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 110 }}>
          <div className="surface" style={{ width: '700px', maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            
            <div style={{ padding: '32px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 className="outfit" style={{ fontSize: '24px', marginBottom: '4px' }}>Configure Mapping</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{mapSource?.name} &bull; {mapSource?.uri}</p>
              </div>
              <button onClick={() => setShowMappingModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                <X size={28} />
              </button>
            </div>

            <div style={{ padding: '32px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '32px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <label style={labelStyle}>1. Source Table Name</label>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <select 
                    style={{ ...inputStyle, flex: 1 }} 
                    value={targetTable} 
                    onChange={e => {
                      setTargetTable(e.target.value);
                      handleInspect(null, e.target.value);
                    }}
                  >
                    <option value="">-- Select a Table --</option>
                    {sourceTables.map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                  <button className="btn btn-ghost" onClick={() => handleInspect()} disabled={inspecting || !targetTable} style={{ border: '1px solid var(--border-color)', minWidth: '140px' }}>
                    {inspecting ? 'Inspecting...' : 'Refresh Columns'}
                  </button>
                </div>
              </div>

              {discoveredCols.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <label style={labelStyle}>2. Order Attributes</label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {[
                        { id: 'order_id',    label: 'Order ID',   req: true },
                        { id: 'order_date',  label: 'Order Date', req: true },
                        { id: 'status',      label: 'Status',     req: false },
                        { id: 'customer_id', label: 'Customer ID',req: false },
                      ].map(field => (
                        <div key={field.id} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', alignItems: 'center', gap: '24px', padding: '12px', background: 'var(--surface-hover)', borderRadius: '12px' }}>
                          <div style={{ fontSize: '14px', fontWeight: '600' }}>
                            {field.label} {field.req && <span style={{ color: '#ef4444' }}>*</span>}
                          </div>
                          <select 
                            style={inputStyle} 
                            value={mapping[field.id] || ''}
                            onChange={e => setMapping({ ...mapping, [field.id]: e.target.value })}
                          >
                            <option value="">-- Ignore --</option>
                            {discoveredCols.map(c => (
                              <option key={c.name} value={c.name}>{c.name} ({c.type})</option>
                            ))}
                          </select>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <label style={labelStyle}>3. Items Configuration</label>
                    <div style={{ display: 'flex', gap: '24px', marginBottom: '8px' }}>
                       <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input type="radio" checked={itemsSourceType === 'json_column'} onChange={() => setItemsSourceType('json_column')} />
                          <span style={{ fontSize: '14px' }}>JSON Column</span>
                       </label>
                       <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input type="radio" checked={itemsSourceType === 'separate_table'} onChange={() => setItemsSourceType('separate_table')} />
                          <span style={{ fontSize: '14px' }}>Separate Table</span>
                       </label>
                    </div>

                    {itemsSourceType === 'json_column' && (
                       <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', alignItems: 'center', gap: '24px', padding: '12px', background: 'var(--surface-hover)', borderRadius: '12px' }}>
                          <div style={{ fontSize: '14px', fontWeight: '600' }}>Items JSON Field <span style={{ color: '#ef4444' }}>*</span></div>
                          <select style={inputStyle} value={mapping['items_column'] || ''} onChange={e => setMapping({ ...mapping, items_column: e.target.value })}>
                            <option value="">-- Select --</option>
                            {discoveredCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                          </select>
                       </div>
                    )}

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
                      {[
                        { id: 'product_id',  label: 'Product ID', req: true },
                        { id: 'quantity',    label: 'Quantity',   req: true },
                        { id: 'unit_price',  label: 'Unit Price', req: true },
                        { id: 'discount',    label: 'Discount',   req: false },
                      ].map(field => (
                        <div key={field.id} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', alignItems: 'center', gap: '24px', padding: '12px', background: 'var(--surface-hover)', borderRadius: '12px' }}>
                          <div style={{ fontSize: '14px', fontWeight: '600' }}>{field.label} {field.req && <span style={{ color: '#ef4444' }}>*</span>}</div>
                          {itemsSourceType === 'json_column' ? (
                             <input style={inputStyle} placeholder="JSON Key (e.g. sku_id)" value={mapping[field.id] || ''} onChange={e => setMapping({ ...mapping, [field.id]: e.target.value })} />
                          ) : (
                             <select style={inputStyle} value={mapping[field.id] || ''} onChange={e => setMapping({ ...mapping, [field.id]: e.target.value })}>
                                <option value="">-- Select --</option>
                                {discoveredCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                             </select>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <label style={labelStyle}>4. Sync Interval</label>
                    <select style={inputStyle} value={syncInterval} onChange={e => setSyncInterval(parseInt(e.target.value))}>
                      <option value={1}>Every 1 Hour</option>
                      <option value={6}>Every 6 Hours</option>
                      <option value={12}>Every 12 Hours</option>
                      <option value={24}>Every 24 Hours</option>
                      <option value={0}>Manual Only</option>
                    </select>
                  </div>

                </div>
              )}

              {testStatus && !inspecting && (
                <div style={{ padding: '12px', borderRadius: '8px', background: '#ef444415', border: '1px solid #ef444430', color: '#ef4444', fontSize: '13px' }}>
                  {testStatus.message}
                </div>
              )}
            </div>

            <div style={{ padding: '24px 32px', background: 'var(--bg-color)', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button className="btn btn-ghost" onClick={() => setShowMappingModal(false)}>Cancel</button>
              <button className="btn btn-primary" disabled={saving || !targetTable || (discoveredCols.length === 0)} onClick={saveMapping} style={{ minWidth: '160px' }}>
                Save Mapping
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

const labelStyle = { fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' };
const inputStyle = {
  background:   'var(--bg-color)',
  border:       '1px solid var(--border-color)',
  padding:      '12px 14px',
  borderRadius: '10px',
  color:        'var(--text-primary)',
  fontSize:     '14px',
  width:        '100%',
  boxSizing:    'border-box',
  outline:      'none',
};

export default Sources;
