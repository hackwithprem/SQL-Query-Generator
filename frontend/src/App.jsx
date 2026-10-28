import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import PromptInput from './components/PromptInput';
import SqlEditor from './components/SqlEditor';
import ResultsTable from './components/ResultsTable';
import ExplanationCard from './components/ExplanationCard';
import ErrorCorrectionCard from './components/ErrorCorrectionCard';
import SchemaExplorerModal from './components/SchemaExplorerModal';
import HistoryModal from './components/HistoryModal';
import SettingsModal from './components/SettingsModal';
import { apiClient } from './api/client';
import { Sparkles, Terminal, Database, HelpCircle } from 'lucide-react';

export default function App() {
  // App state
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [question, setQuestion] = useState('Show all students who scored more than 80 marks.');
  const [sql, setSql] = useState('');
  const [isSafe, setIsSafe] = useState(true);
  const [clarification, setClarification] = useState(null);
  
  // Async states
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);

  // Results & Feedback
  const [results, setResults] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [executionError, setExecutionError] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Metadata & System info
  const [health, setHealth] = useState(null);
  const [schema, setSchema] = useState(null);
  const [history, setHistory] = useState([]);

  // Modals
  const [isSchemaOpen, setIsSchemaOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Apply theme to html root
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

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // Initial load: Fetch health, schema, history
  useEffect(() => {
    loadHealthAndSchema();
  }, []);

  const loadHealthAndSchema = async () => {
    try {
      const healthData = await apiClient.getHealth();
      setHealth(healthData);

      const schemaData = await apiClient.getSchema();
      setSchema(schemaData);

      const historyData = await apiClient.getHistory();
      setHistory(historyData);
    } catch (err) {
      console.warn("Could not load initial health/schema:", err);
    }
  };

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // Action: Generate SQL
  const handleGenerate = async () => {
    if (!question.trim()) return;
    setIsGenerating(true);
    setExecutionError(null);
    setExplanation(null);

    try {
      const res = await apiClient.generateSql(question);
      setSql(res.sql);
      setIsSafe(res.is_safe);
      setClarification(res.clarification);
      showToast("SQL query generated successfully!");

      // Refresh history
      const historyData = await apiClient.getHistory();
      setHistory(historyData);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Failed to generate SQL.";
      setExecutionError(`Generation Error: ${msg}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // Action: Execute Query
  const handleExecute = async () => {
    if (!sql.trim()) return;
    setIsExecuting(true);
    setExecutionError(null);

    try {
      const res = await apiClient.executeSql(sql);
      setResults(res);
      showToast(`Executed in ${res.duration_ms}ms (${res.row_count} rows returned)`);

      // Refresh history
      const historyData = await apiClient.getHistory();
      setHistory(historyData);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Query execution failed.";
      setExecutionError(msg);
      setResults(null);
    } finally {
      setIsExecuting(false);
    }
  };

  // Action: Explain SQL
  const handleExplain = async () => {
    if (!sql.trim()) return;
    setIsExplaining(true);

    try {
      const res = await apiClient.explainSql(sql, question);
      setExplanation(res.explanation);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Failed to explain SQL.";
      showToast(`Explanation failed: ${msg}`);
    } finally {
      setIsExplaining(false);
    }
  };

  // Action: Clear History
  const handleClearHistory = async () => {
    try {
      await apiClient.clearHistory();
      setHistory([]);
      showToast("Query history cleared.");
    } catch (err) {
      showToast("Failed to clear history.");
    }
  };

  // Reset for New Query
  const handleNewQuery = () => {
    setQuestion('');
    setSql('');
    setResults(null);
    setExplanation(null);
    setExecutionError(null);
    setClarification(null);
    setIsSafe(true);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 light:bg-slate-50 light:text-slate-900">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-xl bg-slate-900/90 text-white border border-slate-700 shadow-2xl backdrop-blur-md text-xs font-medium animate-in fade-in slide-in-from-bottom-2 light:bg-slate-900">
          {toastMessage}
        </div>
      )}

      {/* Sidebar */}
      <Sidebar
        onNewQuery={handleNewQuery}
        onOpenSchema={() => setIsSchemaOpen(true)}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenSamples={() => setIsSchemaOpen(true)}
        theme={theme}
        onToggleTheme={toggleTheme}
        health={health}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Header health={health} />

        {/* Scrollable Center Content */}
        <main className="flex-1 overflow-y-auto px-6 py-6 space-y-6 max-w-6xl w-full mx-auto">
          {/* Welcome Intro Section */}
          <div className="space-y-1">
            <h2 className="text-xl font-bold tracking-tight text-slate-100 light:text-slate-900">
              Natural Language SQL Generator
            </h2>
            <p className="text-xs text-slate-400 light:text-slate-500">
              Type your question in natural English to query the university database. Review and edit the generated query before executing.
            </p>
          </div>

          {/* Natural Language Prompt Area */}
          <PromptInput
            question={question}
            setQuestion={setQuestion}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
          />

          {/* SQL Editor Area */}
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

          {/* Explanation Banner (if requested) */}
          {explanation && (
            <ExplanationCard
              explanation={explanation}
              onClose={() => setExplanation(null)}
            />
          )}

          {/* Error Banner with AI Auto-Fix (if execution failed) */}
          {executionError && (
            <ErrorCorrectionCard
              error={executionError}
              failedSql={sql}
              question={question}
              onApplyCorrection={(fixedSql) => {
                setSql(fixedSql);
                setExecutionError(null);
                showToast("Correction applied to SQL Editor. Click Execute when ready.");
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

      {/* Interactive Modals */}
      <SchemaExplorerModal
        isOpen={isSchemaOpen}
        onClose={() => setIsSchemaOpen(false)}
        schema={schema}
        onSelectTableQuery={(query) => {
          setSql(query);
          showToast("Query loaded into editor!");
        }}
      />

      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
        onLoadQuery={(loadedSql, loadedQuestion) => {
          setSql(loadedSql);
          if (loadedQuestion && !loadedQuestion.startsWith('(')) {
            setQuestion(loadedQuestion);
          }
          showToast("Query loaded into editor!");
        }}
        onClearHistory={handleClearHistory}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        health={health}
      />
    </div>
  );
}
