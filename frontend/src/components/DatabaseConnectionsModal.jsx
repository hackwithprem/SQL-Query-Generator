import React, { useState, useEffect } from 'react';
import { 
  X, 
  Database, 
  Plus, 
  Trash2, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles, 
  ArrowRight,
  ShieldCheck,
  Server,
  Network,
  RefreshCw,
  Table2,
  Lock,
  ChevronRight
} from 'lucide-react';
import { apiClient } from '../api/client';

const PROVIDERS = [
  { id: 'postgresql', name: 'PostgreSQL', defaultPort: 5432, desc: 'Compatible with PostgreSQL 12+, AWS RDS, Google Cloud SQL, Supabase' },
  { id: 'mysql', name: 'MySQL', defaultPort: 3306, desc: 'Compatible with MySQL 8+, MariaDB, Google Cloud SQL, AWS Aurora' },
  { id: 'oracle', name: 'Oracle Database', defaultPort: 1521, desc: 'Compatible with Oracle 19c/21c/23ai, Autonomous DB, OCI Cloud' }
];

export default function DatabaseConnectionsModal({
  isOpen,
  onClose,
  onSelectConnectionForQuery,
  activeConnectionId
}) {
  const [connections, setConnections] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [view, setView] = useState('list'); // 'list' or 'new'

  // Form State
  const [provider, setProvider] = useState('postgresql');
  const [name, setName] = useState('');
  const [host, setHost] = useState('');
  const [port, setPort] = useState(5432);
  const [databaseName, setDatabaseName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [sslEnabled, setSslEnabled] = useState(false);
  const [oracleUseSid, setOracleUseSid] = useState(false);

  // Testing & Save State
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Schema Inspection state
  const [inspectingConn, setInspectingConn] = useState(null);
  const [remoteSchema, setRemoteSchema] = useState(null);
  const [isInspecting, setIsInspecting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadConnections();
    }
  }, [isOpen]);

  const loadConnections = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.getConnections();
      setConnections(data);
    } catch (err) {
      console.warn("Could not load connections:", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const handleProviderChange = (pId) => {
    setProvider(pId);
    const p = PROVIDERS.find(item => item.id === pId);
    if (p) setPort(p.defaultPort);
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    if (!host || !databaseName || !username || !password) {
      setTestResult({ success: false, message: "Please fill in Host, Database, Username, and Password." });
      return;
    }

    setIsTesting(true);
    setTestResult(null);
    try {
      const payload = {
        provider,
        name: name || 'Test Connection',
        host: host.trim(),
        port: Number(port),
        database_name: databaseName.trim(),
        username: username.trim(),
        password,
        ssl_enabled: sslEnabled,
        extra_params: provider === 'oracle' ? { use_sid: oracleUseSid } : {}
      };
      const res = await apiClient.testConnection(payload);
      setTestResult(res);
    } catch (err) {
      setTestResult({
        success: false,
        message: err.response?.data?.detail || err.message || "Connection failed."
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveConnection = async (e) => {
    e.preventDefault();
    setSaveError(null);

    if (!name.trim()) {
      setSaveError("Please provide a name for this connection.");
      return;
    }

    setIsSaving(true);
    try {
      const payload = {
        name: name.trim(),
        provider,
        host: host.trim(),
        port: Number(port),
        database_name: databaseName.trim(),
        username: username.trim(),
        password,
        ssl_enabled: sslEnabled,
        extra_params: provider === 'oracle' ? { use_sid: oracleUseSid } : {}
      };
      await apiClient.createConnection(payload);
      await loadConnections();
      setView('list');
      resetForm();
    } catch (err) {
      setSaveError(err.response?.data?.detail || err.message || "Failed to save connection.");
    } finally {
      setIsSaving(false);
    }
  };

  const resetForm = () => {
    setName('');
    setHost('');
    setDatabaseName('');
    setUsername('');
    setPassword('');
    setTestResult(null);
    setSaveError(null);
  };

  const handleDelete = async (connId) => {
    if (!confirm("Are you sure you want to remove this database connection?")) return;
    try {
      await apiClient.deleteConnection(connId);
      setConnections(prev => prev.filter(c => c.id !== connId));
      if (inspectingConn?.id === connId) {
        setInspectingConn(null);
        setRemoteSchema(null);
      }
    } catch (err) {
      alert("Failed to delete connection: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleInspectSchema = async (conn) => {
    setInspectingConn(conn);
    setIsInspecting(true);
    setRemoteSchema(null);
    try {
      const schemaData = await apiClient.getConnectionSchema(conn.id);
      setRemoteSchema(schemaData);
    } catch (err) {
      alert("Failed to inspect schema: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsInspecting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-4xl h-[85vh] rounded-2xl border flex flex-col overflow-hidden shadow-2xl border-slate-800 bg-slate-900 text-slate-100 light:bg-white light:border-slate-200 light:text-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50 shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">Cloud Database Connections</h3>
              <p className="text-xs text-slate-400 light:text-slate-500">
                Connect Oracle, PostgreSQL, or MySQL databases to query live schemas directly in natural language.
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {view === 'list' ? (
              <button
                type="button"
                onClick={() => setView('new')}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-sm transition-all"
              >
                <Plus className="w-4 h-4" />
                <span>Add Connection</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => { setView('list'); resetForm(); }}
                className="px-3 py-1.5 rounded-xl text-xs font-medium text-slate-300 hover:bg-slate-800 light:text-slate-600 light:hover:bg-slate-100 transition-colors"
              >
                Back to Connections
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 light:hover:text-slate-800 light:hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {view === 'new' ? (
            /* Add Connection Form */
            <form onSubmit={handleSaveConnection} className="space-y-5 max-w-2xl mx-auto">
              {/* Provider Selection */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 light:text-slate-700 uppercase tracking-wider">
                  Select Database Provider
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {PROVIDERS.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => handleProviderChange(p.id)}
                      className={`p-3.5 rounded-xl border text-left transition-all ${
                        provider === p.id
                          ? 'border-sky-500 bg-sky-500/10 text-sky-200 light:bg-sky-50 light:border-sky-500 light:text-sky-900 ring-2 ring-sky-500/20'
                          : 'border-slate-800 bg-slate-950/40 hover:border-slate-700 light:border-slate-200 light:bg-white text-slate-400 light:text-slate-600'
                      }`}
                    >
                      <div className="font-semibold text-xs text-slate-100 light:text-slate-900">{p.name}</div>
                      <p className="text-[10px] mt-1 text-slate-400 light:text-slate-500 leading-snug">{p.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Network Guidance Callout */}
              <div className="p-3.5 rounded-xl border border-sky-500/20 bg-sky-950/20 light:bg-sky-50/60 light:border-sky-200 text-xs space-y-1">
                <div className="flex items-center space-x-1.5 font-semibold text-sky-300 light:text-sky-800">
                  <Network className="w-4 h-4" />
                  <span>Cloud Firewall & Connectivity Note</span>
                </div>
                <p className="text-slate-400 light:text-slate-600 text-[11px] leading-relaxed">
                  For Google Cloud SQL, AWS RDS, or Oracle Cloud DBs, ensure your database firewall rules allow incoming connections from your server's IP address.
                </p>
              </div>

              {/* Form Fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2 space-y-1.5">
                  <label className="text-xs font-medium text-slate-300 light:text-slate-700">Connection Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Production Analytics DB"
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300 light:text-slate-700">Host / Endpoint</label>
                  <input
                    type="text"
                    required
                    value={host}
                    onChange={(e) => setHost(e.target.value)}
                    placeholder="e.g. 10.0.0.1 or db.example.com"
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900 font-mono"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300 light:text-slate-700">Port</label>
                  <input
                    type="number"
                    required
                    value={port}
                    onChange={(e) => setPort(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900 font-mono"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300 light:text-slate-700">
                    {provider === 'oracle' ? 'Database Service Name / SID' : 'Database Name'}
                  </label>
                  <input
                    type="text"
                    required
                    value={databaseName}
                    onChange={(e) => setDatabaseName(e.target.value)}
                    placeholder={provider === 'oracle' ? 'e.g. ORCL or XEPDB1' : 'e.g. analytics_db'}
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900 font-mono"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300 light:text-slate-700">Username</label>
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. readonly_user"
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900 font-mono"
                  />
                </div>

                <div className="sm:col-span-2 space-y-1.5">
                  <label className="text-xs font-medium text-slate-300 light:text-slate-700">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="External database password"
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900 font-mono"
                  />
                  <p className="text-[11px] text-slate-500">
                    Passwords are encrypted with Fernet AES-128 before saving and are never exposed via APIs.
                  </p>
                </div>

                <div className="sm:col-span-2 flex items-center space-x-4 pt-1">
                  <label className="flex items-center space-x-2 text-xs text-slate-300 light:text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sslEnabled}
                      onChange={(e) => setSslEnabled(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-800 text-sky-600 focus:ring-sky-500"
                    />
                    <span>Require TLS/SSL Encryption</span>
                  </label>

                  {provider === 'oracle' && (
                    <label className="flex items-center space-x-2 text-xs text-slate-300 light:text-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={oracleUseSid}
                        onChange={(e) => setOracleUseSid(e.target.checked)}
                        className="rounded border-slate-700 bg-slate-800 text-sky-600 focus:ring-sky-500"
                      />
                      <span>Connect using Oracle SID (instead of Service Name)</span>
                    </label>
                  )}
                </div>
              </div>

              {/* Test Result Feedback */}
              {testResult && (
                <div className={`p-3.5 rounded-xl border text-xs flex items-start space-x-2.5 ${
                  testResult.success
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                }`}>
                  {testResult.success ? <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" /> : <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />}
                  <div>
                    <div className="font-semibold">{testResult.success ? 'Connectivity Verified!' : 'Connection Test Failed'}</div>
                    <p className="text-[11px] mt-0.5">{testResult.message}</p>
                    {testResult.duration_ms && <span className="font-mono text-[10px] opacity-75">Response time: {testResult.duration_ms}ms</span>}
                  </div>
                </div>
              )}

              {saveError && (
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{saveError}</span>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800 light:border-slate-200">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={isTesting}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 light:bg-slate-100 light:border-slate-300 light:text-slate-700 light:hover:bg-slate-200 transition-colors disabled:opacity-50"
                >
                  {isTesting ? "Testing..." : "Test Connection"}
                </button>

                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 shadow-md shadow-sky-600/20 active:scale-98 transition-all disabled:opacity-50"
                >
                  {isSaving ? "Saving..." : "Save Connection"}
                </button>
              </div>
            </form>
          ) : (
            /* Connections List */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 light:text-slate-700">
                  Configured Cloud Databases ({connections.length})
                </h4>
              </div>

              {isLoading ? (
                <div className="p-8 text-center text-xs text-slate-500">Loading database connections...</div>
              ) : connections.length === 0 ? (
                <div className="p-8 border rounded-2xl border-slate-800/80 bg-slate-950/20 text-center space-y-3 light:border-slate-200 light:bg-slate-50">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto">
                    <Database className="w-6 h-6" />
                  </div>
                  <h4 className="text-sm font-semibold text-slate-300 light:text-slate-800">No Cloud Databases Connected</h4>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    Add external Oracle, PostgreSQL, or MySQL connections to query your cloud databases directly with plain English.
                  </p>
                  <button
                    type="button"
                    onClick={() => setView('new')}
                    className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-sm"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add First Database Connection</span>
                  </button>
                </div>
              ) : (
                <div className="border rounded-2xl border-slate-800 overflow-hidden light:border-slate-200 divide-y divide-slate-800 light:divide-slate-200">
                  {connections.map((conn) => {
                    const isSelected = activeConnectionId === conn.id;
                    return (
                      <div
                        key={conn.id}
                        className={`p-4 flex flex-wrap items-center justify-between gap-3 transition-colors ${
                          isSelected
                            ? 'bg-sky-500/10 light:bg-sky-50 border-l-4 border-sky-500'
                            : 'bg-slate-900/60 light:bg-white hover:bg-slate-800/40 light:hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="p-2.5 rounded-xl bg-sky-500/10 text-sky-400">
                            <Server className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="font-semibold text-xs text-slate-200 light:text-slate-800">
                                {conn.name}
                              </span>
                              <span className="text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded-full bg-slate-800 text-indigo-400 light:bg-slate-100 border border-slate-700/60 light:border-slate-200">
                                {conn.provider}
                              </span>
                              {conn.ssl_enabled && (
                                <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                  SSL
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-400 light:text-slate-500 font-mono mt-0.5">
                              {conn.username}@{conn.host}:{conn.port}/{conn.database_name}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          <button
                            type="button"
                            onClick={() => handleInspectSchema(conn)}
                            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/80 border border-slate-700 light:bg-slate-100 light:border-slate-300 light:text-slate-700 light:hover:bg-slate-200 transition-colors"
                          >
                            <Table2 className="w-3.5 h-3.5 text-sky-400" />
                            <span>Explore Schema</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => {
                              onSelectConnectionForQuery(conn);
                              onClose();
                            }}
                            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                              isSelected
                                ? 'bg-emerald-600 text-white'
                                : 'bg-sky-600 hover:bg-sky-500 text-white shadow-sm'
                            }`}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>{isSelected ? 'Active Target' : 'Query This DB'}</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleDelete(conn.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 light:hover:bg-slate-100 transition-colors"
                            title="Delete Connection"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Schema Explorer Sub-panel for Cloud Database */}
              {inspectingConn && (
                <div className="border rounded-2xl border-sky-500/30 bg-sky-950/20 light:bg-sky-50/50 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Table2 className="w-4 h-4 text-sky-400" />
                      <h4 className="text-xs font-semibold text-sky-200 light:text-sky-900">
                        Inspecting Remote Schema: {inspectingConn.name} ({inspectingConn.provider.toUpperCase()})
                      </h4>
                    </div>
                    <button
                      type="button"
                      onClick={() => setInspectingConn(null)}
                      className="text-slate-400 hover:text-slate-200 text-xs"
                    >
                      Close
                    </button>
                  </div>

                  {isInspecting ? (
                    <div className="p-6 text-center text-xs text-sky-400 animate-pulse">
                      Retrieving live schema tables and columns from {inspectingConn.host}...
                    </div>
                  ) : remoteSchema ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-60 overflow-y-auto">
                      {remoteSchema.tables.map((t, idx) => (
                        <div key={idx} className="p-3 rounded-xl border border-slate-800 bg-slate-900/80 light:bg-white light:border-slate-200 space-y-1.5">
                          <div className="flex items-center justify-between font-mono text-xs font-semibold text-sky-300 light:text-sky-700">
                            <span>{t.table_name}</span>
                            <span className="text-[10px] text-slate-500">{t.columns.length} cols</span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {t.columns.slice(0, 6).map((c, cIdx) => (
                              <span key={cIdx} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-950 light:bg-slate-100 text-slate-400">
                                {c.name}
                              </span>
                            ))}
                            {t.columns.length > 6 && (
                              <span className="text-[10px] text-slate-500 font-mono">+{t.columns.length - 6} more</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-slate-500">No tables discovered.</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
