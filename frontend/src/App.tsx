import React, { useState, useEffect, useRef } from 'react';
import { 
  Zap, Table, ShieldCheck, Download, Play, RotateCcw, 
  Square, Search, Copy, Bot, Trash2, Globe, RefreshCw, CheckCircle, ExternalLink, BookOpen, Sparkles
} from 'lucide-react';

interface FileData {
  filename: string;
  filepath: string;
  columns: string[];
  detected_column: string;
  detected_location_column?: string;
  detected_officer_column?: string;
  total_rows: number;
  completed_rows: number;
  found_count: number;
  not_found_count: number;
  pending_count: number;
  unfound_count: number;
  preview: any[];
}

interface AIInfo {
  company_name: string;
  sector: string;
  phone: string;
  website: string;
  summary: string;
}

interface FindLookupData {
  company_name: string;
  brand: string;
  candidate_phones: string[];
  results: { title: string; snippet: string; url: string; phones: string[] }[];
  find_url: string;
  google_url: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'scanner' | 'editor'>('scanner');
  const [currentData, setCurrentData] = useState<FileData | null>(null);
  const [availableFiles, setAvailableFiles] = useState<string[]>([]);
  
  // Scanning controls & settings
  const [isScanning, setIsScanning] = useState(false);
  const [workerCount, setWorkerCount] = useState(15);
  const [deepScan, setDeepScan] = useState(false);
  const [selectedCompanyCol, setSelectedCompanyCol] = useState('');
  const [selectedLocationCol, setSelectedLocationCol] = useState('');
  
  // Live Metrics
  const [metrics, setMetrics] = useState({
    total: 0,
    processed: 0,
    found: 0,
    notFound: 0,
    rate: '0.0',
    speed: '0'
  });
  
  const [hudStatus, setHudStatus] = useState('Beklemede');
  const [hudSub, setHudSub] = useState('Dosya bekleniyor...');
  const [hudEta, setHudEta] = useState('Kalan: —');
  const [logs, setLogs] = useState<{ time: string; text: string; color: string }[]>([]);
  const [recentItems, setRecentItems] = useState<any[]>([]);
  const [filterMode, setFilterMode] = useState<'all' | 'found'>('all');

  // Interactive Table Grid State
  const [tableRows, setTableRows] = useState<any[]>([]);
  const [tableColumns, setTableColumns] = useState<string[]>([]);
  const [tablePage, setTablePage] = useState(1);
  const [tableTotalPages, setTableTotalPages] = useState(1);
  const [tableTotalRows, setTableTotalRows] = useState(0);
  const [tableFilter, setTableFilter] = useState<'all' | 'found' | 'not_found' | 'pending'>('all');
  const [tableSearch, setTableSearch] = useState('');
  const [tableStats, setTableStats] = useState({ found: 0, notFound: 0, pending: 0 });

