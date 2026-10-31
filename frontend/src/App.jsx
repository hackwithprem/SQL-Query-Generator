import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import PromptInput from './components/PromptInput';
import SqlEditor from './components/SqlEditor';
import ResultsTable from './components/ResultsTable';
import ExplanationCard from './components/ExplanationCard';
import ErrorCorrectionCard from './components/ErrorCorrectionCard';
import HistoryModal from './components/HistoryModal';
import AuthModal from './components/AuthModal';
import UploadDataModal from './components/UploadDataModal';
import ProfileModal from './components/ProfileModal';
import { apiClient } from './api/client';

export default function App() {
  // ─── Theme ───────────────────────────────────────────────────────────────
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  // ─── Sidebar open/closed ─────────────────────────────────────────────────
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const toggleSidebar = useCallback(() => setIsSidebarOpen(prev => !prev), []);

  // ─── Auth State ──────────────────────────────────────────────────────────
  const [currentUser, setCurrentUser] = useState(null);

  // ─── Active Query Target (dataset or sample DB) ──────────────────────────
  // { type: 'dataset' | 'sample', id: string | null, name: string }
  const [activeTarget, setActiveTarget] = useState({ type: 'sample', id: null, name: null });

  // ─── Core query state ────────────────────────────────────────────────────
  const [question, setQuestion] = useState('Show all students who scored more than 80 marks.');
  const [sql, setSql] = useState('');
  const [isSafe, setIsSafe] = useState(true);
  const [clarification, setClarification] = useState(null);

  // ─── Async states ────────────────────────────────────────────────────────
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);

  // ─── Results & Feedback ──────────────────────────────────────────────────
  const [results, setResults] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [executionError, setExecutionError] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // ─── Metadata & System info ──────────────────────────────────────────────
  const [health, setHealth] = useState(null);
  const [schema, setSchema] = useState(null);
  const [history, setHistory] = useState([]);

  // ─── Modals (Exactly the permitted user features) ────────────────────────
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isUploadDataOpen, setIsUploadDataOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // ─── Apply theme to html root ────────────────────────────────────────────
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

  // ─── Initial load: health, schema, session restore ───────────────────────
  useEffect(() => {
    loadHealthAndSchema();
    restoreSession();
  }, []);

  const restoreSession = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const user = await apiClient.getMe();
      setCurrentUser(user);
      const historyData = await apiClient.getHistory();
      setHistory(historyData);
    } catch {
      localStorage.removeItem('access_token');
    }
  };

  const loadHealthAndSchema = async () => {
    try {
      const healthData = await apiClient.getHealth();
      setHealth(healthData);
      const schemaData = await apiClient.getSchema();
      setSchema(schemaData);
    } catch (err) {
      console.warn('Could not load initial health/schema:', err);
    }
  };

  // ─── Toast helper ────────────────────────────────────────────────────────
  const showToast = useCallback((msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  }, []);

  // ─── Auth handlers ───────────────────────────────────────────────────────
  const handleAuthSuccess = async (user) => {
    setCurrentUser(user);
    showToast(`Welcome, ${user.full_name}! 👋`);
    try {
      const historyData = await apiClient.getHistory();
      setHistory(historyData);
    } catch (err) {
      console.warn('Could not load history on login:', err);
    }
  };

  const handleSignOut = async () => {
    try {
      await apiClient.logout();
    } finally {
      setCurrentUser(null);
      setActiveTarget({ type: 'sample', id: null, name: null });
      setResults(null);
      setSql('');
      setHistory([]);
      setExplanation(null);
      setExecutionError(null);
      showToast('Signed out successfully.');
    }
  };

  // ─── Derived: active dataset ID for API calls ────────────────────────────
  const activeDatasetId = activeTarget.type === 'dataset' ? activeTarget.id : null;

  // Header target description
  const targetDesc = activeTarget.type === 'dataset'
    ? `Dataset: ${activeTarget.name}`
    : 'SQLite University DB';

  const isCustomTarget = activeTarget.type !== 'sample';

  // ─── Action: Generate SQL (Protected by Authentication Gate) ─────────────
  const handleGenerate = async () => {
    if (!question.trim()) return;

    // Strict Authentication Gate: Unauthenticated users are prompted to Sign In / Sign Up
    // The entered question is preserved intact in state!
    if (!currentUser) {
      setIsAuthOpen(true);
      return;
    }

    setIsGenerating(true);
    setExecutionError(null);
    setExplanation(null);

    try {
      const res = await apiClient.generateSql(question, 'sqlite', activeDatasetId);
      setSql(res.sql);
      setIsSafe(res.is_safe);
      // Prefer the schema_assumed clarification from backend; fall back to any other clarification
      setClarification(res.clarification || null);
      if (res.sql) {
        showToast('SQL query generated successfully!');
      } else if (res.clarification || res.explanation) {
        // Generation returned an explanation (e.g. real schema mismatch with explicit schema)
        showToast('ℹ️ ' + (res.clarification || res.explanation).slice(0, 80));
      }
      const historyData = await apiClient.getHistory();
      setHistory(historyData);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to generate SQL.';
      setExecutionError(`Generation Error: ${msg}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // ─── Action: Execute Query ────────────────────────────────────────────────
  const handleExecute = async () => {
    if (!sql.trim()) return;
    if (!currentUser) {
      setIsAuthOpen(true);
      return;
    }

    setIsExecuting(true);
    setExecutionError(null);

    try {
      const res = await apiClient.executeSql(sql, 500, activeDatasetId);
      setResults(res);
      showToast(`Executed in ${res.duration_ms}ms (${res.row_count} rows returned)`);
      const historyData = await apiClient.getHistory();
      setHistory(historyData);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Query execution failed.';
      setExecutionError(msg);
      setResults(null);
    } finally {
      setIsExecuting(false);
    }
  };

  // ─── Action: Explain SQL ──────────────────────────────────────────────────
  const handleExplain = async () => {
    if (!sql.trim()) return;
    setIsExplaining(true);
    try {
      const res = await apiClient.explainSql(sql, question, activeDatasetId);
      setExplanation(res.explanation);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to explain SQL.';
      showToast(`Explanation failed: ${msg}`);
    } finally {
      setIsExplaining(false);
    }
  };

  // ─── Action: Clear History ────────────────────────────────────────────────
  const handleClearHistory = async () => {
    try {
      await apiClient.clearHistory();
      setHistory([]);
      showToast('Query history cleared.');
    } catch {
      showToast('Failed to clear history.');
    }
  };

  // ─── Reset for New Query ──────────────────────────────────────────────────
  const handleNewQuery = () => {
    setQuestion('');
    setSql('');
    setResults(null);
    setExplanation(null);
    setExecutionError(null);
    setClarification(null);
    setIsSafe(true);
  };

  // ─── Dataset selected from Upload Data modal ──────────────────────────────
  const handleSelectDataset = (dataset) => {
    setActiveTarget({ type: 'dataset', id: dataset.id, name: dataset.original_filename });
    showToast(`Active dataset set to "${dataset.original_filename}"`);
    setIsUploadDataOpen(false);
  };

  // ─── Reset to sample DB ───────────────────────────────────────────────────
  const handleResetToSampleDb = () => {
    setActiveTarget({ type: 'sample', id: null, name: null });
    showToast('Switched back to University Sample DB.');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 light:bg-slate-50 light:text-slate-900">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-xl bg-slate-900/95 text-white border border-slate-700 shadow-2xl backdrop-blur-md text-xs font-medium animate-in fade-in slide-in-from-bottom-2 light:bg-slate-900 max-w-sm">
          {toastMessage}
        </div>
      )}

      {/* Collapsible Sidebar — toggle lives inside the sidebar strip */}
      <Sidebar
        onNewQuery={handleNewQuery}
        onOpenUploadData={() => setIsUploadDataOpen(true)}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
        onOpenAuth={() => setIsAuthOpen(true)}
        onSignOut={handleSignOut}
        currentUser={currentUser}
        theme={theme}
        onToggleTheme={toggleTheme}
        isOpen={isSidebarOpen}
        onToggle={toggleSidebar}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Header
          targetDesc={targetDesc}
          onResetToSampleDb={handleResetToSampleDb}
          isCustomTarget={isCustomTarget}
          currentUser={currentUser}
          onOpenAuth={() => setIsAuthOpen(true)}
          onOpenProfile={() => setIsProfileOpen(true)}
        />

        {/* Scrollable Center Content */}
        <main className="flex-1 overflow-y-auto px-6 py-6 space-y-6 max-w-6xl w-full mx-auto">
          {/* Welcome Intro Section */}
          <div className="space-y-1">
            <h2 className="text-xl font-bold tracking-tight text-slate-100 light:text-slate-900">
              SQL Query Generator from Plain English
            </h2>
            <p className="text-xs text-slate-400 light:text-slate-500">
              Transform plain English questions into clean, secure SQL queries. Review and execute against{' '}
              {isCustomTarget ? (
                <span className="text-sky-400 font-semibold">{targetDesc}</span>
              ) : (
                <span className="text-indigo-400 font-semibold">University Sample Database</span>
              )}
              .
            </p>
          </div>

          {/* Natural Language Prompt Area with Sample Questions */}
          <PromptInput
            question={question}
            setQuestion={setQuestion}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
          />

          {/* SQL Editor Area with Review & Execution */}
          <SqlEditor
            sql={sql}
            setSql={setSql}
            onExecute={handleExecute}
            isExecuting={isExecuting}
            onExplain={handleExplain}
            isExplaining={isExplaining}
            onRegenerate={handleGenerate}
            isGenerating={isGenerating}
            clarification={clarification}
            isSafe={isSafe}
          />

          {/* Natural Language Explanation Banner */}
          {explanation && (
            <ExplanationCard
              explanation={explanation}
              onClose={() => setExplanation(null)}
            />
          )}

          {/* Error Banner with AI Auto-Fix (if query fails during execution) */}
          {executionError && (
            <ErrorCorrectionCard
              error={executionError}
              failedSql={sql}
              question={question}
              onApplyCorrection={(fixedSql) => {
                setSql(fixedSql);
                setExecutionError(null);
                showToast('Correction applied to SQL Editor. Click Execute when ready.');
              }}
            />
          )}

          {/* Results Table Section */}
          <ResultsTable
            results={results}
            isLoading={isExecuting}
            error={executionError}
          />
        </main>
      </div>

      {/* ── Modals ────────────────────────────────────────────────────────── */}

      {/* 1. Query History Modal */}
      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
        onLoadQuery={(loadedSql, loadedQuestion) => {
          setSql(loadedSql);
          if (loadedQuestion && !loadedQuestion.startsWith('(')) {
            setQuestion(loadedQuestion);
          }
          showToast('Query loaded into editor!');
        }}
        onClearHistory={handleClearHistory}
      />

      {/* 2. Authentication Modal (Sign In / Sign Up) */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* 3. Upload Data Modal (CSV / Excel) */}
      <UploadDataModal
        isOpen={isUploadDataOpen}
        onClose={() => setIsUploadDataOpen(false)}
        onSelectDatasetForQuery={handleSelectDataset}
        activeDatasetId={activeDatasetId}
      />

      {/* 4. Profile Modal */}
      <ProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        currentUser={currentUser}
        onSignOut={handleSignOut}
        onProfileUpdated={(updatedUser) => {
          setCurrentUser(updatedUser);
          showToast('Profile display name updated!');
        }}
      />
    </div>
  );
}
