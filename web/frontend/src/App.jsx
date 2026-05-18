import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, AlertTriangle, ShieldCheck, Activity, BarChart2, ScanEye } from 'lucide-react';
import './index.css';

const API_URL = 'http://127.0.0.1:5000/api';

const fetchJsonWithRetry = async (url, options = {}, retries = 6) => {
  let lastError;
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const response = await fetch(url, options);
      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        const body = await response.text();
        throw new Error(`API JSON yerine ${contentType || 'bilinmeyen'} yanit dondu. HTTP ${response.status}. ${body.slice(0, 80)}`);
      }
      return await response.json();
    } catch (error) {
      lastError = error;
      await new Promise(resolve => setTimeout(resolve, 700 * (attempt + 1)));
    }
  }
  throw lastError;
};
const BACKGROUND_TOKENS = ['0xFF', 'SYS.MEM', '0110', 'TRK_ERR', 'NULL', 'SCAN_', 'DEEPFAKE', 'TENSOR'];
const BACKGROUND_PARTICLES = Array.from({ length: 25 }).map((_, i) => ({
  id: i,
  x: Math.random() * 100,
  delay: Math.random() * 15,
  duration: 15 + Math.random() * 20,
  text: BACKGROUND_TOKENS[Math.floor(Math.random() * BACKGROUND_TOKENS.length)]
}));

const DICT = {
  tr: {
    title: 'DeepFakeBusted',
    subtitle: '> DİJİTAL GÖRÜNTÜ ANALİZ TERMİNALİ',
    tab_scan: 'Canlı Analiz',
    tab_compare: 'Model Karşılaştırma',
    tab_analysis: 'Eğitim Analizi',
    input_data: '>> GİRİŞ_VERİSİ',
    target_preview: '>> HEDEF_ÖNİZLEME',
    model_view: '>> MODELİN_GÖRDÜĞÜ_YÜZ',
    drag_drop: 'RESMİ SÜRÜKLEYİP BIRAKIN VEYA SEÇMEK İÇİN TIKLAYIN',
    initiate_scan: 'ANALİZİ BAŞLAT',
    compare_all: 'TÜM MODELLERLE KARŞILAŞTIR',
    scanning: 'TARANIYOR...',
    comparing: 'KARŞILAŞTIRILIYOR...',
    awaiting_image: 'GÖRÜNTÜ BEKLENİYOR...',
    analysis_results: '>> ANALİZ_SONUÇLARI',
    all_model_results: '>> TÜM_MODEL_SONUÇLARI',
    consensus: 'KONSENSÜS',
    fake_probability: 'FAKE_OLASILIĞI',
    deepfake_detected: '[ DİKKAT: DEEPFAKE TESPİT EDİLDİ ]',
    real_confirmed: '[ TEMİZ: GERÇEK GÖRÜNTÜ ONAYLANDI ]',
    confidence_level: 'GÜVEN_SEVİYESİ',
    inference_time: 'ÇIKARIM_SÜRESİ',
    face_crop: 'YÜZ_KIRPMA',
    face_crop_applied: 'UYGULANDI',
    face_crop_skipped: 'YÜZ BULUNAMADI',
    error: 'HATA',
    model_compare_title: '>> MODEL_KARŞILAŞTIRMA_MATRİSİ',
    col_model: 'MODEL',
    col_acc: 'DOĞRULUK (ACC)',
    col_auc: 'AUC SKORU',
    col_f1: 'F1 SKORU',
    col_time: 'ORT_SÜRE (ms)',
    no_metrics: 'Henüz model metrikleri bulunamadı.',
    analysis_title: '>> EĞİTİM_GRAFİKLERİ',
    select_model: 'Model Seçin'
  },
  en: {
    title: 'DeepFakeBusted',
    subtitle: '> DIGITAL IMAGE FORENSICS TERMINAL',
    tab_scan: 'Live Scan',
    tab_compare: 'Model Comparison',
    tab_analysis: 'Training Analysis',
    input_data: '>> INPUT_DATA',
    target_preview: '>> TARGET_PREVIEW',
    model_view: '>> MODEL_VIEW',
    drag_drop: 'DRAG & DROP IMAGE HERE OR CLICK TO BROWSE',
    initiate_scan: 'INITIATE SCAN',
    compare_all: 'COMPARE ALL MODELS',
    scanning: 'SCANNING...',
    comparing: 'COMPARING...',
    awaiting_image: 'AWAITING IMAGE...',
    analysis_results: '>> ANALYSIS_RESULTS',
    all_model_results: '>> ALL_MODEL_RESULTS',
    consensus: 'CONSENSUS',
    fake_probability: 'FAKE_PROBABILITY',
    deepfake_detected: '[ WARNING: DEEPFAKE DETECTED ]',
    real_confirmed: '[ CLEAR: REAL IMAGE CONFIRMED ]',
    confidence_level: 'CONFIDENCE_LEVEL',
    inference_time: 'INFERENCE_TIME',
    face_crop: 'FACE_CROP',
    face_crop_applied: 'APPLIED',
    face_crop_skipped: 'FACE NOT FOUND',
    error: 'ERROR',
    model_compare_title: '>> MODEL_COMPARISON_MATRIX',
    col_model: 'MODEL',
    col_acc: 'ACCURACY',
    col_auc: 'AUC SCORE',
    col_f1: 'F1 SCORE',
    col_time: 'AVG_TIME (ms)',
    no_metrics: 'No model metrics found yet.',
    analysis_title: '>> TRAINING_PLOTS',
    select_model: 'Select Model'
  }
};