  // AI Modal
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiData, setAiData] = useState<AIInfo | null>(null);

  // Find.com.tr Quick Lookup & Number Assign Modal
  const [findModalOpen, setFindModalOpen] = useState(false);
  const [findLoading, setFindLoading] = useState(false);
  const [findData, setFindData] = useState<FindLookupData | null>(null);
  const [findTargetRowIdx, setFindTargetRowIdx] = useState<number | null>(null);
  const [manualPhoneInput, setManualPhoneInput] = useState('');
  const [toastMsg, setToastMsg] = useState('');

  // Guide / Help Modal
  const [guideModalOpen, setGuideModalOpen] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3500);
  };

  const addLog = (text: string, color = '#94a3b8') => {
    const time = new Date().toTimeString().split(' ')[0];
    setLogs(prev => [...prev.slice(-150), { time, text, color }]);
  };

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/ws/scan`;
    
    function connect() {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (e) => {
        const m = JSON.parse(e.data);
        if (m.type === 'progress') {
          setMetrics({
            total: m.total_rows,
            processed: m.completed_rows,
            found: m.found_count,
            notFound: m.not_found_count,
            rate: m.success_rate.toString(),
            speed: m.speed.toString()
          });

          const left = m.target_count - m.done_count;
          if (m.speed > 0 && left > 0) {
            const sec = Math.round(left / m.speed);
            setHudEta(`Kalan: ${Math.floor(sec / 60)}dk ${sec % 60}sn`);
          }

          if (m.latest_item) {
            setHudSub(`${m.latest_item.company} ➔ ${m.latest_item.phone}`);
            const isOk = m.latest_item.status === 'Tamamlandı';
            addLog(`[${m.latest_item.status}] ${m.latest_item.company}: ${m.latest_item.phone} (${m.latest_item.reason || ''})`, isOk ? '#34d399' : '#94a3b8');
            setRecentItems(prev => [m.latest_item, ...prev.slice(0, 199)]);
          }
        } else if (m.type === 'done') {
          setIsScanning(false);
          setHudStatus('Tamamlandı');
          addLog(`İŞLEM BİTTİ! Toplam bulunan numara: ${m.found_count}`, '#34d399');
        }
      };

      ws.onclose = () => setTimeout(connect, 1500);
    }

    connect();
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const res = await fetch('/api/files');
      const data = await res.json();
      setAvailableFiles(data.files || []);
      if (data.files && data.files.length > 0) {
        selectFile(data.files[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const selectFile = async (filename: string) => {
    try {
      addLog(`Dosya seçildi: ${filename}`, '#22d3ee');
      const res = await fetch(`/api/select_file?filename=${encodeURIComponent(filename)}`, { method: 'POST' });
      const data = await res.json();
      onFileLoaded(data);
    } catch (err: any) {
      addLog(`Hata: ${err.message}`, '#f87171');
    }
  };

  const onFileLoaded = (d: FileData) => {
    setCurrentData(d);
    setSelectedCompanyCol(d.detected_column);
    setSelectedLocationCol(d.detected_location_column || '');
    setMetrics({
      total: d.total_rows,
      processed: d.completed_rows,
      found: d.found_count,
      notFound: d.not_found_count,
      rate: d.completed_rows > 0 ? ((d.found_count / d.completed_rows) * 100).toFixed(1) : '0.0',
      speed: '0'
    });
    setHudStatus('Hazır');
    setHudSub(`${d.filename} (${d.total_rows.toLocaleString()} satır)`);
    setRecentItems(d.preview || []);
    addLog(`Dosya yüklendi: ${d.filename} (${d.total_rows.toLocaleString()} satır)`, '#34d399');
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    const file = e.target.files[0];
    const fd = new FormData();
    fd.append('file', file);
    addLog(`Yükleniyor: ${file.name}...`, '#22d3ee');
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: fd });
      const d = await res.json();
      onFileLoaded(d);
      fetchFiles();
    } catch (err: any) {
      addLog(`Yükleme Hatası: ${err.message}`, '#f87171');
    }
  };

  const startScan = (mode: 'all' | 'reset_all' | 'unfound') => {
    if (!wsRef.current || !currentData) return;
    if (mode === 'reset_all') {
      if (!confirm('Tüm sonuçlar sıfırlanacak ve listenin tamamı baştan taranacaktır. Onaylıyor musunuz?')) return;
      setMetrics(prev => ({ ...prev, processed: 0, found: 0, notFound: 0, rate: '0.0' }));
      setRecentItems([]);
      addLog('TÜM LİSTE SIFIRLANDI. Sıfırdan baştan taranıyor...', '#ec4899');
    }

    setIsScanning(true);
    setHudStatus('Taranıyor...');
    wsRef.current.send(JSON.stringify({
      action: 'start',
      mode,
      concurrency: workerCount,
      deep_scan: deepScan,
      company_col: selectedCompanyCol,
      location_col: selectedLocationCol
    }));
  };

  const stopScan = () => {
    if (!wsRef.current) return;
    wsRef.current.send(JSON.stringify({ action: 'stop' }));
    setIsScanning(false);
    setHudStatus('Durdu');
    addLog('Tarama durduruldu.', '#f87171');
  };

  const loadTableData = async () => {
    try {
      const res = await fetch(
        `/api/table?page=${tablePage}&page_size=50&search=${encodeURIComponent(tableSearch)}&filter_status=${tableFilter}&sort_by=found_first`
      );
      const data = await res.json();
      setTableRows(data.rows || []);
      setTableColumns(data.columns || []);
      setTableTotalRows(data.total_rows || 0);
      setTableTotalPages(data.total_pages || 1);
      setTableStats({
        found: data.found_total || 0,
        notFound: data.not_found_total || 0,
        pending: data.pending_total || 0
      });
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (activeTab === 'editor') {
      loadTableData();
    }
  }, [activeTab, tablePage, tableFilter, tableSearch]);

  const handleCellUpdate = async (rowIdx: number, colName: string, newVal: string) => {
    try {
      await fetch('/api/update_cell', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row_index: rowIdx, column_name: colName, new_value: newVal })
      });
      loadTableData();
      showToast(`✓ Hücre güncellendi: ${newVal}`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteRow = async (rowIdx: number) => {
    if (!confirm(`${rowIdx + 1}. satırı silmek istediğinize emin misiniz?`)) return;
    try {
      await fetch(`/api/delete_row?row_index=${rowIdx}`, { method: 'POST' });
      loadTableData();
      showToast(`Satır silindi`);
    } catch (err) {
      console.error(err);
    }
  };

  const openFindLookupModal = async (company: string, rowIdx: number) => {
    setFindTargetRowIdx(rowIdx);
    setFindModalOpen(true);
    setFindLoading(true);
    setFindData(null);
    setManualPhoneInput('');
    try {
      const res = await fetch('/api/find_lookup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_name: company })
      });
      const data = await res.json();
      setFindData(data);
      if (data.candidate_phones && data.candidate_phones.length > 0) {
        setManualPhoneInput(data.candidate_phones[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setFindLoading(false);
    }
  };

  const savePhoneToRow = async (phone: string) => {
    if (findTargetRowIdx === null) return;
    if (!phone || !phone.trim()) {
      alert('Lütfen bir telefon numarası girin.');
      return;
    }
    await handleCellUpdate(findTargetRowIdx, 'Bulunan_Telefon', phone.trim());
    setFindModalOpen(false);
    showToast(`✓ ${phone} numarası başarıyla kaydedildi!`);
  };

  const openAiModal = async (company: string, phone = '', url = '') => {
    setAiModalOpen(true);
    setAiLoading(true);
    setAiData(null);
    try {
      const res = await fetch('/api/ai_company_info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: company,
          phone: phone !== '—' ? phone : null,
          website: url !== '—' ? url : null
        })
      });
      const data = await res.json();
      setAiData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setAiLoading(false);
    }
  };

  const copyToClipboard = (txt: string) => {
    navigator.clipboard.writeText(txt);
    showToast(`Kopyalandı: ${txt}`);
  };

  const pct = metrics.total > 0 ? Math.min(100, Math.round((metrics.processed / metrics.total) * 100)) : 0;

  return (
    <div className="container">
      
      {/* Toast Notification */}
      {toastMsg && (
        <div style={{
          position: 'fixed', bottom: '24px', right: '24px', background: '#0284c7', color: '#ffffff',
          padding: '12px 20px', borderRadius: '10px', fontWeight: 800, zIndex: 1000,
          boxShadow: '0 10px 30px rgba(0,0,0,0.8)', border: '1px solid #38bdf8', animation: 'popIn 0.2s ease-out'
        }}>
          {toastMsg}
        </div>
      )}

      {/* Header */}
      <header className="header">
        <div className="brand">
          <div className="brand-icon">
            <Zap className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="brand-title">10K Şirket İstihbarat & Telefon Motoru</h1>
            <p className="brand-sub">React 2026 Engine • Find.com.tr Entegrasyonu • Hata Teşhis Analizi</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button 
            onClick={() => setGuideModalOpen(true)}
            style={{ background: 'rgba(139, 92, 246, 0.2)', border: '1px solid rgba(139, 92, 246, 0.4)', color: '#c084fc' }}
            title="Kullanım Rehberi & İpuçları"
          >
            <BookOpen className="w-4 h-4" /> 📖 Nasıl Çalışır? (Rehber)
          </button>
          
          <button 
            onClick={() => window.location.href = '/api/download'}
            style={{ background: 'linear-gradient(135deg, #10b981, #059669)', color: 'white' }}
          >
            <Download className="w-4 h-4" /> Güncel Excel İndir
          </button>

          <div style={{
            fontSize: '11px', fontWeight: 800, color: '#10b981',
            background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.35)',
            padding: '6px 14px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '6px'
          }}>
            <ShieldCheck className="w-4 h-4" /> %100 Yerel Güvenlik
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="tab-bar">
        <button 
          className={`tab-btn ${activeTab === 'scanner' ? 'active' : ''}`}
          onClick={() => setActiveTab('scanner')}
        >
          <Zap className="w-4 h-4" /> ⚡ Canlı Radar & Tarayıcı
        </button>
        <button 
          className={`tab-btn ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => setActiveTab('editor')}
        >
          <Table className="w-4 h-4" /> 📊 İnteraktif Excel Tablosu & Teşhis Raporu
        </button>
      </div>

      {/* Bento Grid Metrics */}
      <div className="grid-metrics">
        <div className="metric-card">
          <span className="metric-label">Toplam Şirket</span>
          <span className="metric-value">{metrics.total.toLocaleString()}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Taranan</span>
          <span className="metric-value" style={{ color: '#38bdf8' }}>{metrics.processed.toLocaleString()}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Bulunan Numara</span>
          <span className="metric-value" style={{ color: '#34d399' }}>{metrics.found.toLocaleString()}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Bulunamayan</span>
          <span className="metric-value" style={{ color: '#f87171' }}>{metrics.notFound.toLocaleString()}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Başarı Oranı</span>
          <span className="metric-value" style={{ color: '#a78bfa' }}>%{metrics.rate}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Hız</span>
          <span className="metric-value" style={{ color: '#fbbf24' }}>{metrics.speed} /sn</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="progress-container">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
        <div className="progress-text">{pct}% Tamamlandı</div>
      </div>

      {/* TAB 1: SCANNER */}
      {activeTab === 'scanner' && (
        <>
          <div className="control-grid">
            
            {/* 1. File Upload & Select */}
            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '12px' }}>
                  1. DOSYA YÜKLE VEYA SEÇ
                </div>
                
                <label className="dropzone" style={{ display: 'block' }}>
                  <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFileUpload} style={{ display: 'none' }} />
                  <div style={{ fontWeight: 800, color: '#38bdf8', fontSize: '13px' }}>📂 Excel / CSV Dosyası Bırakın</div>
                  <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>Tıklayın veya sürükleyin</div>
                </label>

                {availableFiles.length > 0 && (
                  <div style={{ marginTop: '12px' }}>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Mevcut Dosyalar:</div>
                    <select 
                      value={currentData?.filename || ''} 
                      onChange={(e) => selectFile(e.target.value)}
                      style={{ width: '100%' }}
                    >
                      {availableFiles.map(f => <option key={f} value={f}>{f}</option>)}
                    </select>
                  </div>
                )}
              </div>

              {currentData && (
                <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #1e293b', fontSize: '11px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ color: '#94a3b8', fontWeight: 600 }}>🏢 Şirket Sütunu:</span>
                    <select value={selectedCompanyCol} onChange={e => setSelectedCompanyCol(e.target.value)} style={{ maxWidth: '170px' }}>
                      {currentData.columns.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#94a3b8', fontWeight: 600 }}>📍 Şehir / Adres:</span>
                    <select value={selectedLocationCol} onChange={e => setSelectedLocationCol(e.target.value)} style={{ maxWidth: '170px' }}>
                      <option value="">(Yok / Belirtilmemiş)</option>
                      {currentData.columns.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* 2. Speed Settings */}
            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '12px' }}>
                  2. HIZ & MOTOR AYARLARI
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                    <span style={{ color: '#94a3b8', fontWeight: 600 }}>Eşzamanlı Worker</span>
                    <span style={{ color: '#22d3ee', fontWeight: 800 }}>{workerCount} Worker</span>
                  </div>
                  <input 
                    type="range" min="5" max="35" value={workerCount} 
                    onChange={e => setWorkerCount(parseInt(e.target.value))} 
                    style={{ width: '100%', accentColor: '#06b6d4' }}
                  />
                  <div style={{ fontSize: '10px', color: '#64748b', marginTop: '3px' }}>20.000 şirket için 20-25 worker önerilir.</div>
                </div>

                <label style={{
                  display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px',
                  background: 'rgba(9, 13, 22, 0.7)', padding: '10px 12px', borderRadius: '10px',
                  border: '1px solid #1e293b', cursor: 'pointer'
                }}>
                  <input 
                    type="checkbox" checked={deepScan} onChange={e => setDeepScan(e.target.checked)} 
                    style={{ accentColor: '#06b6d4', width: '16px', height: '16px' }}
                  />
                  <div>
                    <div style={{ fontWeight: 700, color: '#e2e8f0' }}>🌐 Resmi Web Sitelerinin İçine Gir (Derin Mod)</div>
                    <div style={{ fontSize: '10px', color: '#64748b' }}>Kapalıyken 3 kat daha hızlı çalışır (Özet taraması)</div>
                  </div>
                </label>
              </div>

              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '8px' }}>
                Arama Motoru: <span style={{ color: '#34d399', fontWeight: 800 }}>Find.com.tr, Firmatlas & Web Siteleri (Teşhisli)</span>
              </div>
            </div>

            {/* 3. Action Controls */}
            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '8px' }}>
              <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '2px' }}>
                3. KONTROL
              </div>
              <button 
                className="btn-primary" 
                disabled={isScanning || !currentData} 
                onClick={() => startScan('all')}
              >
                <Play className="w-4 h-4" /> 🚀 Kalanları Tara
              </button>
              <button 
                className="btn-reset" 
                disabled={isScanning || !currentData} 
                onClick={() => startScan('reset_all')}
              >
                <RotateCcw className="w-4 h-4" /> 🔁 Tümünü Sıfırdan Baştan Tara
              </button>
              <button 
                className="btn-secondary" 
                disabled={isScanning || !currentData || currentData.unfound_count === 0} 
                onClick={() => startScan('unfound')}
              >
                <RefreshCw className="w-4 h-4" /> 🔄 Sadece Bulunamayanları Tara ({currentData?.unfound_count || 0})
              </button>
              <button 
                className="btn-stop" 
                disabled={!isScanning} 
                onClick={stopScan}
              >
                <Square className="w-4 h-4" /> ⏹️ Durdur
              </button>
              <div style={{ fontSize: '11px', color: '#64748b', textAlign: 'center', marginTop: '2px' }}>
                {currentData ? `${currentData.total_rows.toLocaleString()} satır hazır.` : 'Lütfen dosya yükleyin'}
              </div>
            </div>

          </div>

          {/* HUD & Terminal */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
            <div className="hud-box">
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div className="radar">
                  {isScanning && <div className="radar-sweep" />}
                  <div style={{ width: '10px', height: '10px', background: '#06b6d4', borderRadius: '50%', boxShadow: '0 0 10px #06b6d4' }} />
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 800, textTransform: 'uppercase' }}>AGENT CANLI DURUMU</div>
                  <div style={{ fontSize: '15px', fontWeight: 900, color: '#38bdf8' }}>{hudStatus}</div>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>{hudSub}</div>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 800 }}>ANLIK HIZ</div>
                <div style={{ fontSize: '20px', fontWeight: 900, color: '#34d399', fontFamily: 'monospace' }}>
                  {metrics.speed} <span style={{ fontSize: '11px', color: '#64748b' }}>/sn</span>
                </div>
                <div style={{ fontSize: '11px', color: '#64748b' }}>{hudEta}</div>
              </div>
            </div>

            <div className="terminal" ref={terminalRef}>
              {logs.map((l, i) => (
                <div key={i} style={{ color: l.color, marginBottom: '2px' }}>
                  [{l.time}] {l.text}
                </div>
              ))}
            </div>
          </div>

          {/* Live Recent Stream */}
          <div className="glass-card" style={{ marginTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#f8fafc' }}>⚡ CANLI TARAMA AKIŞI & HATA TEŞHİSİ (Son 200 İşlem)</div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button className={`btn-secondary ${filterMode === 'all' ? 'active' : ''}`} style={{ padding: '5px 12px' }} onClick={() => setFilterMode('all')}>Tümü</button>
                <button className={`btn-secondary ${filterMode === 'found' ? 'active' : ''}`} style={{ padding: '5px 12px' }} onClick={() => setFilterMode('found')}>Sadece Bulunanlar</button>
              </div>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th style={{ width: '45px' }}>#</th>
                    <th>Şirket Adı</th>
                    <th style={{ width: '180px' }}>Bulunan Telefon</th>
                    <th style={{ width: '110px' }}>Durum</th>
                    <th>Neden Bulunamadı / Teşhis Açıklaması</th>
                    <th style={{ width: '180px', textAlign: 'center' }}>İşlem</th>
                  </tr>
                </thead>
                <tbody>
                  {recentItems
                    .filter(it => filterMode === 'all' || (it.phone && it.phone !== '—'))
                    .map((it, idx) => {
                      const isOk = it.status === 'Tamamlandı' || (it.phone && it.phone !== '—');
                      const compName = it.company || it[currentData?.detected_column || ''] || '—';
                      const rowIdx = it.index !== undefined ? it.index : idx;
                      const reasonText = it.reason || it.Neden_Bulunamadi || (isOk ? 'Doğrulandı' : 'Açık dijital kayıt bulunamadı');

                      return (
                        <tr key={idx}>
                          <td style={{ color: '#64748b', fontFamily: 'monospace' }}>{idx + 1}</td>
                          <td style={{ fontWeight: 700, color: '#f1f5f9' }}>{compName}</td>
                          <td style={{ fontFamily: 'monospace', fontWeight: 800, color: isOk ? '#34d399' : '#64748b' }}>
                            {it.phone || '—'} {isOk && (
                              <button className="btn-copy" onClick={() => copyToClipboard(it.phone)} title="Numarayı Kopyala">
                                <Copy className="w-3 h-3 inline" />
                              </button>
                            )}
                          </td>
                          <td>
                            {isOk ? <span className="badge-ok">Tamamlandı</span> : <span className="badge-fail">Bulunamadı</span>}
                          </td>
                          <td>
                            <span className="reason-pill" title={reasonText} style={{ color: isOk ? '#34d399' : '#fca5a5' }}>
                              {isOk ? '✓ ' : '⚠️ '}{reasonText}
                            </span>
                          </td>
                          <td style={{ textAlign: 'center', display: 'flex', gap: '4px', justifyContent: 'center' }}>
                            <button 
                              className="btn-find" 
                              onClick={() => openFindLookupModal(compName, rowIdx)}
                              title="Find.com.tr'da Sorgula & Numara Gir"
                            >
                              <Search className="w-3 h-3 inline" /> Find'da Ara
                            </button>
                            <button className="btn-ai" onClick={() => openAiModal(compName, it.phone, it.url)}>
                              <Bot className="w-3 h-3 inline" /> AI
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* TAB 2: INTERACTIVE EXCEL GRID */}
      {activeTab === 'editor' && (
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
            
            {/* Filter Tabs */}
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
              <button className={`filter-chip ${tableFilter === 'all' ? 'active' : ''}`} onClick={() => { setTableFilter('all'); setTablePage(1); }}>
                🌐 Tümü
              </button>
              <button className={`filter-chip ${tableFilter === 'found' ? 'active' : ''}`} onClick={() => { setTableFilter('found'); setTablePage(1); }}>
                ✅ Numarası Olanlar (En Üstte)
              </button>
              <button className={`filter-chip ${tableFilter === 'not_found' ? 'active' : ''}`} onClick={() => { setTableFilter('not_found'); setTablePage(1); }}>
                ❌ Bulunamayanlar
              </button>
              <button className={`filter-chip ${tableFilter === 'pending' ? 'active' : ''}`} onClick={() => { setTableFilter('pending'); setTablePage(1); }}>
                ⏳ Bekleyenler
              </button>
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input 
                type="search" 
                placeholder="🔍 Tabloda şirket veya telefon ara..." 
                value={tableSearch}
                onChange={e => { setTableSearch(e.target.value); setTablePage(1); }}
                style={{ width: '280px' }}
              />
              <button className="btn-secondary" onClick={loadTableData} style={{ padding: '8px 14px' }}>
                <RefreshCw className="w-4 h-4" /> Yenile
              </button>
            </div>
          </div>

          {/* Stats Bar */}
          <div style={{ display: 'flex', gap: '12px', marginBottom: '12px', fontSize: '11px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ background: 'rgba(14, 165, 233, 0.15)', border: '1px solid rgba(14, 165, 233, 0.3)', padding: '4px 10px', borderRadius: '8px', color: '#38bdf8', fontWeight: 700 }}>
              Bulunan: {tableStats.found.toLocaleString()}
            </span>
            <span style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '4px 10px', borderRadius: '8px', color: '#f87171', fontWeight: 700 }}>
              Bulunamayan: {tableStats.notFound.toLocaleString()}
            </span>
            <span style={{ background: 'rgba(148, 163, 184, 0.15)', padding: '4px 10px', borderRadius: '8px', color: '#94a3b8', fontWeight: 700 }}>
              Bekleyen: {tableStats.pending.toLocaleString()}
            </span>
            <span style={{ marginLeft: 'auto', color: '#38bdf8', fontSize: '11px' }}>
              💡 <b>Neden Bulunamadı Teşhisi:</b> Şirketin açık kaydı olup olmadığını, adaş şirket elenip elenmediğini doğrudan görebilirsiniz.
            </span>
          </div>

          <div className="table-container" style={{ maxHeight: '600px' }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width: '45px' }}>#</th>
                  {tableColumns.map(c => <th key={c}>{c}</th>)}
                  <th style={{ width: '180px', textAlign: 'center' }}>Find.com.tr & Hızlı Giriş</th>
                  <th style={{ width: '50px', textAlign: 'center' }}>Sil</th>
                </tr>
              </thead>
              <tbody>
                {tableRows.map((row, i) => {
                  const rowIdx = row._row_idx;
                  const phone = row['Bulunan_Telefon'] || '';
                  const status = row['Durum'] || 'Bekliyor';
                  const isOk = status === 'Tamamlandı' || (phone && phone.trim() !== '');
                  const compVal = row['Ünvan'] || row['ünvan'] || row[selectedCompanyCol] || row[tableColumns[0]] || '';

                  return (
                    <tr key={rowIdx}>
                      <td style={{ color: '#64748b', fontFamily: 'monospace' }}>{(tablePage - 1) * 50 + i + 1}</td>
                      {tableColumns.map(col => {
                        const val = row[col] || '';
                        if (col === 'Durum') {
                          return (
                            <td key={col}>
                              {isOk ? <span className="badge-ok">Tamamlandı</span> : (status === 'Bulunamadı' ? <span className="badge-fail">Bulunamadı</span> : <span className="badge-wait">Bekliyor</span>)}
                            </td>
                          );
                        }
                        if (col === 'Neden_Bulunamadi') {
                          return (
                            <td key={col}>
                              <span className="reason-pill" title={val} style={{ color: isOk ? '#34d399' : '#fca5a5' }}>
                                {val ? val : (isOk ? 'Doğrulandı' : '—')}
                              </span>
                            </td>
                          );
                        }
                        if (col === 'Bulunan_Telefon') {
                          return (
                            <td 
                              key={col} 
                              className="editable-cell"
                              onClick={() => openFindLookupModal(compVal, rowIdx)}
                              style={{ fontFamily: 'monospace', fontWeight: 800, color: isOk ? '#34d399' : '#64748b' }}
                              title="Numarayı düzenlemek veya Find'da aramak için tıklayın"
                            >
                              {val ? `${val} ` : <span style={{ color: '#38bdf8', textDecoration: 'underline' }}>🔍 Find'da Ara & Gir</span>}
                              {val && (
                                <button className="btn-copy" onClick={(e) => { e.stopPropagation(); copyToClipboard(val); }}>
                                  <Copy className="w-3 h-3 inline" />
                                </button>
                              )}
                            </td>
                          );
                        }
                        if (col === 'Telefon_Kaynak_URL') {
                          return (
                            <td key={col}>
                              {val ? (
                                <a href={val} target="_blank" rel="noreferrer" style={{ color: '#38bdf8', textDecoration: 'none', fontWeight: 600, fontSize: '11px' }}>
                                  {val.substring(0, 30)}...
                                </a>
                              ) : <span style={{ color: '#475569' }}>—</span>}
                            </td>
                          );
                        }
                        return (
                          <td 
                            key={col} 
                            className="editable-cell"
                            onClick={(e) => {
                              const current = (e.currentTarget.textContent || '').trim();
                              const next = prompt(`Düzenle (${col}):`, current === '(boş)' ? '' : current);
                              if (next !== null) handleCellUpdate(rowIdx, col, next);
                            }}
                          >
                            {val ? val : <span style={{ color: '#475569' }}>(boş)</span>}
                          </td>
                        );
                      })}
                      <td style={{ textAlign: 'center', display: 'flex', gap: '4px', justifyContent: 'center' }}>
                        <button 
                          className="btn-find" 
                          onClick={() => openFindLookupModal(compVal, rowIdx)}
                          title="Find.com.tr'da Sorgula & Numara Gir"
                        >
                          <Search className="w-3 h-3 inline" /> Find'da Ara
                        </button>
                        <button className="btn-ai" onClick={() => openAiModal(compVal, phone, row['Telefon_Kaynak_URL'])}>
                          <Bot className="w-3 h-3 inline" /> AI
                        </button>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button onClick={() => handleDeleteRow(rowIdx)} style={{ background: 'rgba(239,68,68,0.2)', color: '#f87171', border: '1px solid rgba(239,68,68,0.4)', padding: '4px 8px', borderRadius: '6px', cursor: 'pointer' }}>
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px', fontSize: '12px' }}>
            <div style={{ color: '#94a3b8', fontWeight: 600 }}>Sayfa {tablePage} / {tableTotalPages} ({tableTotalRows.toLocaleString()} Kayıt)</div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn-secondary" disabled={tablePage <= 1} onClick={() => setTablePage(p => Math.max(1, p - 1))}>◀ Önceki</button>
              <button className="btn-secondary" disabled={tablePage >= tableTotalPages} onClick={() => setTablePage(p => p + 1)}>Sonraki ▶</button>
            </div>
          </div>

        </div>
      )}

      {/* KULLANIM REHBERİ (NASIL ÇALIŞIR?) MODALI */}
      {guideModalOpen && (
        <div className="modal-backdrop" style={{ display: 'flex' }} onClick={() => setGuideModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '820px', maxHeight: '90vh', overflowY: 'auto' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '16px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '40px', height: '40px', background: 'linear-gradient(135deg, #8b5cf6, #ec4899)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <BookOpen className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: 900, color: '#f8fafc' }}>10K Telefon & İstihbarat Agent Kullanım Rehberi</h3>
                  <p style={{ fontSize: '12px', color: '#c084fc', fontWeight: 700 }}>Hızlı Başlangıç & Maksimum Başarı İpuçları</p>
                </div>
              </div>
              <button onClick={() => setGuideModalOpen(false)} style={{ background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155', color: '#94a3b8', borderRadius: '8px', padding: '6px 10px', cursor: 'pointer' }}>✕</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', fontSize: '13px', lineHeight: 1.6 }}>
              
              {/* Adım Adım Rehber */}
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '14px', padding: '18px' }}>
                <div style={{ fontSize: '14px', fontWeight: 900, color: '#38bdf8', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles className="w-4 h-4" /> 🚀 4 Adımda Hızlı Kullanım:
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div style={{ background: 'rgba(9, 13, 22, 0.7)', padding: '12px 16px', borderRadius: '10px', border: '1px solid #1e293b' }}>
                    <div style={{ fontWeight: 800, color: '#f8fafc', marginBottom: '4px' }}>1. Dosya Seçimi</div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>Excel veya CSV dosyanızı açılır listeden seçin veya kutuya bırakın. <b>Şirket Sütunu: Ünvan</b> olarak ayarlanmalıdır.</div>
                  </div>

                  <div style={{ background: 'rgba(9, 13, 22, 0.7)', padding: '12px 16px', borderRadius: '10px', border: '1px solid #1e293b' }}>
                    <div style={{ fontWeight: 800, color: '#f8fafc', marginBottom: '4px' }}>2. Hız & Worker Ayarı</div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>Eşzamanlı tarama hızını belirleyin. 20.000 satırlık dev listelerde <b>20 - 25 Worker</b> idealdir.</div>
                  </div>

                  <div style={{ background: 'rgba(9, 13, 22, 0.7)', padding: '12px 16px', borderRadius: '10px', border: '1px solid #1e293b' }}>
                    <div style={{ fontWeight: 800, color: '#f8fafc', marginBottom: '4px' }}>3. Taramayı Başlatma</div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}><b>🚀 Kalanları Tara</b> diyerek kaldığınız yerden devam edebilir veya <b>🔁 Sıfırdan Baştan</b> başlatabilirsiniz.</div>
                  </div>

                  <div style={{ background: 'rgba(9, 13, 22, 0.7)', padding: '12px 16px', borderRadius: '10px', border: '1px solid #1e293b' }}>
                    <div style={{ fontWeight: 800, color: '#f8fafc', marginBottom: '4px' }}>4. Excel İndirme</div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>Sağ üstteki <b>📥 Güncel Excel İndir</b> butonuna basarak bulunan tüm numaraları ve teşhis raporunu indirebilirsiniz.</div>
                  </div>
                </div>
              </div>

              {/* Find.com.tr Entegrasyonu */}
              <div style={{ background: 'rgba(14, 165, 233, 0.1)', border: '1px solid rgba(14, 165, 233, 0.3)', borderRadius: '14px', padding: '18px' }}>
                <div style={{ fontSize: '14px', fontWeight: 900, color: '#38bdf8', marginBottom: '8px' }}>
                  🔍 Find.com.tr Doğrudan Arama & 1-Tıkla Numara Girişi
                </div>
                <div style={{ color: '#cbd5e1', fontSize: '12px' }}>
                  Bulunamayan şirketlerin yanında bulunan <b>🔍 Find'da Ara</b> butonuna basarak doğrudan Find.com.tr sayfasına gidebilir ve bulduğunuz numarayı açılan kutucuğa yazıp <b>💾 Kaydet</b> diyerek anında Excel'e işleyebilirsiniz.
                </div>
              </div>

              {/* Güvenceler */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '12px', padding: '14px' }}>
                  <div style={{ fontWeight: 800, color: '#34d399', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle className="w-4 h-4" /> Otomatik Kayıt Güvencesi
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                    Elektrik veya internet kesilse bile sistem her 15 satırda bir Excel'e otomatik kaydeder. Asla veri kaybı yaşamazsınız.
                  </div>
                </div>

                <div style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.3)', borderRadius: '12px', padding: '14px' }}>
                  <div style={{ fontWeight: 800, color: '#a78bfa', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ShieldCheck className="w-4 h-4" /> %100 Yerel & Gizli
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                    Yüklediğiniz hiçbir veri dışarı sızmaz, tüm işlemler tamamen kendi bilgisayarınızda gerçekleşir.
                  </div>
                </div>
              </div>

            </div>

          </div>
        </div>
      )}

      {/* FIND.COM.TR QUICK SEARCH & NUMBER INSERTION MODAL */}
      {findModalOpen && (
        <div className="modal-backdrop" style={{ display: 'flex' }} onClick={() => setFindModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '680px' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '14px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', background: 'linear-gradient(135deg, #0ea5e9, #2563eb)', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Search className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 style={{ fontSize: '15px', fontWeight: 900, color: '#f8fafc' }}>Find.com.tr Hızlı Şirket Sorgulama</h3>
                  <p style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 700 }}>Doğrudan Numara Bul & Satıra Kaydet</p>
                </div>
              </div>
              <button onClick={() => setFindModalOpen(false)} style={{ background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155', color: '#94a3b8', borderRadius: '8px', padding: '4px 8px' }}>✕</button>
            </div>

            {/* Target Company Box */}
            <div style={{ background: 'rgba(7, 13, 30, 0.8)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '12px', padding: '14px 18px', marginBottom: '16px' }}>
              <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800 }}>HEDEFLENEN ŞİRKET</div>
              <div style={{ fontSize: '15px', fontWeight: 900, color: '#ffffff', marginTop: '2px' }}>{findData?.company_name || 'Yükleniyor...'}</div>
              {findData?.brand && (
                <div style={{ fontSize: '11px', color: '#38bdf8', marginTop: '3px' }}>Marka: <b>{findData.brand}</b></div>
              )}
            </div>

            {/* Direct Web Links */}
            {findData && (
              <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
                <a 
                  href={findData.find_url} target="_blank" rel="noreferrer"
                  style={{
                    flex: 1, background: 'linear-gradient(135deg, #0284c7, #0369a1)', color: '#ffffff',
                    padding: '10px 14px', borderRadius: '10px', textDecoration: 'none', fontWeight: 800,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', fontSize: '12px'
                  }}
                >
                  <Search className="w-4 h-4" /> 🔍 Find.com.tr Sayfasında Aç <ExternalLink className="w-3 h-3" />
                </a>
                <a 
                  href={findData.google_url} target="_blank" rel="noreferrer"
                  style={{
                    flex: 1, background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#020617',
                    padding: '10px 14px', borderRadius: '10px', textDecoration: 'none', fontWeight: 800,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', fontSize: '12px'
                  }}
                >
                  <Globe className="w-4 h-4" /> 🌐 Google İletişim Aç <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            )}

            {/* Candidate Numbers */}
            {findLoading ? (
              <div style={{ textAlign: 'center', padding: '30px', color: '#38bdf8' }}>
                <div style={{ fontSize: '28px', animation: 'spin 1s linear infinite', display: 'inline-block' }}>⚡</div>
                <div style={{ marginTop: '10px', fontWeight: 800 }}>Find.com.tr ve Resmi Veritabanları Taranıyor...</div>
              </div>
            ) : findData ? (
              <div>
                {findData.candidate_phones.length > 0 ? (
                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 800, color: '#34d399', marginBottom: '8px', textTransform: 'uppercase' }}>
                      ✓ BULUNAN / ÖNERİLEN NUMARALAR (1-Tıkla Ata):
                    </div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {findData.candidate_phones.map((p, idx) => (
                        <button
                          key={idx}
                          onClick={() => { setManualPhoneInput(p); savePhoneToRow(p); }}
                          style={{
                            background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.4)',
                            color: '#34d399', padding: '8px 14px', borderRadius: '8px', fontWeight: 800,
                            fontFamily: 'monospace', fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px'
                          }}
                        >
                          <CheckCircle className="w-4 h-4 text-emerald-400" /> {p} ➔ Satıra Yaz
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '10px 14px', borderRadius: '10px', color: '#f87171', fontSize: '11px', marginBottom: '16px' }}>
                    Otomatik eşleşen numara bulunamadı. Yukarıdaki butonlardan <b>Find.com.tr</b> veya <b>Google</b>'da açıp numarayı aşağıya yazabilirsiniz.
                  </div>
                )}

                {/* Manual Phone Input Box */}
                <div style={{ background: 'rgba(9, 13, 22, 0.9)', border: '1px solid #1e293b', borderRadius: '12px', padding: '14px', marginTop: '10px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '6px' }}>
                    📞 TELEFON NUMARASINI GİRİN VEYA DÜZELTİN:
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input 
                      type="text" 
                      placeholder="+90 212 ... veya 0532 ..." 
                      value={manualPhoneInput}
                      onChange={e => setManualPhoneInput(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') savePhoneToRow(manualPhoneInput); }}
                      style={{ flex: 1, padding: '10px 14px', fontSize: '14px', fontWeight: 700, fontFamily: 'monospace' }}
                      autoFocus
                    />
                    <button 
                      onClick={() => savePhoneToRow(manualPhoneInput)}
                      style={{ background: 'linear-gradient(135deg, #10b981, #059669)', color: '#ffffff', padding: '10px 20px', fontWeight: 800 }}
                    >
                      <CheckCircle className="w-4 h-4" /> 💾 Bu Numarayı Kaydet
                    </button>
                  </div>
                </div>

              </div>
            ) : null}

          </div>
        </div>
      )}

      {/* AI Intelligence Modal */}
      {aiModalOpen && (
        <div className="modal-backdrop" style={{ display: 'flex' }} onClick={() => setAiModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '14px', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '32px', height: '32px', background: 'linear-gradient(135deg, #8b5cf6, #d946ef)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 style={{ fontSize: '15px', fontWeight: 900, color: '#f8fafc' }}>{aiData?.company_name || 'Şirket İstihbarat Raporu'}</h3>
                  <p style={{ fontSize: '11px', color: '#a78bfa', fontWeight: 700 }}>Antigravity AI Analisti (Sıfır API Masrafı)</p>
                </div>
              </div>
              <button onClick={() => setAiModalOpen(false)} style={{ background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155', color: '#94a3b8', borderRadius: '8px', padding: '4px 8px' }}>✕</button>
            </div>

            {aiLoading ? (
              <div style={{ textAlign: 'center', padding: '36px', color: '#38bdf8' }}>
                <div style={{ fontSize: '32px', animation: 'spin 1.2s linear infinite', display: 'inline-block' }}>⚡</div>
                <div style={{ marginTop: '14px', fontWeight: 800, fontSize: '14px' }}>Antigravity Yapay Zeka Şirketi Analiz Ediyor...</div>
                <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>Web sitesi, faaliyet alanı ve istihbarat verileri taranıyor</div>
              </div>
            ) : aiData ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ background: 'linear-gradient(135deg, rgba(7, 13, 30, 0.9), rgba(15, 23, 42, 0.8))', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '12px', padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800 }}>FAALİYET ALANI / SEKTÖR</div>
                    <div style={{ fontSize: '15px', fontWeight: 900, color: '#38bdf8', marginTop: '3px' }}>🏢 {aiData.sector}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 800 }}>TELEFON</div>
                    <div style={{ fontSize: '14px', fontWeight: 800, color: '#34d399', fontFamily: 'monospace' }}>📞 {aiData.phone}</div>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '12px', fontWeight: 800, color: '#a78bfa', marginBottom: '8px' }}>📋 YAPAY ZEKA YÖNETİCİ ÖZETİ</div>
                  <div style={{ background: 'rgba(9, 13, 22, 0.9)', border: '1px solid #1e293b', borderRadius: '10px', padding: '14px', fontSize: '12px', lineHeight: 1.6, color: '#f1f5f9' }}>
                    {aiData.summary}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '6px', textTransform: 'uppercase' }}>🌐 DOĞRULANAN DİJİTAL VARLIKLAR</div>
                  <div style={{ background: 'rgba(7, 13, 30, 0.8)', border: '1px solid #1e293b', borderRadius: '10px', padding: '10px 14px', fontSize: '11px' }}>
                    {aiData.website && aiData.website !== '—' ? (
                      <div><b>Resmi Web Sitesi:</b> <a href={aiData.website} target="_blank" rel="noreferrer" style={{ color: '#38bdf8', fontWeight: 700 }}>{aiData.website}</a></div>
                    ) : <div style={{ color: '#64748b' }}>Doğrulanmış web sitesi bulunamadı</div>}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

    </div>
  );
}
