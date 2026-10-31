import React, { useState } from 'react';
import { 
  X, 
  Key, 
  ExternalLink, 
  CheckCircle2, 
  AlertTriangle, 
  Terminal, 
  HelpCircle, 
  RefreshCw, 
  Copy, 
  Check,
  Cpu,
  ShieldAlert
} from 'lucide-react';
import { apiClient } from '../api/client';

export default function ApiSetupGuideModal({
  isOpen,
  onClose,
  health,
  onRefreshHealth
}) {
  const [copiedSnippet, setCopiedSnippet] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyStatus, setVerifyStatus] = useState(null);

  if (!isOpen) return null;

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedSnippet(key);
    setTimeout(() => setCopiedSnippet(null), 2500);
  };

  const handleTestHealth = async () => {
    setIsVerifying(true);
    setVerifyStatus(null);
    try {
      const data = await apiClient.getHealth();
      if (onRefreshHealth) onRefreshHealth();
      setVerifyStatus({
        success: data?.status === 'healthy',
        provider: data?.ai_provider?.provider,
        is_configured: data?.ai_provider?.is_configured,
        configured_type: data?.ai_provider?.configured_provider
      });
    } catch (err) {
      setVerifyStatus({
        success: false,
        message: err.message || "Failed to reach backend."
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const groqSnippet = `# LLM Provider Configuration in backend/.env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile`;

  const geminiSnippet = `# LLM Provider Configuration in backend/.env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy_your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-4xl h-[88vh] rounded-2xl border flex flex-col overflow-hidden shadow-2xl border-slate-800 bg-slate-900 text-slate-100 light:bg-white light:border-slate-200 light:text-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50 shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">API Key Setup & Provider Guide</h3>
              <p className="text-xs text-slate-400 light:text-slate-500">
                Step-by-step instructions to configure live Groq or Google Gemini generative AI engines.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 light:hover:text-slate-800 light:hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Current AI Engine Status Banner */}
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950/40 light:bg-slate-50 light:border-slate-200 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-sky-500/10 text-sky-400">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[11px] font-semibold uppercase text-slate-400 tracking-wider">Current Engine Status</span>
                <div className="text-sm font-semibold text-slate-200 light:text-slate-800 flex items-center space-x-2 mt-0.5">
                  <span>{health?.ai_provider?.provider || "Local Pattern Engine"}</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleTestHealth}
              disabled={isVerifying}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-200 light:bg-white light:border-slate-300 light:text-slate-700 light:hover:bg-slate-100 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${isVerifying ? 'animate-spin' : ''}`} />
              <span>{isVerifying ? "Checking Health..." : "Verify AI Provider Health"}</span>
            </button>
          </div>

          {verifyStatus && (
            <div className={`p-3.5 rounded-xl border text-xs flex items-center space-x-2 ${
              verifyStatus.success
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
            }`}>
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>
                Backend Status: Healthy &bull; Active Provider: <strong>{verifyStatus.provider}</strong>
              </span>
            </div>
          )}

          {/* Security Alert Callout */}
          <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-300 text-xs flex items-start space-x-3">
            <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5 text-amber-400" />
            <div className="space-y-1">
              <span className="font-semibold text-amber-200 light:text-amber-900">Security Best Practice</span>
              <p className="text-[11px] text-amber-300/90 light:text-amber-800 leading-relaxed">
                Never paste private API keys into an ordinary public chat or client browser code. Keys should reside securely in the backend <code className="bg-amber-950/40 px-1.5 py-0.5 rounded font-mono">backend/.env</code> file or Google Cloud Secret Manager.
              </p>
            </div>
          </div>

          {/* Primary Walkthrough: Groq */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <span className="w-6 h-6 rounded-full bg-sky-600 text-white font-bold flex items-center justify-center text-xs">
                1
              </span>
              <h4 className="text-sm font-semibold text-slate-100 light:text-slate-900">
                Primary Option: Groq Cloud API Setup (Recommended)
              </h4>
            </div>

            <div className="ml-8 space-y-4">
              <ol className="space-y-3 text-xs text-slate-300 light:text-slate-700">
                <li className="flex items-start space-x-2">
                  <span className="font-bold text-sky-400">Step 1:</span>
                  <span>
                    Open the official Groq developer console:{' '}
                    <a
                      href="https://console.groq.com/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sky-400 hover:text-sky-300 inline-flex items-center space-x-1 font-semibold underline"
                    >
                      <span>https://console.groq.com/</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </span>
                </li>

                <li className="flex items-start space-x-2">
                  <span className="font-bold text-sky-400">Step 2:</span>
                  <span>Sign in or create a free developer account using Google or GitHub.</span>
                </li>

                <li className="flex items-start space-x-2">
                  <span className="font-bold text-sky-400">Step 3:</span>
                  <span>Navigate to <strong>API Keys</strong> in the left sidebar navigation menu.</span>
                </li>

                <li className="flex items-start space-x-2">
                  <span className="font-bold text-sky-400">Step 4:</span>
                  <span>Click <strong>Create API Key</strong>, assign a name (e.g. <em>SQL-Query-Generator</em>), and click Submit.</span>
                </li>

                <li className="flex items-start space-x-2">
                  <span className="font-bold text-sky-400">Step 5:</span>
                  <span>Copy the generated key immediately (it begins with <code className="font-mono text-sky-300">gsk_...</code>).</span>
                </li>

                <li className="flex items-start space-x-2">
                  <span className="font-bold text-sky-400">Step 6:</span>
                  <span>
                    Open or create your <code className="font-mono px-1.5 py-0.5 rounded bg-slate-800 light:bg-slate-200 text-sky-300 light:text-sky-800">backend/.env</code> file and configure:
                  </span>
                </li>
              </ol>

              {/* Code snippet */}
              <div className="relative rounded-xl border border-slate-800 bg-slate-950 p-3.5 font-mono text-xs text-emerald-400 light:bg-slate-900 overflow-x-auto">
                <button
                  type="button"
                  onClick={() => copyToClipboard(groqSnippet, 'groq')}
                  className="absolute right-3 top-3 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 light:bg-slate-800 light:text-slate-300 transition-colors"
                  title="Copy snippet"
                >
                  {copiedSnippet === 'groq' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
                <pre>{groqSnippet}</pre>
              </div>

              <div className="space-y-1 text-xs text-slate-300 light:text-slate-700">
                <span className="font-bold text-sky-400">Step 7:</span> Restart the FastAPI backend server to load the new environment variables.
              </div>
            </div>
          </div>

          {/* Alternative Walkthrough: Google Gemini */}
          <div className="space-y-3 pt-3 border-t border-slate-800 light:border-slate-200">
            <div className="flex items-center space-x-2">
              <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center text-xs">
                2
              </span>
              <h4 className="text-sm font-semibold text-slate-100 light:text-slate-900">
                Alternative Option: Google Gemini API Setup
              </h4>
            </div>

            <div className="ml-8 space-y-4">
              <ol className="space-y-2.5 text-xs text-slate-300 light:text-slate-700">
                <li className="flex items-start space-x-2">
                  <span className="font-bold text-indigo-400">Step 1:</span>
                  <span>
                    Open Google AI Studio:{' '}
                    <a
                      href="https://aistudio.google.com/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sky-400 hover:text-sky-300 inline-flex items-center space-x-1 font-semibold underline"
                    >
                      <span>https://aistudio.google.com/</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </span>
                </li>

                <li className="flex items-start space-x-2">
                  <span className="font-bold text-indigo-400">Step 2:</span>
                  <span>Click <strong>Get API Key</strong> and create an API key in a new or existing Google Cloud project.</span>
                </li>

                <li className="flex items-start space-x-2">
                  <span className="font-bold text-indigo-400">Step 3:</span>
                  <span>Configure your <code className="font-mono px-1.5 py-0.5 rounded bg-slate-800 light:bg-slate-200 text-sky-300 light:text-sky-800">backend/.env</code> with:</span>
                </li>
              </ol>

              {/* Gemini Snippet */}
              <div className="relative rounded-xl border border-slate-800 bg-slate-950 p-3.5 font-mono text-xs text-indigo-300 light:bg-slate-900 overflow-x-auto">
                <button
                  type="button"
                  onClick={() => copyToClipboard(geminiSnippet, 'gemini')}
                  className="absolute right-3 top-3 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 light:bg-slate-800 light:text-slate-300 transition-colors"
                  title="Copy snippet"
                >
                  {copiedSnippet === 'gemini' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
                <pre>{geminiSnippet}</pre>
              </div>
            </div>
          </div>

          {/* Troubleshooting Table */}
          <div className="space-y-3 pt-3 border-t border-slate-800 light:border-slate-200">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 light:text-slate-700">
              Troubleshooting Common Errors
            </h4>
            <div className="border rounded-xl border-slate-800 overflow-hidden light:border-slate-200 text-xs">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-950/60 light:bg-slate-100 border-b border-slate-800 light:border-slate-200 text-slate-400 light:text-slate-600 font-mono text-[11px]">
                  <tr>
                    <th className="py-2 px-3 w-1/3">Issue / Error</th>
                    <th className="py-2 px-3">Root Cause & Resolution</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 light:divide-slate-200 text-slate-300 light:text-slate-700">
                  <tr>
                    <td className="py-2.5 px-3 font-mono text-rose-400">Missing API Key / Offline Mode</td>
                    <td className="py-2.5 px-3">
                      Verify that <code className="bg-slate-800 px-1 rounded text-sky-300">GROQ_API_KEY</code> has been added to <code className="bg-slate-800 px-1 rounded text-sky-300">backend/.env</code> and is not blank.
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-mono text-rose-400">Invalid API Key (401)</td>
                    <td className="py-2.5 px-3">
                      Check for leading/trailing spaces or quotes in the key. Re-generate a fresh key from the console.
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-mono text-amber-400">Rate Limit Exceeded (429)</td>
                    <td className="py-2.5 px-3">
                      Wait 60 seconds before submitting further queries, or switch between Groq and Gemini.
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-mono text-rose-400">Changes Not Applying</td>
                    <td className="py-2.5 px-3">
                      The FastAPI server process must be restarted whenever changes are made to <code className="bg-slate-800 px-1 rounded text-sky-300">.env</code>.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
