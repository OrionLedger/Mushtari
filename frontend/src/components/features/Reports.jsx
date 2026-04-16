import React, { useState } from 'react';
import { 
  FileText, Plus, MoreVertical, Play, Download, 
  ExternalLink, Calendar, Clock, CheckCircle2, 
  AlertCircle, RefreshCw, X, ChevronRight, BarChart3,
  Edit2, Trash2
} from 'lucide-react';

const MOCK_REPORTS = [
  { id: 1, name: 'Monthly Financial Audit', schedule: 'Monthly', lastRun: '2 days ago', status: 'ready', metric: 'Total Revenue' },
  { id: 2, name: 'Weekly Inventory Health', schedule: 'Weekly', lastRun: '5h ago', status: 'ready', metric: 'Safety Stock' },
  { id: 3, name: 'Daily Sales Velocity', schedule: 'Daily', lastRun: 'Just now', status: 'processing', metric: 'Orders' },
  { id: 4, name: 'Quarterly Forecast Accuracy', schedule: 'Quarterly', lastRun: '1 week ago', status: 'ready', metric: 'Error Margin' },
  { id: 5, name: 'Supplier Lead Time Audit', schedule: 'Manual', lastRun: 'Never', status: 'error', metric: 'Lead Days' },
];

const Reports = () => {
  const [reports, setReports] = useState(MOCK_REPORTS);
  const [selectedReport, setSelectedReport] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState(null);
  const [formData, setFormData] = useState({ name: '', schedule: 'Weekly', metric: 'Total Revenue' });

  const handleCreateOrUpdate = (e) => {
    e.preventDefault();
    if (isEditing) {
      setReports(reports.map(r => r.id === activeMenuId ? { ...r, ...formData } : r));
    } else {
      const br = {
        ...formData,
        id: Date.now(),
        lastRun: 'Never',
        status: 'ready'
      };
      setReports([br, ...reports]);
    }
    closeModal();
  };

  const openModal = (report = null) => {
    if (report) {
      setFormData({ name: report.name, schedule: report.schedule, metric: report.metric });
      setIsEditing(true);
      setActiveMenuId(report.id);
    } else {
      setFormData({ name: '', schedule: 'Weekly', metric: 'Total Revenue' });
      setIsEditing(false);
    }
    setShowModal(true);
    setActiveMenuId(null);
  };

  const closeModal = () => {
    setShowModal(false);
    setIsEditing(false);
    setActiveMenuId(null);
  };

  const handleDelete = (id) => {
    setReports(reports.filter(r => r.id !== id));
    if (selectedReport?.id === id) setSelectedReport(null);
    setActiveMenuId(null);
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'ready': return <CheckCircle2 size={16} color="#10b981" />;
      case 'processing': return <RefreshCw size={16} color="#3b82f6" className="spin" />;
      case 'error': return <AlertCircle size={16} color="#ef4444" />;
      default: return null;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* ── Header ── */}
      <div className="surface glass" style={{ padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
           <nav style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.1em', marginBottom: '8px' }}>Analytics / Documentation</nav>
           <h2 className="outfit" style={{ fontSize: '28px', marginBottom: '4px' }}>Reporting Engine</h2>
           <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Automated document generation and distribution logs.</p>
        </div>
        <button className="btn btn-primary" onClick={() => openModal()} style={{ display: 'flex', gap: '8px' }}>
           <Plus size={18} /> New Schedule
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selectedReport ? '1.5fr 1fr' : '1fr', gap: '24px', transition: 'all 0.3s' }}>
        
        {/* ── List Area ── */}
        <div className="surface" style={{ padding: '0', overflow: 'hidden' }}>
           <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                 <tr style={{ background: 'var(--surface-hover)', borderBottom: '1px solid var(--border-color)' }}>
                    <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Report Name</th>
                    <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Schedule</th>
                    <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Last Run</th>
                    <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Status</th>
                    <th style={{ padding: '16px 24px' }}></th>
                 </tr>
              </thead>
              <tbody>
                 {reports.map((report) => (
                   <tr key={report.id} onClick={() => setSelectedReport(report)} style={{ borderBottom: '1px solid var(--border-color)', cursor: 'pointer', background: selectedReport?.id === report.id ? 'var(--surface-hover)' : 'transparent' }}>
                      <td style={{ padding: '20px 24px' }}>
                         <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div style={{ padding: '8px', borderRadius: '10px', background: 'var(--bg-color)', color: 'var(--accent-color)' }}><FileText size={20} /></div>
                            <span style={{ fontWeight: '600', fontSize: '15px' }}>{report.name}</span>
                         </div>
                      </td>
                      <td style={{ padding: '20px 24px', fontSize: '14px' }}>{report.schedule}</td>
                      <td style={{ padding: '20px 24px', fontSize: '14px', color: 'var(--text-secondary)' }}>{report.lastRun}</td>
                      <td style={{ padding: '20px 24px' }}>
                         <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
                            {getStatusIcon(report.status)}
                            <span style={{ textTransform: 'capitalize' }}>{report.status}</span>
                         </div>
                      </td>
                      <td style={{ padding: '20px 24px', textAlign: 'right', position: 'relative' }}>
                         <button 
                            className="btn btn-ghost" 
                            style={{ padding: '8px' }}
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveMenuId(activeMenuId === report.id ? null : report.id);
                            }}
                         >
                            <MoreVertical size={18} />
                         </button>

                         {activeMenuId === report.id && (
                           <div style={{ position: 'absolute', top: '100%', right: '24px', zIndex: 10, minWidth: '120px', background: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.5)', overflow: 'hidden' }}>
                              <button 
                                 onClick={(e) => { e.stopPropagation(); openModal(report); }}
                                 style={{ width: '100%', padding: '12px 16px', border: 'none', background: 'transparent', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', textAlign: 'left', fontSize: '13px' }}
                                 onMouseEnter={(e) => e.currentTarget.style.background = 'var(--surface-hover)'}
                                 onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                              >
                                 <Edit2 size={14} color="var(--accent-color)" /> Edit
                              </button>
                              <button 
                                 onClick={(e) => { e.stopPropagation(); handleDelete(report.id); }}
                                 style={{ width: '100%', padding: '12px 16px', border: 'none', background: 'transparent', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', textAlign: 'left', fontSize: '13px' }}
                                 onMouseEnter={(e) => e.currentTarget.style.background = 'var(--surface-hover)'}
                                 onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                              >
                                 <Trash2 size={14} /> Delete
                              </button>
                           </div>
                         )}
                      </td>
                   </tr>
                 ))}
              </tbody>
           </table>
        </div>

        {/* ── Detail Panel ── */}
        {selectedReport && (
          <div className="surface glass" style={{ padding: '32px', height: 'fit-content', position: 'sticky', top: '32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 className="outfit" style={{ fontSize: '20px' }}>Report Profile</h3>
                <button onClick={() => setSelectedReport(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}><X size={22} /></button>
             </div>

             <div style={{ padding: '24px', borderRadius: '16px', background: 'var(--bg-color)', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontSize: '18px', marginBottom: '16px' }}>{selectedReport.name}</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                   <div>
                      <label style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: 'bold' }}>PRIMARY METRIC</label>
                      <div style={{ fontSize: '14px', fontWeight: '600' }}>{selectedReport.metric}</div>
                   </div>
                   <div>
                      <label style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: 'bold' }}>SCHEDULE</label>
                      <div style={{ fontSize: '14px' }}>{selectedReport.schedule}</div>
                   </div>
                </div>
             </div>

             <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                  <Play size={18} style={{ marginRight: '8px' }} /> Run Report Now
                </button>
                <div style={{ display: 'flex', gap: '12px' }}>
                   <button className="btn btn-ghost" style={{ flex: 1, border: '1px solid var(--border-color)', justifyContent: 'center' }}>
                      <Download size={18} style={{ marginRight: '8px' }} /> PDF
                   </button>
                   <button className="btn btn-ghost" style={{ flex: 1, border: '1px solid var(--border-color)', justifyContent: 'center' }}>
                      <Download size={18} style={{ marginRight: '8px' }} /> CSV
                   </button>
                </div>
             </div>
          </div>
        )}
      </div>

      {/* ── Unified Form Modal (Create & Edit) ── */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <form onSubmit={handleCreateOrUpdate} className="surface" style={{ width: '450px', padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
             <h2 className="outfit" style={{ fontSize: '24px' }}>{isEditing ? 'Edit Report Schedule' : 'New Analytics Report'}</h2>
             <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                   <label style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>Report Title</label>
                   <input required style={{ background: 'var(--bg-color)', border: '1px solid var(--border-color)', padding: '12px', borderRadius: '10px', color: 'var(--text-primary)' }} placeholder="e.g. Q4 Executive Summary" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                   <label style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>Target Metric</label>
                   <select style={{ background: 'var(--bg-color)', border: '1px solid var(--border-color)', padding: '12px', borderRadius: '10px', color: 'var(--text-primary)' }} value={formData.metric} onChange={e => setFormData({...formData, metric: e.target.value})}>
                      <option>Total Revenue</option>
                      <option>Inventory ROI</option>
                      <option>CAC / LTV</option>
                      <option>Lead Time Efficiency</option>
                   </select>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                   <label style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>Frequency</label>
                   <select style={{ background: 'var(--bg-color)', border: '1px solid var(--border-color)', padding: '12px', borderRadius: '10px', color: 'var(--text-primary)' }} value={formData.schedule} onChange={e => setFormData({...formData, schedule: e.target.value})}>
                      <option>Daily</option>
                      <option>Weekly</option>
                      <option>Monthly</option>
                      <option>Quarterly</option>
                      <option>Manual Only</option>
                   </select>
                </div>
             </div>
             <div style={{ display: 'flex', gap: '12px' }}>
                <button type="button" onClick={closeModal} className="btn btn-ghost" style={{ flex: 1, border: '1px solid var(--border-color)' }}>Cancel</button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>{isEditing ? 'Save Changes' : 'Create Schedule'}</button>
             </div>
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

export default Reports;