const CyberBackground = () => {
  return (
    <div className="cyber-bg-container">
      <div className="bg-perspective-grid"></div>
      {BACKGROUND_PARTICLES.map(p => (
        <motion.div
          key={p.id}
          className="floating-data"
          initial={{ y: '110vh', opacity: 0 }}
          animate={{ y: '-10vh', opacity: [0, 0.1, 0.1, 0] }}
          transition={{ duration: p.duration, repeat: Infinity, delay: p.delay, ease: 'linear' }}
          style={{ left: `${p.x}%` }}
        >
          {p.text}
        </motion.div>
      ))}
    </div>
  );
};

const CyberTitle = ({ text }) => {
  const [displayText, setDisplayText] = useState(text);
  const [isGlitching, setIsGlitching] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    let active = true;
    
    const runCycle = async () => {
      while (active) {
        setDisplayText(text);
        setIsVisible(true);
        setIsGlitching(false);
        await new Promise(r => setTimeout(r, 4000 + Math.random() * 3000));
        if (!active) break;

        const eventType = Math.random() > 0.4 ? 'typewriter' : 'sudden';
        
        if (eventType === 'sudden') {
          setIsVisible(false);
          await new Promise(r => setTimeout(r, 200 + Math.random() * 500));
          if (!active) break;

          setIsVisible(true);
          setIsGlitching(true);
          await new Promise(r => setTimeout(r, 400 + Math.random() * 600));
        } else {
          setIsVisible(false);
          await new Promise(r => setTimeout(r, 500 + Math.random() * 500));
          if (!active) break;
          
          setIsVisible(true);
          setIsGlitching(true); 
          
          for (let i = 1; i <= text.length; i++) {
            if (!active) break;
            setDisplayText(text.substring(0, i));
            await new Promise(r => setTimeout(r, 40 + Math.random() * 60));
          }
          if (!active) break;
          await new Promise(r => setTimeout(r, 300));
        }
      }
    };
    
    runCycle();
    return () => { active = false; };
  }, [text]);

  return (
    <h1 style={{ opacity: isVisible ? 1 : 0, transition: 'opacity 0.05s' }}>
      <span className={isGlitching ? "glitch-active" : ""} data-text={displayText}>
        {displayText}
      </span>
    </h1>
  );
};

