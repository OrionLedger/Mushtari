import React, { useState, useRef, useCallback } from 'react';
import { Upload, FileSpreadsheet, CheckCircle, XCircle, AlertTriangle, Download, Loader2, Database } from 'lucide-react';
import dataService from '../../services/dataService';
import { useI18n } from '../../i18n';

const IMPORT_TYPES = [
  {
    id: 'products',
    labelKey: 'import.type_products',
    icon: <Database size={20} />,
    descriptionKey: 'import.desc_products',
    importFn: (file, onProgress) => dataService.importProducts(file, onProgress),
    templateType: 'products',
    accept: '.xlsx,.xls',
  },
  {
    id: 'orders',
    labelKey: 'import.type_orders',
    icon: <FileSpreadsheet size={20} />,
    descriptionKey: 'import.desc_orders',
    importFn: (file, onProgress) => dataService.importOrders(file, onProgress),
    templateType: 'orders',
    accept: '.xlsx,.xls',
  },
];

const DataImport = () => {
  const { t } = useI18n();
  const fileInputRef = useRef(null);
  const [importType, setImportType] = useState('products');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const currentType = IMPORT_TYPES.find((t) => t.id === importType) || IMPORT_TYPES[0];

  const handleFileDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) validateAndSetFile(droppedFile);
  }, []);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (file) => {
    setError(null);
    setResult(null);

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['xlsx', 'xls'].includes(ext)) {
      setError(t('import.error_format'));
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError(t('import.error_size'));
      return;
    }
    setFile(file);
  };

  const handleImport = async () => {
    if (!file) return;
    setUploading(true);
    setUploadProgress(0);
    setError(null);
    setResult(null);

    try {
      const res = await currentType.importFn(file, (progressEvent) => {
        if (progressEvent.total) {
          setUploadProgress(Math.round((progressEvent.loaded / progressEvent.total) * 100));
        }
      });
      setResult(res);
    } catch (err) {
      setError(err.message || t('import.error_generic'));
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setUploadProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDownloadTemplate = () => {
    const url = dataService.getTemplateDownloadUrl(currentType.templateType);
    window.open(url, '_blank');
  };

  return (
    <div>
      <div className="surface" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h2 className="outfit" style={{ fontSize: '22px', marginBottom: '8px' }}>
          {t('import.title')}
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
          {t('import.subtitle')}
        </p>

        {/* Import Type Selector */}
        <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
          {IMPORT_TYPES.map((type) => (
            <button
              key={type.id}
              className={`btn ${importType === type.id ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => { setImportType(type.id); handleReset(); }}
              style={{ flex: 1, justifyContent: 'center', padding: '14px 20px' }}
            >
              {type.icon}
              <span>{t(type.labelKey)}</span>
            </button>
          ))}
        </div>

        {/* Type Description */}
        <div style={{
          padding: '12px 16px',
          borderRadius: '12px',
          backgroundColor: 'var(--surface-hover)',
          marginBottom: '24px',
          fontSize: '13px',
          color: 'var(--text-secondary)',
        }}>
          {t(currentType.descriptionKey)}
        </div>

        {/* Drop Zone */}
        {!file && !uploading && (
          <div
            className={`surface`}
            style={{
              border: `2px dashed ${dragOver ? 'var(--accent-color)' : 'var(--border-color)'}`,
              borderRadius: '16px',
              padding: '48px 24px',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              backgroundColor: dragOver ? 'var(--surface-hover)' : 'var(--surface-color)',
            }}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={40} color="var(--accent-color)" style={{ marginBottom: '16px' }} />
            <p style={{ fontWeight: '500', marginBottom: '8px' }}>
              {t('import.drop_zone')}
            </p>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              {t('import.drop_hint')}
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept={currentType.accept}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>
        )}

        {/* Selected File */}
        {file && !uploading && !result && (
          <div style={{
            padding: '20px',
            borderRadius: '12px',
            backgroundColor: 'var(--surface-hover)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FileSpreadsheet size={24} color="var(--accent-color)" />
              <div>
                <p style={{ fontWeight: '500' }}>{file.name}</p>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn-ghost" onClick={handleReset}>
                {t('import.cancel')}
              </button>
              <button className="btn btn-primary" onClick={handleImport}>
                <Upload size={16} />
                {t('import.start')}
              </button>
            </div>
          </div>
        )}

        {/* Upload Progress */}
        {uploading && (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <Loader2 size={20} className="spin" color="var(--accent-color)" />
              <span style={{ fontSize: '14px' }}>{t('import.uploading')} ({uploadProgress}%)</span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              borderRadius: '4px',
              backgroundColor: 'var(--border-color)',
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${uploadProgress}%`,
                height: '100%',
                backgroundColor: 'var(--accent-color)',
                borderRadius: '4px',
                transition: 'width 0.3s ease',
              }} />
            </div>
          </div>
        )}

        {/* Result Summary */}
        {result && (
          <div className="surface" style={{
            border: `1px solid ${result.rows_failed > 0 ? 'var(--alert-color, #ef4444)' : 'var(--accent-color)'}`,
            marginBottom: '16px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              {result.rows_failed > 0 ? (
                <AlertTriangle size={24} color="#f59e0b" />
              ) : (
                <CheckCircle size={24} color="var(--accent-color)" />
              )}
              <div>
                <p style={{ fontWeight: '600', fontSize: '16px' }}>
                  {result.status === 'completed' ? t('import.result_success') : t('import.result_partial')}
                </p>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  {t('import.result_duration', { ms: result.duration_ms })}
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '12px', marginBottom: '16px' }}>
              <StatBox label={t('import.stat_total')} value={result.total_rows} color="var(--text-primary)" />
              <StatBox label={t('import.stat_imported')} value={result.rows_imported} color="var(--accent-color)" />
              {result.rows_updated > 0 && (
                <StatBox label={t('import.stat_updated')} value={result.rows_updated} color="#3b82f6" />
              )}
              <StatBox label={t('import.stat_failed')} value={result.rows_failed} color={result.rows_failed > 0 ? '#ef4444' : 'var(--text-secondary)'} />
              <StatBox label={t('import.stat_skipped')} value={result.rows_skipped} color="var(--text-secondary)" />
            </div>

            {/* Warnings */}
            {result.warnings.length > 0 && (
              <div style={{ marginBottom: '12px' }}>
                <p style={{ fontWeight: '500', fontSize: '13px', color: '#f59e0b', marginBottom: '8px' }}>
                  {t('import.warnings')} ({result.warnings.length})
                </p>
                <div style={{ maxHeight: '120px', overflowY: 'auto' }}>
                  {result.warnings.map((w, i) => (
                    <p key={i} style={{ fontSize: '12px', color: 'var(--text-secondary)', padding: '2px 0' }}>
                      ⚠ {w}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Errors */}
            {result.errors.length > 0 && (
              <div style={{ marginBottom: '12px' }}>
                <p style={{ fontWeight: '500', fontSize: '13px', color: '#ef4444', marginBottom: '8px' }}>
                  {t('import.errors')} ({result.errors.length})
                </p>
                <div style={{ maxHeight: '120px', overflowY: 'auto' }}>
                  {result.errors.map((e, i) => (
                    <p key={i} style={{ fontSize: '12px', color: '#ef4444', padding: '2px 0' }}>
                      ✗ {e}
                    </p>
                  ))}
                </div>
              </div>
            )}

            <button className="btn btn-primary" onClick={handleReset} style={{ width: '100%' }}>
              {t('import.import_another')}
            </button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            padding: '16px',
            borderRadius: '12px',
            backgroundColor: '#ef444412',
            border: '1px solid #ef444430',
            color: '#ef4444',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}>
            <XCircle size={20} />
            <span style={{ fontSize: '14px' }}>{error}</span>
          </div>
        )}

        {/* Template Download */}
        <div style={{
          marginTop: '24px',
          padding: '16px',
          borderRadius: '12px',
          backgroundColor: 'var(--surface-hover)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <p style={{ fontWeight: '500', fontSize: '14px' }}>{t('import.template_title')}</p>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {t('import.template_desc')}
            </p>
          </div>
          <button className="btn btn-ghost" onClick={handleDownloadTemplate}>
            <Download size={16} />
            {t('import.download_template')}
          </button>
        </div>
      </div>
    </div>
  );
};

const StatBox = ({ label, value, color }) => (
  <div style={{
    padding: '12px',
    borderRadius: '10px',
    backgroundColor: 'var(--surface-hover)',
    textAlign: 'center',
  }}>
    <p style={{ fontSize: '24px', fontWeight: '700', color }}>{value}</p>
    <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>{label}</p>
  </div>
);

export default DataImport;
