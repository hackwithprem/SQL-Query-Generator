import React, { useState, useRef, useEffect } from 'react';
import { 
  X, 
  UploadCloud, 
  FileSpreadsheet, 
  Table2, 
  Trash2, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles, 
  Eye, 
  ArrowRight,
  Database,
  Layers,
  FileCheck,
  Edit2,
  Save
} from 'lucide-react';
import { apiClient } from '../api/client';

export default function UploadDataModal({
  isOpen,
  onClose,
  onSelectDatasetForQuery,
  activeDatasetId
}) {
  const [files, setFiles] = useState([]);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [customSheetName, setCustomSheetName] = useState('');

  // Inline rename state: { [fileId]: string }
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');

  // Preview state
  const [previewData, setPreviewData] = useState(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      loadFiles();
    }
  }, [isOpen]);

  const loadFiles = async () => {
    setIsLoadingList(true);
    try {
      const data = await apiClient.getFiles();
      setFiles(data);
    } catch (err) {
      console.warn("Could not load uploaded files:", err);
    } finally {
      setIsLoadingList(false);
    }
  };

  if (!isOpen) return null;

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    setUploadError(null);
    setUploadSuccess(null);

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      setUploadError("Invalid file type. Only CSV (.csv) and Excel (.xlsx, .xls) files are supported.");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setUploadError("File size exceeds 15MB limit. Please upload a smaller file.");
      return;
    }

    setIsUploading(true);
    try {
      const sheet = customSheetName.trim() || null;
      const res = await apiClient.uploadData(file, sheet);
      setUploadSuccess(`"${file.name}" uploaded and parsed into table '${res.table_name}' (${res.row_count} rows)!`);
      setCustomSheetName('');
      loadFiles();
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Upload failed.";
      setUploadError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (fileId) => {
    if (!confirm("Are you sure you want to remove this dataset?")) return;
    try {
      await apiClient.deleteFile(fileId);
      setFiles(prev => prev.filter(f => f.id !== fileId));
      if (previewData?.dataset?.id === fileId) {
        setPreviewData(null);
      }
    } catch (err) {
      alert("Failed to delete dataset: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleStartRename = (file) => {
    setRenamingId(file.id);
    setRenameValue(file.original_filename);
  };

  const handleSaveRename = async (fileId) => {
    if (!renameValue.trim()) return;
    try {
      await apiClient.renameDataset(fileId, renameValue.trim());
      setFiles(prev => prev.map(f => f.id === fileId ? { ...f, original_filename: renameValue.trim() } : f));
      setRenamingId(null);
    } catch (err) {
      alert("Failed to rename dataset: " + (err.response?.data?.detail || err.message));
    }
  };

  const handlePreview = async (fileId) => {
    setIsPreviewLoading(true);
    try {
      const data = await apiClient.getFilePreview(fileId);
      setPreviewData(data);
    } catch (err) {
      alert("Failed to load preview: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsPreviewLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-4xl h-[85vh] rounded-2xl border flex flex-col overflow-hidden shadow-2xl border-slate-800 bg-slate-900 text-slate-100 light:bg-white light:border-slate-200 light:text-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-4 border-b flex items-center justify-between border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50 shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">Upload Data (CSV / Excel)</h3>
              <p className="text-xs text-slate-400 light:text-slate-500">
                Upload your spreadsheets to create private, isolated SQL tables queryable in natural English.
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

        {/* Scrollable Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Drag and Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center transition-all cursor-pointer ${
              isDragging 
                ? 'border-sky-500 bg-sky-500/10 light:bg-sky-50' 
                : 'border-slate-700/80 bg-slate-950/40 hover:border-slate-600 light:border-slate-300 light:bg-slate-50/50'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv, .xlsx, .xls"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div className="w-12 h-12 rounded-2xl bg-sky-500/10 text-sky-400 flex items-center justify-center mb-3">
              <UploadCloud className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-slate-200 light:text-slate-800">
              Drag & Drop your CSV or Excel file here
            </h4>
            <p className="text-xs text-slate-400 light:text-slate-500 mt-1">
              or click to browse your computer
            </p>
            <div className="mt-3 flex items-center space-x-2 text-[11px] text-slate-500">
              <span className="px-2 py-0.5 rounded bg-slate-800 light:bg-slate-200 text-slate-300 light:text-slate-700 font-mono">.csv</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 light:bg-slate-200 text-slate-300 light:text-slate-700 font-mono">.xlsx</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 light:bg-slate-200 text-slate-300 light:text-slate-700 font-mono">.xls</span>
              <span>&bull; Up to 15MB</span>
            </div>
          </div>

          {/* Optional Excel Worksheet Selector */}
          <div className="flex items-center space-x-3 p-3 rounded-xl bg-slate-950/30 border border-slate-800 light:bg-slate-50 light:border-slate-200 text-xs">
            <span className="text-slate-400 light:text-slate-600 font-medium whitespace-nowrap">
              Excel Sheet Name (Optional):
            </span>
            <input
              type="text"
              value={customSheetName}
              onChange={(e) => setCustomSheetName(e.target.value)}
              placeholder="e.g. Sales2026 (Leave blank for default first sheet)"
              className="flex-1 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-100 outline-none text-xs focus:border-sky-500 light:bg-white light:border-slate-300 light:text-slate-900"
            />
          </div>

          {/* Upload Status Alerts */}
          {isUploading && (
            <div className="p-3.5 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs flex items-center space-x-2 animate-pulse">
              <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
              <span>Parsing spreadsheet, normalizing column names, and building isolated database table...</span>
            </div>
          )}

          {uploadError && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {uploadSuccess && (
            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{uploadSuccess}</span>
            </div>
          )}

          {/* Uploaded Datasets Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 light:text-slate-700">
                Your Uploaded Datasets ({files.length})
              </h4>
            </div>

            {isLoadingList ? (
              <div className="p-8 text-center text-xs text-slate-500">Loading datasets...</div>
            ) : files.length === 0 ? (
              <div className="p-8 border rounded-xl border-slate-800/80 bg-slate-950/20 text-center text-xs text-slate-500 light:border-slate-200 light:bg-slate-50">
                No datasets uploaded yet. Upload a CSV or Excel file to get started!
              </div>
            ) : (
              <div className="border rounded-xl border-slate-800 overflow-hidden light:border-slate-200 divide-y divide-slate-800 light:divide-slate-200">
                {files.map((file) => {
                  const isSelected = activeDatasetId === file.id;
                  const isRenaming = renamingId === file.id;
                  return (
                    <div 
                      key={file.id}
                      className={`p-4 flex flex-wrap items-center justify-between gap-3 transition-colors ${
                        isSelected 
                          ? 'bg-sky-500/10 light:bg-sky-50 border-l-4 border-sky-500' 
                          : 'bg-slate-900/60 light:bg-white hover:bg-slate-800/40 light:hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
                          <FileSpreadsheet className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            {isRenaming ? (
                              <div className="flex items-center space-x-1.5">
                                <input
                                  type="text"
                                  value={renameValue}
                                  onChange={(e) => setRenameValue(e.target.value)}
                                  className="px-2 py-0.5 text-xs rounded bg-slate-800 border border-slate-700 text-slate-100 outline-none light:bg-white light:border-slate-300 light:text-slate-900"
                                />
                                <button
                                  type="button"
                                  onClick={() => handleSaveRename(file.id)}
                                  className="p-1 rounded bg-sky-600 text-white hover:bg-sky-500"
                                  title="Save Rename"
                                >
                                  <Save className="w-3 h-3" />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setRenamingId(null)}
                                  className="p-1 rounded text-slate-400 hover:bg-slate-800"
                                  title="Cancel"
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </div>
                            ) : (
                              <div className="flex items-center space-x-1.5">
                                <span className="font-semibold text-xs text-slate-200 light:text-slate-800">
                                  {file.original_filename}
                                </span>
                                <button
                                  type="button"
                                  onClick={() => handleStartRename(file)}
                                  className="text-slate-400 hover:text-sky-400"
                                  title="Rename Dataset"
                                >
                                  <Edit2 className="w-3 h-3" />
                                </button>
                              </div>
                            )}
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-sky-400 light:bg-slate-100 border border-slate-700/60 light:border-slate-200">
                              Table: {file.table_name}
                            </span>
                            {file.sheet_name && (
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-900/60 text-indigo-300 light:bg-indigo-50 border border-indigo-700/50 light:border-indigo-200">
                                Sheet: {file.sheet_name}
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-400 light:text-slate-500 mt-0.5">
                            {file.row_count.toLocaleString()} rows &bull; {file.column_count} columns &bull; {(file.file_size_bytes / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={() => handlePreview(file.id)}
                          className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/80 border border-slate-700 light:bg-slate-100 light:border-slate-300 light:text-slate-700 light:hover:bg-slate-200 transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Preview</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            onSelectDatasetForQuery(file);
                            onClose();
                          }}
                          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                            isSelected
                              ? 'bg-emerald-600 text-white'
                              : 'bg-sky-600 hover:bg-sky-500 text-white shadow-sm'
                          }`}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>{isSelected ? 'Active Query Target' : 'Query This Data'}</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleDelete(file.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 light:hover:bg-slate-100 transition-colors"
                          title="Delete Dataset"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Preview Panel if active */}
          {previewData && (
            <div className="border rounded-2xl border-indigo-500/30 bg-indigo-950/20 light:bg-indigo-50/40 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Table2 className="w-4 h-4 text-indigo-400" />
                  <h4 className="text-xs font-semibold text-indigo-200 light:text-indigo-900">
                    Preview: {previewData.dataset.original_filename} (Table: <code className="text-sky-300">{previewData.dataset.table_name}</code>)
                  </h4>
                </div>
                <button
                  type="button"
                  onClick={() => setPreviewData(null)}
                  className="text-slate-400 hover:text-slate-200 text-xs"
                >
                  Close Preview
                </button>
              </div>

              {/* Inferred Column Types */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {previewData.dataset.columns.map((c, idx) => (
                  <span 
                    key={idx}
                    className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-900 border border-slate-700/80 text-slate-300 light:bg-white light:border-slate-300 light:text-slate-700"
                  >
                    {c.name}: <span className="text-sky-400 font-semibold">{c.type}</span>
                  </span>
                ))}
              </div>

              {/* Sample Rows Table */}
              <div className="overflow-x-auto rounded-xl border border-slate-800 light:border-slate-200 bg-slate-950/40 light:bg-white">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-slate-100 text-[11px] font-mono text-slate-400">
                      {previewData.dataset.columns.map((c, idx) => (
                        <th key={idx} className="py-2 px-3 font-medium">{c.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 light:divide-slate-200">
                    {previewData.sample_rows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-800/30 light:hover:bg-slate-50 font-mono text-[11px]">
                        {previewData.dataset.columns.map((c, cIdx) => (
                          <td key={cIdx} className="py-1.5 px-3 whitespace-nowrap text-slate-300 light:text-slate-800">
                            {row[c.name] === null ? <span className="italic text-slate-600">NULL</span> : String(row[c.name])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
