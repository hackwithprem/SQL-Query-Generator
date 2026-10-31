import React, { useState } from 'react';
import { 
  X, 
  Lock, 
  Mail, 
  User as UserIcon, 
  Eye, 
  EyeOff, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { apiClient } from '../api/client';

export default function AuthModal({
  isOpen,
  onClose,
  onAuthSuccess,
  initialMode = 'signin'
}) {
  const [mode, setMode] = useState(initialMode); // 'signin' or 'signup'
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(true);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  if (!isOpen) return null;

  const handleDemoFill = () => {
    setEmail('demo@example.com');
    setPassword('DemoUser123!');
    setMode('signin');
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (mode === 'signup') {
      if (!fullName.trim()) {
        setError('Please enter your full name.');
        return;
      }
      if (password.length < 8) {
        setError('Password must be at least 8 characters long.');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return;
      }
      if (!acceptTerms) {
        setError('Please accept the Terms of Service to continue.');
        return;
      }
    }

    setIsLoading(true);
    try {
      if (mode === 'signup') {
        const res = await apiClient.signup(fullName.trim(), email.trim(), password);
        setSuccessMsg('Account created successfully!');
        setTimeout(() => {
          onAuthSuccess(res.user);
          onClose();
        }, 600);
      } else {
        const res = await apiClient.login(email.trim(), password);
        setSuccessMsg('Signed in successfully!');
        setTimeout(() => {
          onAuthSuccess(res.user);
          onClose();
        }, 600);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Authentication failed.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-md rounded-2xl border flex flex-col overflow-hidden shadow-2xl border-slate-800 bg-slate-900 text-slate-100 light:bg-white light:border-slate-200 light:text-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 border-b flex items-center justify-between border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">
                {mode === 'signin' ? 'Sign In to Your Workspace' : 'Create an Account'}
              </h3>
              <p className="text-xs text-slate-400 light:text-slate-500">
                {mode === 'signin' 
                  ? 'Access your private datasets and query history' 
                  : 'Start generating SQL and connecting cloud databases'}
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

        {/* Tab switcher */}
        <div className="grid grid-cols-2 p-2 border-b border-slate-800 bg-slate-950/40 light:border-slate-200 light:bg-slate-100/60 text-xs font-medium">
          <button
            type="button"
            onClick={() => { setMode('signin'); setError(null); }}
            className={`py-2 rounded-lg text-center transition-all ${
              mode === 'signin'
                ? 'bg-sky-600 text-white shadow-sm font-semibold'
                : 'text-slate-400 hover:text-slate-200 light:text-slate-600 light:hover:text-slate-900'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setMode('signup'); setError(null); }}
            className={`py-2 rounded-lg text-center transition-all ${
              mode === 'signup'
                ? 'bg-sky-600 text-white shadow-sm font-semibold'
                : 'text-slate-400 hover:text-slate-200 light:text-slate-600 light:hover:text-slate-900'
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Content & Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {mode === 'signup' && (
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 light:text-slate-700">
                Full Name
              </label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Alex Morgan"
                  className="w-full pl-9 pr-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900"
                />
              </div>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300 light:text-slate-700">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full pl-9 pr-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300 light:text-slate-700">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === 'signup' ? 'Minimum 8 characters' : 'Enter your password'}
                className="w-full pl-9 pr-9 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {mode === 'signup' && (
            <>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300 light:text-slate-700">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat password"
                    className="w-full pl-9 pr-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-slate-50 light:border-slate-300 light:text-slate-900 font-mono"
                  />
                </div>
              </div>

              <label className="flex items-center space-x-2 text-xs text-slate-400 light:text-slate-600 pt-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={acceptTerms}
                  onChange={(e) => setAcceptTerms(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-sky-600 focus:ring-sky-500"
                />
                <span>I accept the Workspace Terms and Data Isolation Policy</span>
              </label>
            </>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 shadow-md shadow-sky-600/20 active:scale-98 transition-all disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <span>{mode === 'signin' ? 'Sign In to Workspace' : 'Complete Registration'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          {/* Quick Demo Credentials */}
          {mode === 'signin' && (
            <div className="pt-2 text-center">
              <button
                type="button"
                onClick={handleDemoFill}
                className="text-xs text-sky-400 hover:text-sky-300 underline font-medium"
              >
            
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
