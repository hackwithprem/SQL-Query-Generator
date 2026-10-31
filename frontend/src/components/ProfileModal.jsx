import React, { useState } from 'react';
import { X, User, Mail, Calendar, ShieldCheck, LogOut, CheckCircle2, Edit2, Save, Loader2 } from 'lucide-react';
import { apiClient } from '../api/client';

export default function ProfileModal({
  isOpen,
  onClose,
  currentUser,
  onSignOut,
  onProfileUpdated
}) {
  if (!isOpen || !currentUser) return null;

  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState(currentUser.full_name || '');
  const [isSaving, setIsSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const initials = currentUser.full_name
    ? currentUser.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  const memberSince = currentUser.created_at
    ? new Date(currentUser.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    : 'Active Member';

  const handleSaveName = async (e) => {
    e.preventDefault();
    if (!displayName.trim()) return;
    setIsSaving(true);
    setStatusMsg(null);
    try {
      const updated = await apiClient.updateProfile(displayName.trim());
      if (onProfileUpdated) {
        onProfileUpdated(updated);
      }
      setIsEditing(false);
      setStatusMsg('Profile updated successfully!');
      setTimeout(() => setStatusMsg(null), 3000);
    } catch (err) {
      setStatusMsg('Failed to update name: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsSaving(false);
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
              <User className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100 light:text-slate-900">User Profile</h3>
              <p className="text-xs text-slate-400 light:text-slate-500">
                Your authenticated account details
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
        <div className="p-6 space-y-6">
          {statusMsg && (
            <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs">
              {statusMsg}
            </div>
          )}

          {/* User Hero Banner */}
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-sky-500/20 shrink-0">
              {initials}
            </div>
            <div className="space-y-1 min-w-0 flex-1">
              {isEditing ? (
                <form onSubmit={handleSaveName} className="flex items-center space-x-2">
                  <input
                    type="text"
                    required
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="w-full px-2.5 py-1 text-xs rounded-lg bg-slate-800 border border-slate-700 text-slate-100 focus:border-sky-500 outline-none light:bg-slate-50 light:border-slate-300 light:text-slate-900"
                  />
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="p-1.5 rounded-lg bg-sky-600 text-white hover:bg-sky-500"
                    title="Save Name"
                  >
                    {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setIsEditing(false); setDisplayName(currentUser.full_name || ''); }}
                    className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-800"
                    title="Cancel"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </form>
              ) : (
                <div className="flex items-center space-x-2">
                  <h4 className="text-base font-bold text-slate-100 light:text-slate-900 truncate">
                    {currentUser.full_name || 'User'}
                  </h4>
                  <button
                    type="button"
                    onClick={() => setIsEditing(true)}
                    className="text-slate-400 hover:text-sky-400"
                    title="Edit Name"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
              <p className="text-xs text-slate-400 light:text-slate-500 flex items-center space-x-1 truncate">
                <Mail className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{currentUser.email}</span>
              </p>
              <div className="flex items-center space-x-1.5 pt-0.5">
                <span className="inline-flex items-center space-x-1 text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Verified User</span>
                </span>
              </div>
            </div>
          </div>

          {/* Details Card */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/40 light:bg-slate-50 light:border-slate-200 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 light:text-slate-500 flex items-center space-x-1.5">
                <Calendar className="w-3.5 h-3.5" />
                <span>Member Since</span>
              </span>
              <span className="font-medium text-slate-200 light:text-slate-700">
                {memberSince}
              </span>
            </div>

            <div className="flex items-center justify-between border-t border-slate-800/50 light:border-slate-200/80 pt-2.5">
              <span className="text-slate-400 light:text-slate-500 flex items-center space-x-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Session Security</span>
              </span>
              <span className="font-medium text-slate-200 light:text-slate-700">
                Supabase / JWT Protected
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="pt-2 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-xl text-xs font-semibold border border-slate-700/80 hover:bg-slate-800/80 text-slate-300 light:border-slate-300 light:hover:bg-slate-100 light:text-slate-700 transition-colors"
            >
              Close
            </button>
            <button
              type="button"
              onClick={() => {
                onClose();
                onSignOut();
              }}
              className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-sm transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Log Out</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