const MouseTrail = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let width = window.innerWidth;
    let height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;

    let particles = [];
    let ripples = [];
    let lastMouse = { x: width / 2, y: height / 2 };

    const handleResize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };

    const handleMouseMove = (e) => {
      const x = e.clientX;
      const y = e.clientY;
      const dx = x - lastMouse.x;
      const dy = y - lastMouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist > 3) {
        const angle = Math.atan2(dy, dx);
        // Spawn sparks/speed lines
        for (let i = 0; i < 3; i++) {
          particles.push({
            x: x + (Math.random() - 0.5) * 15,
            y: y + (Math.random() - 0.5) * 15,
            vx: Math.cos(angle) * (Math.random() * 8 + 4),
            vy: Math.sin(angle) * (Math.random() * 8 + 4),
            life: 1,
            angle: angle + (Math.random() - 0.5) * 0.2
          });
        }
      }
      lastMouse = { x, y };
    };

    const handleMouseClick = (e) => {
      ripples.push({
        x: e.clientX,
        y: e.clientY,
        radius: 0,
        maxRadius: 50 + Math.random() * 20,
        life: 1
      });

      // Also spawn a burst of particles on click
      for (let i = 0; i < 10; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 10 + 5;
        particles.push({
          x: e.clientX,
          y: e.clientY,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          driftX: (Math.random() - 0.5) * 2,
          driftY: (Math.random() - 0.5) * 2,
          life: 1,
          angle: angle
        });
      }
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('click', handleMouseClick);

    let animationFrameId;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        // Move opposite to mouse direction to create trail
        p.x -= p.vx * 0.3;
        p.y -= p.vy * 0.3;
        p.life -= 0.020;

        if (p.life <= 0) {
          particles.splice(i, 1);
          i--;
          continue;
        }

        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x - Math.cos(p.angle) * 30 * p.life, p.y - Math.sin(p.angle) * 30 * p.life);

        ctx.strokeStyle = `rgba(245, 158, 11, ${p.life * 0.8})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      for (let i = 0; i < ripples.length; i++) {
        const r = ripples[i];
        r.radius += 8;
        r.life -= 0.02;

        if (r.life <= 0) {
          ripples.splice(i, 1);
          i--;
          continue;
        }

        ctx.beginPath();
        ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(245, 158, 11, ${r.life})`;
        ctx.lineWidth = 4;
        ctx.stroke();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('click', handleMouseClick);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} style={{ position: 'fixed', top: 0, left: 0, pointerEvents: 'none', zIndex: 999 }} />;
};

