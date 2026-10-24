import React, { useState, useEffect, useRef } from 'react';
import {
  Clapperboard,
  Film,
  Camera,
  Sparkles,
  Sliders,
  Play,
  Maximize2,
  Download,
  Trash2,
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Eye,
  Grid,
  Monitor,
  LayoutGrid,
  Clock,
  Volume2,
  CloudRain,
  Users,
  Box,
  Zap,
  Palette,
  Crosshair,
  Compass,
  Radio,
  ChevronRight,
  ChevronLeft,
  Layers,
  ArrowRight
} from 'lucide-react';

const THEMES = {
  gold: {
    id: 'gold',
    name: 'Midnight Cinema',
    primary: 'from-amber-400 via-orange-400 to-amber-300',
    accent: 'amber',
    bg: '#07090e',
    cardBg: 'bg-slate-900/60',
    border: 'border-slate-800',
    activeTab: 'bg-amber-500 text-slate-950 font-bold shadow-lg shadow-amber-500/20',
    badge: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
    btnPrimary: 'bg-gradient-to-r from-amber-500 via-orange-500 to-amber-400 text-slate-950 hover:from-amber-400 hover:to-orange-400 shadow-amber-500/20',
    glow: 'rgba(245, 158, 11, 0.25)',
  },
  cyber: {
    id: 'cyber',
    name: 'Cyber Neo-Noir',
    primary: 'from-cyan-400 via-teal-300 to-emerald-400',
    accent: 'cyan',
    bg: '#050a10',
    cardBg: 'bg-cyan-950/20',
    border: 'border-cyan-900/40',
    activeTab: 'bg-cyan-400 text-slate-950 font-bold shadow-lg shadow-cyan-400/25',
    badge: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300',
    btnPrimary: 'bg-gradient-to-r from-cyan-400 via-teal-400 to-emerald-400 text-slate-950 hover:from-cyan-300 hover:to-teal-300 shadow-cyan-500/25',
    glow: 'rgba(6, 182, 212, 0.25)',
  },
  crimson: {
    id: 'crimson',
    name: 'Hollywood 35mm',
    primary: 'from-rose-400 via-red-500 to-orange-400',
    accent: 'rose',
    bg: '#0a0608',
    cardBg: 'bg-rose-950/20',
    border: 'border-rose-900/40',
    activeTab: 'bg-rose-500 text-white font-bold shadow-lg shadow-rose-500/25',
    badge: 'bg-rose-500/10 border-rose-500/30 text-rose-300',
    btnPrimary: 'bg-gradient-to-r from-rose-500 via-red-500 to-orange-500 text-white hover:from-rose-400 hover:to-red-400 shadow-rose-500/25',
    glow: 'rgba(244, 63, 94, 0.25)',
  },
  silver: {
    id: 'silver',
    name: 'Director Titanium',
    primary: 'from-slate-100 via-slate-300 to-slate-400',
    accent: 'slate',
    bg: '#090a0f',
    cardBg: 'bg-slate-900/50',
    border: 'border-slate-700/50',
    activeTab: 'bg-white text-slate-950 font-bold shadow-lg shadow-white/20',
    badge: 'bg-slate-700/40 border-slate-600/50 text-slate-200',
    btnPrimary: 'bg-gradient-to-r from-slate-100 to-slate-300 text-slate-950 hover:from-white hover:to-slate-200 shadow-white/10',
    glow: 'rgba(255, 255, 255, 0.15)',
  }
};

export default function App() {
  const [currentTheme, setCurrentTheme] = useState('gold');
  const [activeViewMode, setActiveViewMode] = useState('monitor'); // 'monitor' | 'deck' | 'script'
  const [scriptText, setScriptText] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('tamil');
  const [breakdown, setBreakdown] = useState(null);
  const [activeSceneIdx, setActiveSceneIdx] = useState(0);
  const [loadingBreakdown, setLoadingBreakdown] = useState(false);
  const [generatingImages, setGeneratingImages] = useState({});
  const [sceneImages, setSceneImages] = useState({});
  const [selectedShots, setSelectedShots] = useState({});
  const [sampleScripts, setSampleScripts] = useState([]);
  const [notification, setNotification] = useState(null);
  const [fullscreenImage, setFullscreenImage] = useState(null);
  const [gridOverlay, setGridOverlay] = useState(false);
  const [timecode, setTimecode] = useState('01:00:00:00');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const theme = THEMES[currentTheme];

  // Timecode counter simulation
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      const s = String(now.getSeconds()).padStart(2, '0');
      const f = String(Math.floor((now.getMilliseconds() / 1000) * 24)).padStart(2, '0');
      setTimecode(`${h}:${m}:${s}:${f}`);
    }, 41); // ~24fps
    return () => clearInterval(timer);
  }, []);

  // Fetch initial breakdown and sample scripts
  useEffect(() => {
    fetch('/api/sample-scripts')
      .then(res => res.json())
      .then(data => setSampleScripts(data))
      .catch(err => console.error("Could not fetch samples:", err));

    fetch('/api/breakdown')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.breakdown) {
          setBreakdown(data.breakdown);
        }
      })
      .catch(err => console.error("Could not fetch existing breakdown:", err));
  }, []);

  const showToast = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleLoadSample = (sample) => {
    setScriptText(sample.text);
    setSelectedLanguage(sample.language);
    showToast(`Loaded: ${sample.title}`);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      showToast(`Ingesting ${file.name}...`, 'info');
      const res = await fetch('/api/upload-script', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      
      setScriptText(data.text);
      showToast(`Loaded ${file.name} successfully!`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleGenerateBreakdown = async () => {
    if (!scriptText.trim()) {
      showToast('Please enter or upload a script first.', 'error');
      return;
    }

    setLoadingBreakdown(true);
    try {
      const res = await fetch('/api/breakdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_text: scriptText,
          language: selectedLanguage
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Analysis failed');

      setBreakdown(data.breakdown);
      setActiveSceneIdx(0);
      showToast(`Analysis complete: ${data.breakdown.scenes?.length || 0} scenes detected!`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoadingBreakdown(false);
    }
  };

  const handleGenerateStoryboard = async (scene, sceneNum) => {
    const shot = selectedShots[sceneNum] || '🎬 முதன்மை காட்சி (Master Dramatic Scene Shot)';
    setGeneratingImages(prev => ({ ...prev, [sceneNum]: true }));

    try {
      const res = await fetch('/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scene, shot })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Image generation failed');

      setSceneImages(prev => ({
        ...prev,
        [sceneNum]: {
          url: data.image_url,
          prompt: data.prompt,
          shot: data.shot
        }
      }));
      showToast(`Scene ${sceneNum} Storyboard rendered!`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setGeneratingImages(prev => ({ ...prev, [sceneNum]: false }));
    }
  };

  const handleClear = async () => {
    if (!window.confirm("Clear all scenes, script, and storyboards?")) return;
    try {
      await fetch('/api/clear', { method: 'POST' });
      setBreakdown(null);
      setScriptText('');
      setSceneImages({});
      setSelectedShots({});
      setActiveSceneIdx(0);
      showToast("Workspace cleared.", 'info');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const scenes = breakdown?.scenes || [];
  const activeScene = scenes[activeSceneIdx] || null;

  return (
    <div 
      className="min-h-screen text-slate-200 flex flex-col font-sans transition-colors duration-500"
      style={{ backgroundColor: theme.bg }}
    >
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-5 py-3 rounded-2xl border backdrop-blur-xl shadow-2xl transition-all ${
          notification.type === 'error'
            ? 'bg-rose-950/80 border-rose-500/50 text-rose-200'
            : notification.type === 'info'
            ? 'bg-cyan-950/80 border-cyan-500/50 text-cyan-200'
            : 'bg-emerald-950/80 border-emerald-500/50 text-emerald-200'
        }`}>
          {notification.type === 'error' ? <AlertCircle className="w-5 h-5 text-rose-400" /> : <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
          <span className="text-xs font-semibold">{notification.message}</span>
        </div>
      )}

      {/* Lightbox Modal */}
      {fullscreenImage && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 backdrop-blur-2xl p-6"
          onClick={() => setFullscreenImage(null)}
        >
          <div className="relative max-w-6xl max-h-[92vh] flex flex-col items-center">
            <img 
              src={fullscreenImage} 
              alt="High-Res Storyboard" 
              className="rounded-2xl border border-white/20 shadow-2xl max-h-[85vh] object-contain"
            />
            <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
              <span>ESC / Click anywhere to close</span>
              <a 
                href={fullscreenImage} 
                download="storyboard.png"
                onClick={(e) => e.stopPropagation()}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white"
              >
                <Download className="w-3.5 h-3.5" /> Download Frame
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Top Production Control Bar (NLE Suite Style) */}
      <header className="sticky top-0 z-40 border-b border-white/5 bg-black/60 backdrop-blur-2xl px-6 py-3">
        <div className="max-w-[1700px] mx-auto flex flex-wrap items-center justify-between gap-4">
          
          {/* Logo & Production Metadata */}
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-slate-900 to-black border border-white/10 flex items-center justify-center shadow-lg">
                <Clapperboard className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className={`text-lg font-black tracking-wider bg-gradient-to-r ${theme.primary} bg-clip-text text-transparent`}>
                    AI DIRECTOR PRO
                  </span>
                  <span className="text-[9px] uppercase tracking-widest font-mono font-bold px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">
                    NLE v2.5
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    ONLINE
                  </span>
                  <span>•</span>
                  <span>24.000 FPS</span>
                  <span>•</span>
                  <span>4K SCOPE 2.39:1</span>
                </div>
              </div>
            </div>

            {/* Live SMPTE Timecode Counter */}
            <div className="hidden lg:flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl bg-black/80 border border-white/10 font-mono text-xs shadow-inner">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
              <span className="text-slate-500 font-bold">TC:</span>
              <span className="text-amber-400 tracking-wider font-semibold">{timecode}</span>
            </div>
          </div>

          {/* Central Workspace Mode Selector */}
          <div className="flex items-center bg-black/50 border border-white/10 p-1 rounded-xl gap-1">
            {[
              { id: 'monitor', label: 'Viewfinder Studio', icon: Monitor },
              { id: 'deck', label: 'Storyboard Deck', icon: LayoutGrid },
              { id: 'script', label: 'Script Teleprompter', icon: FileText }
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeViewMode === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveViewMode(tab.id)}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive ? theme.activeTab : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Right Controls: Theme, Language, Reset */}
          <div className="flex items-center gap-3">
            {/* Theme Palette Picker */}
            <div className="flex items-center gap-1.5 bg-black/40 border border-white/10 p-1 rounded-xl" title="Change Studio Theme">
              <Palette className="w-3.5 h-3.5 text-slate-500 ml-1.5" />
              {Object.keys(THEMES).map(tKey => (
                <button
                  key={tKey}
                  onClick={() => setCurrentTheme(tKey)}
                  className={`w-5 h-5 rounded-lg transition-transform ${
                    currentTheme === tKey ? 'scale-110 ring-2 ring-white/60' : 'opacity-60 hover:opacity-100'
                  }`}
                  style={{
                    backgroundColor: tKey === 'gold' ? '#F59E0B' : tKey === 'cyber' ? '#06B6D4' : tKey === 'crimson' ? '#F43F5E' : '#E2E8F0'
                  }}
                  title={THEMES[tKey].name}
                />
              ))}
            </div>

            {/* Language Switcher */}
            <div className="hidden sm:flex items-center bg-black/40 border border-white/10 rounded-xl p-1 text-[11px]">
              {[
                { id: 'tamil', label: 'தமிழ்' },
                { id: 'english', label: 'EN' },
                { id: 'hindi', label: 'हि' },
                { id: 'telugu', label: 'తె' }
              ].map(lang => (
                <button
                  key={lang.id}
                  onClick={() => setSelectedLanguage(lang.id)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                    selectedLanguage === lang.id
                      ? 'bg-white/20 text-white font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {lang.label}
                </button>
              ))}
            </div>

            {/* Reset */}
            <button
              onClick={handleClear}
              className="p-2 rounded-xl bg-black/40 hover:bg-rose-950/40 border border-white/10 hover:border-rose-500/40 text-slate-400 hover:text-rose-300 transition-all"
              title="Reset Project"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

        </div>
      </header>

      {/* Main Studio Body */}
      <div className="flex-1 max-w-[1700px] w-full mx-auto px-6 py-6 grid grid-cols-1 xl:grid-cols-12 gap-6">
        
        {/* Left Column: Script Ingestion & Teleprompter Panel */}
        <div className={`xl:col-span-4 flex flex-col gap-5 ${sidebarOpen ? '' : 'hidden xl:flex'}`}>
          
          <div className={`rounded-3xl border ${theme.border} ${theme.cardBg} backdrop-blur-xl p-6 shadow-2xl flex flex-col gap-4 relative overflow-hidden`}>
            
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className={`p-2 rounded-xl ${theme.badge}`}>
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white tracking-wide">Screenplay Ingestion</h2>
                  <p className="text-[11px] text-slate-400">Story, script breakdown & visual seeds</p>
                </div>
              </div>

              {/* Sample script quick loader */}
              <div className="flex items-center gap-1.5">
                {sampleScripts.slice(0, 3).map((sample, i) => (
                  <button
                    key={sample.id}
                    onClick={() => handleLoadSample(sample)}
                    className="text-[10px] font-mono px-2 py-1 rounded-lg bg-black/40 hover:bg-white/10 text-slate-300 hover:text-white border border-white/10 transition-all"
                    title={sample.title}
                  >
                    Demo {i + 1}
                  </button>
                ))}
              </div>
            </div>

            {/* Textarea */}
            <div className="relative">
              <textarea
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                placeholder="Paste your screenplay scene, dramatic Tamil/English story, or cinema action lines here..."
                rows={11}
                className="w-full bg-black/60 border border-white/10 rounded-2xl p-4 text-xs font-mono leading-relaxed text-slate-200 placeholder-slate-600 focus:outline-none focus:border-white/30 focus:ring-1 focus:ring-white/20 transition-all resize-none shadow-inner"
              />
              <div className="absolute bottom-3 right-3 text-[10px] font-mono text-slate-500">
                {scriptText.length} chars
              </div>
            </div>

            {/* Actions: File upload & Run Breakdown */}
            <div className="flex flex-col gap-3">
              <label className="cursor-pointer flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white transition-all shadow-sm">
                <Upload className="w-3.5 h-3.5" />
                <span>Import Script (PDF / DOCX / TXT)</span>
                <input
                  type="file"
                  accept=".txt,.pdf,.docx"
                  className="hidden"
                  onChange={handleFileUpload}
                />
              </label>

              <button
                onClick={handleGenerateBreakdown}
                disabled={loadingBreakdown}
                className={`w-full py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all flex items-center justify-center gap-2.5 shadow-xl ${theme.btnPrimary} disabled:opacity-50`}
              >
                {loadingBreakdown ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Deconstructing Screenplay...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>காட்சி பிரிப்பு உருவாக்கு (Generate Breakdown)</span>
                  </>
                )}
              </button>
            </div>

          </div>

          {/* Film Stats Card */}
          {breakdown && (
            <div className={`rounded-3xl border ${theme.border} bg-black/40 backdrop-blur-xl p-5 space-y-4`}>
              <div className="flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider">
                <span>Production Overview</span>
                <span className="text-[10px] text-emerald-400 font-mono">ANALYSIS READY</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <div className="text-[10px] text-slate-400 font-medium">Total Scenes</div>
                  <div className="text-xl font-black text-white mt-0.5">{scenes.length}</div>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <div className="text-[10px] text-slate-400 font-medium">Frames Generated</div>
                  <div className="text-xl font-black text-amber-400 mt-0.5">
                    {Object.keys(sceneImages).length} / {scenes.length}
                  </div>
                </div>
              </div>
              <div className="text-xs text-slate-300 font-medium truncate">
                🎬 Title: <span className="text-white font-bold">{breakdown.title || 'Untitled Feature'}</span>
              </div>
            </div>
          )}

        </div>

        {/* Right Column: Central Production Stage */}
        <div className="xl:col-span-8 flex flex-col gap-6">

          {/* Filmstrip Scene Reel Selector */}
          {scenes.length > 0 && (
            <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-none">
              {scenes.map((scene, idx) => {
                const sn = scene.scene_number || (idx + 1);
                const hasImg = Boolean(sceneImages[sn]?.url);
                const isSelected = activeSceneIdx === idx;

                return (
                  <button
                    key={idx}
                    onClick={() => setActiveSceneIdx(idx)}
                    className={`flex-shrink-0 flex items-center gap-3 px-4 py-2.5 rounded-2xl border transition-all text-left ${
                      isSelected
                        ? `${theme.badge} border-white/40 shadow-lg`
                        : 'bg-black/40 border-white/5 text-slate-400 hover:text-slate-200 hover:border-white/20'
                    }`}
                  >
                    <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold ${
                      isSelected ? 'bg-white text-slate-950 font-black' : 'bg-white/10 text-slate-400'
                    }`}>
                      {sn}
                    </div>
                    <div>
                      <div className="text-xs font-bold truncate max-w-[140px] text-slate-200">
                        {scene.location || `Scene ${sn}`}
                      </div>
                      <div className="text-[10px] font-mono text-slate-400">
                        {scene.time || 'Day/Night'}
                      </div>
                    </div>
                    {hasImg && (
                      <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400" title="Storyboard Ready" />
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* MODE 1: DIRECTOR MONITOR & VIEWFINDER */}
          {activeViewMode === 'monitor' && (
            <div className="space-y-6">
              {activeScene ? (
                <>
                  {/* Master Viewfinder Monitor Box */}
                  <div className="rounded-3xl border border-white/10 bg-black/90 p-5 shadow-2xl space-y-4 relative overflow-hidden">
                    
                    {/* Viewfinder Header Controls */}
                    <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1.5 text-red-500 font-bold uppercase tracking-widest text-[10px]">
                          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                          MONITOR • SCENE {activeScene.scene_number || activeSceneIdx + 1}
                        </span>
                        <span>|</span>
                        <span>SHUTTER: 180°</span>
                        <span>|</span>
                        <span>ISO 800</span>
                        <span>|</span>
                        <span>ARRI ALEXA MINI LF</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setGridOverlay(!gridOverlay)}
                          className={`p-1.5 rounded-lg border text-xs transition-all ${
                            gridOverlay ? 'bg-white/20 border-white/40 text-white' : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
                          }`}
                          title="Toggle Rule-of-Thirds Grid"
                        >
                          <Grid className="w-3.5 h-3.5" />
                        </button>
                        {sceneImages[activeScene.scene_number]?.url && (
                          <button
                            onClick={() => setFullscreenImage(sceneImages[activeScene.scene_number].url)}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/20 border border-white/10 text-slate-300 hover:text-white transition-all"
                            title="Fullscreen View"
                          >
                            <Maximize2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Viewfinder Screen Area (16:9) */}
                    <div className="relative aspect-video rounded-2xl bg-[#040609] border border-white/10 overflow-hidden flex items-center justify-center shadow-inner group">
                      
                      {/* Viewfinder Corner Overlays */}
                      <div className="absolute top-3 left-3 w-6 h-6 border-t-2 border-l-2 border-white/40 pointer-events-none z-10" />
                      <div className="absolute top-3 right-3 w-6 h-6 border-t-2 border-r-2 border-white/40 pointer-events-none z-10" />
                      <div className="absolute bottom-3 left-3 w-6 h-6 border-b-2 border-l-2 border-white/40 pointer-events-none z-10" />
                      <div className="absolute bottom-3 right-3 w-6 h-6 border-b-2 border-r-2 border-white/40 pointer-events-none z-10" />

                      {/* Rule of Thirds Grid Overlay */}
                      {gridOverlay && (
                        <div className="absolute inset-0 pointer-events-none grid grid-cols-3 grid-rows-3 z-10">
                          <div className="border-r border-b border-white/15" />
                          <div className="border-r border-b border-white/15" />
                          <div className="border-b border-white/15" />
                          <div className="border-r border-b border-white/15" />
                          <div className="border-r border-b border-white/15" />
                          <div className="border-b border-white/15" />
                          <div className="border-r border-white/15" />
                          <div className="border-r border-white/15" />
                          <div />
                        </div>
                      )}

                      {/* Center Crosshair */}
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-30 z-10">
                        <Crosshair className="w-12 h-12 text-white" />
                      </div>

                      {/* Actual Storyboard Frame Image */}
                      {sceneImages[activeScene.scene_number]?.url ? (
                        <img
                          src={sceneImages[activeScene.scene_number].url}
                          alt="Rendered Storyboard"
                          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                        />
                      ) : (
                        <div className="text-center p-8 space-y-3 z-10">
                          <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto text-slate-500">
                            <Camera className="w-7 h-7" />
                          </div>
                          <p className="text-xs text-slate-400 font-medium">
                            No storyboard frame rendered yet for Scene {activeScene.scene_number}.
                          </p>
                          <p className="text-[11px] text-slate-600 font-mono">
                            Select framing below & click "Generate Frame"
                          </p>
                        </div>
                      )}

                      {/* Loading Spinner Overlay */}
                      {generatingImages[activeScene.scene_number] && (
                        <div className="absolute inset-0 bg-black/85 backdrop-blur-md flex flex-col items-center justify-center gap-3 z-20">
                          <RefreshCw className="w-9 h-9 text-amber-400 animate-spin" />
                          <div className="text-center">
                            <p className="text-xs font-bold text-white tracking-wide">
                              SYNTHESIZING CINEMATIC FRAME...
                            </p>
                            <span className="text-[10px] text-slate-400 font-mono">
                              Rendering actions, characters, weather & lighting
                            </span>
                          </div>
                        </div>
                      )}

                    </div>

                    {/* Viewfinder Bottom Control Strip */}
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center pt-2">
                      <div className="md:col-span-8 flex items-center gap-3">
                        <div className="w-full">
                          <label className="text-[10px] uppercase tracking-wider font-mono text-slate-400 block mb-1">
                            Camera Framing Preset
                          </label>
                          <select
                            value={selectedShots[activeScene.scene_number] || ''}
                            onChange={(e) => setSelectedShots(prev => ({
                              ...prev,
                              [activeScene.scene_number]: e.target.value
                            }))}
                            className="w-full bg-black/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-white/30"
                          >
                            <option value="🎬 முதன்மை காட்சி (Master Dramatic Scene Shot)">
                              🎬 முதன்மை காட்சி (Master Dramatic Scene Shot)
                            </option>
                            {activeScene.dialogues?.flatMap(d => d.shots || []).map((s, idx) => (
                              <option key={idx} value={`📷 ${s}`}>
                                📷 {s}
                              </option>
                            ))}
                            <option value="📷 Low Angle Dramatic Power Shot">
                              📷 Low Angle Dramatic Power Shot
                            </option>
                            <option value="📷 Extreme Close-Up - Emotional Character Focus">
                              📷 Extreme Close-Up - Emotional Character Focus
                            </option>
                            <option value="📷 Wide Establishing Shot - Full Environment">
                              📷 Wide Establishing Shot - Full Environment
                            </option>
                          </select>
                        </div>
                      </div>

                      <div className="md:col-span-4 pt-4 md:pt-0">
                        <button
                          onClick={() => handleGenerateStoryboard(activeScene, activeScene.scene_number)}
                          disabled={generatingImages[activeScene.scene_number]}
                          className={`w-full py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg transition-all ${theme.btnPrimary} disabled:opacity-50`}
                        >
                          {generatingImages[activeScene.scene_number] ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Camera className="w-3.5 h-3.5" />
                          )}
                          <span>Render Frame</span>
                        </button>
                      </div>
                    </div>

                    {/* Prompt Inspector Box */}
                    {sceneImages[activeScene.scene_number]?.prompt && (
                      <div className="p-3.5 rounded-2xl bg-white/5 border border-white/5 text-xs text-slate-400 space-y-1">
                        <div className="flex items-center gap-1.5 font-mono text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                          <Eye className="w-3.5 h-3.5" />
                          <span>AI Synthesized Director Prompt:</span>
                        </div>
                        <p className="text-[11px] font-mono text-slate-300 leading-relaxed">
                          {sceneImages[activeScene.scene_number].prompt}
                        </p>
                      </div>
                    )}

                  </div>

                  {/* Scene Breakdown Details Card */}
                  <div className={`rounded-3xl border ${theme.border} ${theme.cardBg} backdrop-blur-xl p-8 space-y-6 shadow-2xl`}>
                    
                    {/* Scene Metadata Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-white/5">
                      <div>
                        <div className="flex items-center gap-3">
                          <span className={`px-3 py-1 rounded-xl text-xs font-bold uppercase tracking-wider ${theme.badge}`}>
                            காட்சி {activeScene.scene_number || activeSceneIdx + 1}
                          </span>
                          <h3 className="text-xl font-black text-white">
                            {activeScene.location}
                          </h3>
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                          <span className="flex items-center gap-1.5 text-amber-300 font-medium">
                            <Clock className="w-3.5 h-3.5" /> {activeScene.time || 'Day/Night'}
                          </span>
                          {activeScene.weather && (
                            <span className="flex items-center gap-1.5 text-cyan-300 font-medium">
                              <CloudRain className="w-3.5 h-3.5" /> {activeScene.weather}
                            </span>
                          )}
                        </div>
                      </div>

                      {activeScene.audio && (
                        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs text-purple-300 font-mono">
                          <Volume2 className="w-3.5 h-3.5 text-purple-400" />
                          <span>{activeScene.audio}</span>
                        </div>
                      )}
                    </div>

                    {/* Character & Props Row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Characters */}
                      <div className="p-4 rounded-2xl bg-black/40 border border-white/5 space-y-2">
                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                          <Users className="w-4 h-4 text-amber-400" />
                          <span>கதாபாத்திரங்கள் (Characters)</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {activeScene.characters?.map((c, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs font-semibold">
                              {c}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Props */}
                      <div className="p-4 rounded-2xl bg-black/40 border border-white/5 space-y-2">
                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                          <Box className="w-4 h-4 text-cyan-400" />
                          <span>உபகரணங்கள் (Props)</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {activeScene.props?.map((p, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-200 text-xs font-semibold">
                              {p}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Summary */}
                    {activeScene.summary && (
                      <div className="p-4 rounded-2xl bg-black/40 border border-white/5 space-y-1.5">
                        <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
                          Scene Narrative Summary
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed font-sans">
                          {activeScene.summary}
                        </p>
                      </div>
                    )}

                    {/* Action Beats Timeline */}
                    {activeScene.action?.length > 0 && (
                      <div className="space-y-3">
                        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                          <Play className="w-3.5 h-3.5 text-amber-400" />
                          <span>நடவடிக்கைகள் (Sequential Action Beats)</span>
                        </div>
                        <div className="space-y-2">
                          {activeScene.action.map((act, i) => (
                            <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-black/40 border border-white/5 text-xs text-slate-300">
                              <span className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center text-[10px] font-bold text-slate-400 flex-shrink-0 mt-0.5">
                                {i + 1}
                              </span>
                              <p className="leading-relaxed">{act}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Dialogues & Shots */}
                    {activeScene.dialogues?.length > 0 && (
                      <div className="space-y-3">
                        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                          <Radio className="w-3.5 h-3.5 text-cyan-400" />
                          <span>உரையாடல்கள் & ஷாட்கள் (Dialogues & Shots)</span>
                        </div>
                        <div className="space-y-3">
                          {activeScene.dialogues.map((dlg, i) => (
                            <div key={i} className="p-4 rounded-2xl bg-black/50 border border-white/5 space-y-2">
                              <div className="flex items-center gap-2 text-xs font-bold text-amber-400">
                                <span>{dlg.character}</span>
                              </div>
                              <p className="text-sm font-medium text-slate-100 pl-4 leading-relaxed">
                                "{dlg.line}"
                              </p>
                              <div className="pl-4 pt-1 flex flex-wrap gap-2">
                                {dlg.shots?.length > 0 ? (
                                  dlg.shots.map((s, sIdx) => (
                                    <span key={sIdx} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-[11px] font-medium">
                                      <Camera className="w-3 h-3 text-cyan-400" />
                                      {s}
                                    </span>
                                  ))
                                ) : (
                                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-cyan-950/30 border border-cyan-500/20 text-cyan-300 text-[11px]">
                                    <Camera className="w-3 h-3 text-cyan-400" />
                                    Close-up - {dlg.character} உணர்ச்சி வெளிப்பாடு
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  </div>
                </>
              ) : (
                <div className="rounded-3xl border border-white/10 bg-black/40 p-12 text-center space-y-3">
                  <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto text-slate-600">
                    <Film className="w-8 h-8" />
                  </div>
                  <h3 className="text-base font-bold text-slate-200">No Script Analyzed Yet</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Paste your screenplay in the left ingestion dock or click a Demo sample to generate full breakdowns and cinematic storyboards.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* MODE 2: STORYBOARD DECK (WALL OF FRAMES) */}
          {activeViewMode === 'deck' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-2">
                <div>
                  <h3 className="text-base font-black text-white">Production Storyboard Wall</h3>
                  <p className="text-xs text-slate-400">All screenplay scenes visual pre-visualization gallery</p>
                </div>
              </div>

              {scenes.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {scenes.map((sc, i) => {
                    const sn = sc.scene_number || (i + 1);
                    const img = sceneImages[sn];

                    return (
                      <div key={i} className={`rounded-3xl border ${theme.border} bg-black/60 p-5 space-y-4 shadow-xl flex flex-col justify-between`}>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className={`px-2.5 py-0.5 rounded-lg text-xs font-bold ${theme.badge}`}>
                              Scene {sn}
                            </span>
                            <span className="text-xs text-slate-400 font-mono">
                              {sc.time || 'Day/Night'}
                            </span>
                          </div>
                          <h4 className="text-sm font-bold text-white truncate">
                            {sc.location}
                          </h4>

                          {/* Image Box */}
                          <div className="relative aspect-video rounded-xl bg-black/90 border border-white/10 overflow-hidden flex items-center justify-center">
                            {img?.url ? (
                              <img
                                src={img.url}
                                alt={`Scene ${sn}`}
                                className="w-full h-full object-cover cursor-pointer hover:scale-105 transition-transform"
                                onClick={() => setFullscreenImage(img.url)}
                              />
                            ) : (
                              <div className="text-center p-4">
                                <Camera className="w-8 h-8 text-slate-700 mx-auto mb-1" />
                                <span className="text-[11px] text-slate-500 font-mono">Frame Not Rendered</span>
                              </div>
                            )}

                            {generatingImages[sn] && (
                              <div className="absolute inset-0 bg-black/80 flex items-center justify-center gap-2">
                                <RefreshCw className="w-5 h-5 text-amber-400 animate-spin" />
                                <span className="text-xs text-white font-mono">Rendering...</span>
                              </div>
                            )}
                          </div>

                          <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                            {sc.summary}
                          </p>
                        </div>

                        <div className="pt-2">
                          <button
                            onClick={() => handleGenerateStoryboard(sc, sn)}
                            disabled={generatingImages[sn]}
                            className={`w-full py-2 rounded-xl text-xs font-bold flex items-center justify-center gap-2 ${theme.btnPrimary} disabled:opacity-50`}
                          >
                            <Camera className="w-3.5 h-3.5" />
                            <span>{img?.url ? 'Re-render Frame' : 'Generate Frame'}</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="rounded-3xl border border-white/10 bg-black/40 p-12 text-center text-xs text-slate-500">
                  Analyze a script first to view the production storyboard deck.
                </div>
              )}
            </div>
          )}

          {/* MODE 3: SCRIPT TELEPROMPTER */}
          {activeViewMode === 'script' && (
            <div className={`rounded-3xl border ${theme.border} bg-black/80 p-8 shadow-2xl space-y-6 font-mono`}>
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <span className="text-xs uppercase tracking-widest text-slate-400 font-bold">Screenplay Teleprompter</span>
                <span className="text-xs text-amber-400 font-bold">{breakdown?.title || 'Screenplay Text'}</span>
              </div>
              <div className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed max-h-[70vh] overflow-y-auto pr-4">
                {scriptText || "No script text currently entered."}
              </div>
            </div>
          )}

        </div>

      </div>

      {/* Studio Footer */}
      <footer className="border-t border-white/5 py-6 px-6 text-center text-[11px] font-mono text-slate-500">
        AI Director Pro Studio 2.5 • Advanced Cinematic Script Deconstruction & Photorealistic Storyboard Generator
      </footer>
    </div>
  );
}