export default function App() {
  const [lang, setLang] = useState('tr');
  const t = DICT[lang];

  const [activeTab, setActiveTab] = useState('scan');

  // App State
  const [models, setModels] = useState([]);
  const [displayNames, setDisplayNames] = useState({});
  const [metrics, setMetrics] = useState({});

  // Scan State
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [model, setModel] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [result, setResult] = useState(null);
  const [allResults, setAllResults] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    const demoImageUrl = new URLSearchParams(window.location.search).get('demoImage');
    if (!demoImageUrl) return;

    let active = true;
    fetch(demoImageUrl)
      .then(response => {
        if (!response.ok) throw new Error('Demo image could not be loaded.');
        return response.blob();
      })
      .then(blob => {
        if (!active) return;
        const fileName = demoImageUrl.split('/').pop() || 'demo-image.webp';
        const demoFile = new File([blob], fileName, { type: blob.type || 'image/webp' });
        setFile(demoFile);
        setPreview(URL.createObjectURL(demoFile));
        setResult(null);
        setAllResults(null);
        setError(null);
      })
      .catch(() => {});

    return () => { active = false; };
  }, []);

  useEffect(() => {
    fetchJsonWithRetry(`${API_URL}/models`)
      .then(data => {
        setModels(data.models || []);
        setDisplayNames(data.display_names || {});
        if (data.models && data.models.length > 0) {
          setModel(data.models.includes('xception_hfdf40') ? 'xception_hfdf40' : data.models[0]);
        }
      })
      .catch(console.error);

    fetchJsonWithRetry(`${API_URL}/metrics`)
      .then(data => setMetrics(data))
      .catch(console.error);
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type.startsWith('image/')) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setResult(null);
      setAllResults(null);
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      setFile(droppedFile);
      setPreview(URL.createObjectURL(droppedFile));
      setResult(null);
      setAllResults(null);
      setError(null);
    }
  };

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const handleScan = async (e) => {
    e.preventDefault();
    if (!file || !model) return;

    setIsScanning(true);
    setResult(null);
    setAllResults(null);
    setError(null);

    const formData = new FormData();
    formData.append('image', file);
    formData.append('model', model);

    try {
      await new Promise(r => setTimeout(r, 1200));
      const data = await fetchJsonWithRetry(`${API_URL}/predict`, { method: 'POST', body: formData }, 2);
      if (data.error) throw new Error(data.error);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsScanning(false);
    }
  };

  const handleCompareAll = async () => {
    if (!file || models.length === 0) return;

    setIsComparing(true);
    setResult(null);
    setAllResults(null);
    setError(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const data = await fetchJsonWithRetry(`${API_URL}/predict-all`, { method: 'POST', body: formData }, 2);
      if (data.error) throw new Error(data.error);
      setAllResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsComparing(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { type: 'spring', stiffness: 100 } }
  };

  const renderScanTab = () => (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="main-grid">
      <motion.div variants={itemVariants} className="panel">
        <h3 className="panel-title">{t.input_data}</h3>
        <form onSubmit={handleScan}>
          <div
            onClick={() => fileInputRef.current.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className={`upload-area ${file ? 'has-file' : ''}`}
          >
            <Upload className="upload-icon" size={32} />
            <div className="upload-text">{file ? file.name : t.drag_drop}</div>
            <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="image/*" style={{ display: 'none' }} />
          </div>

          <select value={model} onChange={(e) => setModel(e.target.value)} className="neo-select">
            {models.length === 0 && <option>{t.select_model}...</option>}
            {models.map(m => (
              <option key={m} value={m}>{displayNames[m] || m}</option>
            ))}
          </select>

          <button type="submit" disabled={!file || isScanning || isComparing || models.length === 0} className="btn-primary">
            {isScanning ? t.scanning : t.initiate_scan}
          </button>
          <button type="button" disabled={!file || isScanning || isComparing || models.length === 0} className="btn-secondary" onClick={handleCompareAll}>
            {isComparing ? t.comparing : t.compare_all}
          </button>
        </form>
        {error && <div className="error-box">[{t.error}]: {error}</div>}
      </motion.div>

      <motion.div variants={itemVariants} className="panel preview-panel">
        <h3 className="panel-title">{t.target_preview}</h3>
        <div className={`preview-container ${isScanning || isComparing ? 'is-scanning' : ''}`}>
          {!preview ? (
            <p className="placeholder-text">{t.awaiting_image}</p>
          ) : (
            <img src={preview} alt="Preview" id="image-preview" style={{ display: 'block' }} />
          )}
          {(isScanning || isComparing) && (
            <motion.div
              initial={{ top: '-10%' }} animate={{ top: '110%' }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
              className="scanline-fx-react"
            />
          )}
        </div>
        {(result?.face_crop?.preview_url || allResults?.summary?.face_crop?.preview_url) && (
          <>
            <h3 className="panel-title model-view-title">{t.model_view}</h3>
            <div className="face-preview-container">
              <img
                src={result?.face_crop?.preview_url || allResults?.summary?.face_crop?.preview_url}
                alt="Face crop preview"
                className="face-preview-img"
              />
            </div>
          </>
        )}
      </motion.div>

      <div className="col-span-full" style={{ gridColumn: '1 / -1' }}>
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="result-panel-react"
            >
              <h3 className="panel-title text-dim">{t.analysis_results}</h3>

              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
                className={`result-badge ${result.label === 'fake' ? 'fake' : 'real'}`}
              >
                <div className="badge-content">
                  {result.label === 'fake' ? <AlertTriangle size={32} /> : <ShieldCheck size={32} />}
                  <span>{result.label === 'fake' ? t.deepfake_detected : t.real_confirmed}</span>
                </div>
              </motion.div>

              <div className="metrics-grid">
                <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.4 }} className="metric">
                  <div className="metric-label">{t.confidence_level}</div>
                  <div className="metric-value">{(result.confidence * 100).toFixed(2)}%</div>
                </motion.div>

                <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.5 }} className="metric">
                  <div className="metric-label">{t.inference_time}</div>
                  <div className="metric-value">{result.inference_time_ms} ms</div>
                </motion.div>
              </div>
              {result.face_crop && (
                <div className={`face-crop-note ${result.face_crop.applied ? 'applied' : 'skipped'}`}>
                  {t.face_crop}: {result.face_crop.applied ? t.face_crop_applied : t.face_crop_skipped}
                </div>
              )}
            </motion.div>
          )}
          {allResults && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="result-panel-react"
            >
              <h3 className="panel-title text-dim">{t.all_model_results}</h3>
              <div className={`result-badge ${allResults.summary.consensus_label === 'fake' ? 'fake' : 'real'}`}>
                <div className="badge-content">
                  {allResults.summary.consensus_label === 'fake' ? <AlertTriangle size={32} /> : <ShieldCheck size={32} />}
                  <span>
                    {t.consensus}: {allResults.summary.consensus_label.toUpperCase()} (
                    {allResults.summary.consensus_label === 'fake'
                      ? allResults.summary.fake_votes
                      : allResults.summary.real_votes}
                    /{allResults.summary.model_count})
                  </span>
                </div>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table className="cmp-table all-results-table">
                  <thead>
                    <tr>
                      <th>{t.col_model}</th>
                      <th>SONUÇ</th>
                      <th>{t.confidence_level}</th>
                      <th>{t.fake_probability}</th>
                      <th>{t.col_time}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allResults.results.map(item => (
                      <tr key={item.model}>
                        <td style={{ color: 'var(--accent)' }}>{item.display_name}</td>
                        <td className={item.label === 'fake' ? 'fake-val' : 'real-val'}>{item.label.toUpperCase()}</td>
                        <td>{(item.confidence * 100).toFixed(2)}%</td>
                        <td>{(item.fake_probability * 100).toFixed(2)}%</td>
                        <td>{item.inference_time_ms.toFixed(2)} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {allResults.summary.face_crop && (
                <div className={`face-crop-note ${allResults.summary.face_crop.applied ? 'applied' : 'skipped'}`}>
                  {t.face_crop}: {allResults.summary.face_crop.applied ? t.face_crop_applied : t.face_crop_skipped}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );

  const renderCompareTab = () => {
    const metricKeys = Object.keys(metrics);
    if (metricKeys.length === 0) return <div className="panel"><p className="text-dim font-mono">{t.no_metrics}</p></div>;

    // Find best values
    const bestAcc = Math.max(...metricKeys.map(k => metrics[k].accuracy || 0));
    const bestAuc = Math.max(...metricKeys.map(k => metrics[k].auc_roc || 0));
    const bestF1 = Math.max(...metricKeys.map(k => metrics[k].f1_score || 0));

    return (
      <motion.div variants={containerVariants} initial="hidden" animate="visible" className="panel">
        <h3 className="panel-title">{t.model_compare_title}</h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="cmp-table">
            <thead>
              <tr>
                <th>{t.col_model}</th>
                <th>{t.col_acc}</th>
                <th>{t.col_auc}</th>
                <th>{t.col_f1}</th>
                <th>{t.col_time}</th>
              </tr>
            </thead>
            <tbody>
              {metricKeys.map(k => {
                const m = metrics[k];
                return (
                  <tr key={k}>
                    <td style={{ color: 'var(--accent)' }}>{displayNames[k] || k}</td>
                    <td className={m.accuracy === bestAcc ? 'best-val' : ''}>{(m.accuracy * 100).toFixed(2)}%</td>
                    <td className={m.auc_roc === bestAuc ? 'best-val' : ''}>{m.auc_roc?.toFixed(4)}</td>
                    <td className={m.f1_score === bestF1 ? 'best-val' : ''}>{m.f1_score?.toFixed(4)}</td>
                    <td>{m.inference_ms ? m.inference_ms.toFixed(2) : '--'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </motion.div>
    );
  };

  const renderAnalysisTab = () => {
    return (
      <motion.div variants={containerVariants} initial="hidden" animate="visible" className="panel">
        <h3 className="panel-title">{t.analysis_title}</h3>
        {models.length === 0 && <p className="text-dim font-mono">{t.select_model}</p>}

        <select value={model} onChange={(e) => setModel(e.target.value)} className="neo-select" style={{ maxWidth: '300px' }}>
          {models.map(m => (
            <option key={m} value={m}>{displayNames[m] || m}</option>
          ))}
        </select>

        {model && (
          <div className="plots-grid">
            <img
              key={`${model}-loss`}
              src={`${API_URL}/plots/${model}_loss_curve.png`}
              alt="Training Loss Curve"
              className="plot-img"
              onLoad={(e) => { e.currentTarget.style.display = 'block'; }}
              onError={(e) => { e.currentTarget.style.display = 'none'; }}
            />
            <img
              key={`${model}-accuracy`}
              src={`${API_URL}/plots/${model}_accuracy_curve.png`}
              alt="Training Accuracy Curve"
              className="plot-img"
              onLoad={(e) => { e.currentTarget.style.display = 'block'; }}
              onError={(e) => { e.currentTarget.style.display = 'none'; }}
            />
            <img
              key={`${model}-confusion`}
              src={`${API_URL}/plots/${model}_confusion_matrix.png`}
              alt="Confusion Matrix"
              className="plot-img"
              onLoad={(e) => { e.currentTarget.style.display = 'block'; }}
              onError={(e) => { e.currentTarget.style.display = 'none'; }}
            />
            <img
              key={`${model}-roc`}
              src={`${API_URL}/plots/${model}_roc_curve.png`}
              alt="ROC Curve"
              className="plot-img"
              onLoad={(e) => { e.currentTarget.style.display = 'block'; }}
              onError={(e) => { e.currentTarget.style.display = 'none'; }}
            />
          </div>
        )}
      </motion.div>
    );
  };

  return (
    <>
      <MouseTrail />
      <CyberBackground />
      <div className="container">
        <div className="lang-toggle">
          <button className={`lang-btn ${lang === 'tr' ? 'active' : ''}`} onClick={() => setLang('tr')}>TR</button>
          <button className={`lang-btn ${lang === 'en' ? 'active' : ''}`} onClick={() => setLang('en')}>EN</button>
        </div>

        <motion.header
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <CyberTitle text={t.title} />
          <p className="subtitle">{t.subtitle}</p>
        </motion.header>

        <div className="tabs-header">
          <button className={`tab-btn ${activeTab === 'scan' ? 'active' : ''}`} onClick={() => setActiveTab('scan')}>
            <ScanEye size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'text-bottom' }} /> {t.tab_scan}
          </button>
          <button className={`tab-btn ${activeTab === 'compare' ? 'active' : ''}`} onClick={() => setActiveTab('compare')}>
            <BarChart2 size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'text-bottom' }} /> {t.tab_compare}
          </button>
          <button className={`tab-btn ${activeTab === 'analysis' ? 'active' : ''}`} onClick={() => setActiveTab('analysis')}>
            <Activity size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'text-bottom' }} /> {t.tab_analysis}
          </button>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'scan' && renderScanTab()}
            {activeTab === 'compare' && renderCompareTab()}
            {activeTab === 'analysis' && renderAnalysisTab()}
          </motion.div>
        </AnimatePresence>
      </div>
    </>
  );
}
