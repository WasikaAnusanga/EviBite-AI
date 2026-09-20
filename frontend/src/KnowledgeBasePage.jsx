import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Trash2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  ShieldCheck,
  FileCode,
  FileSpreadsheet,
  File,
  X,
  Plus,
} from 'lucide-react';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md', '.csv'];

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(filename) {
  const ext = filename ? filename.substring(filename.lastIndexOf('.')).toLowerCase() : '';
  if (ext === '.pdf') return <FileText className="w-5 h-5 text-rose-600" />;
  if (ext === '.docx') return <FileText className="w-5 h-5 text-blue-600" />;
  if (ext === '.csv') return <FileSpreadsheet className="w-5 h-5 text-emerald-600" />;
  if (ext === '.md' || ext === '.txt') return <FileCode className="w-5 h-5 text-amber-600" />;
  return <File className="w-5 h-5 text-slate-500" />;
}

export default function KnowledgeBasePage({ authToken, onSignOut }) {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [confirmDeleteDoc, setConfirmDeleteDoc] = useState(null);
  const [reindexingId, setReindexingId] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
  }, [authToken]);

  const fetchDocuments = async () => {
    if (!authToken) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch('/api/documents', {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.status === 401) {
        onSignOut();
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      } else {
        setErrorMsg('Failed to load document collection.');
      }
    } catch (err) {
      setErrorMsg('Network error: Unable to connect to backend server.');
    } finally {
      setIsLoading(false);
    }
  };

  const processFileSelected = async (file) => {
    if (!file) return;

    setErrorMsg(null);
    setSuccessMsg(null);

    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setErrorMsg(`Unsupported file type '${ext}'. Supported formats: PDF, DOCX, TXT, MD, CSV.`);
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setErrorMsg(`File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds 10 MB limit.`);
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/documents/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        body: formData,
      });

      if (res.status === 401) {
        onSignOut();
        return;
      }

      const data = await res.json();
      if (res.ok) {
        setSuccessMsg(`Document '${file.name}' uploaded successfully (${data.document?.chunk_count || 0} chunks extracted).`);
        fetchDocuments();
      } else {
        setErrorMsg(data.detail || 'Upload failed.');
      }
    } catch (err) {
      setErrorMsg('Network error while uploading file.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleDelete = async (docId) => {
    if (!authToken || !docId) return;
    setErrorMsg(null);
    try {
      const res = await fetch(`/api/documents/${docId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.status === 401) {
        onSignOut();
        return;
      }
      if (res.ok) {
        setSuccessMsg('Document and indexed chunks removed successfully.');
        setConfirmDeleteDoc(null);
        fetchDocuments();
      } else {
        setErrorMsg('Failed to delete document.');
      }
    } catch (err) {
      setErrorMsg('Network error while deleting document.');
    }
  };

  const handleReindex = async (docId) => {
    if (!authToken || !docId) return;
    setReindexingId(docId);
    setErrorMsg(null);
    try {
      const res = await fetch(`/api/documents/${docId}/reindex`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.status === 401) {
        onSignOut();
        return;
      }
      if (res.ok) {
        setSuccessMsg('Document text re-extracted and re-indexed successfully.');
        fetchDocuments();
      } else {
        setErrorMsg('Reindex failed.');
      }
    } catch (err) {
      setErrorMsg('Network error while reindexing document.');
    } finally {
      setReindexingId(null);
    }
  };

  const readyCount = documents.filter((d) => d.status === 'Ready').length;

  return (
    <div className="flex-1 p-8 overflow-y-auto space-y-6 bg-white">
      {/* HEADER TITLE & DESCRIPTION */}
      <div className="border-b border-slate-100 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-[#1d5c31]">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">My Knowledge Base</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload product guides, allergen sheets, nutrition information or other food documents. EviBite can use these documents as evidence in future chats.
            </p>
          </div>
        </div>
      </div>

      {/* KNOWLEDGE SOURCES STATUS BANNER */}
      <div className="bg-[#f0fdf4] border border-emerald-200 rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-6 h-6 text-emerald-700 shrink-0" />
          <div>
            <h4 className="text-xs font-bold text-emerald-950">Automatic Evidence Integration Active</h4>
            <p className="text-[11px] text-emerald-800">
              Once a document is <strong>Ready</strong>, Agent 2 automatically searches your stored knowledge base during chat queries. You do <em>not</em> need to attach files to individual chat messages.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-white px-3.5 py-2 rounded-xl border border-emerald-300 text-xs font-semibold text-[#1d5c31] shrink-0">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>My Knowledge Base — {readyCount} ready documents</span>
        </div>
      </div>

      {/* NOTIFICATIONS */}
      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-3.5 flex items-center justify-between text-xs text-rose-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-rose-500 hover:text-rose-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-500 hover:text-emerald-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* UPLOAD DRAG & DROP AREA */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition flex flex-col items-center justify-center space-y-3 ${
          isUploading
            ? 'border-emerald-400 bg-emerald-50/50'
            : 'border-slate-300 hover:border-emerald-500 bg-slate-50/50 hover:bg-emerald-50/20'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => processFileSelected(e.target.files[0])}
          accept=".pdf,.docx,.txt,.md,.csv"
          className="hidden"
        />

        <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center text-[#1d5c31]">
          {isUploading ? (
            <RefreshCw className="w-6 h-6 animate-spin text-[#1d5c31]" />
          ) : (
            <UploadCloud className="w-6 h-6" />
          )}
        </div>

        <div>
          <h3 className="text-sm font-bold text-slate-900">
            {isUploading ? 'Extracting text and chunking document...' : 'Click to upload or drag & drop food documents'}
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Supported formats: <strong>PDF, DOCX, TXT, MD, CSV</strong> (Max size: <strong>10 MB</strong>)
          </p>
        </div>

        {!isUploading && (
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 bg-[#1d5c31] hover:bg-[#154524] text-white rounded-xl text-xs font-semibold shadow-sm transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>Select File from Computer</span>
          </button>
        )}
      </div>

      {/* DOCUMENTS LIST */}
      <div className="space-y-4 pt-2">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-900">Your Document Collection</h3>
          <span className="text-xs text-slate-500 font-medium">{documents.length} Total Documents</span>
        </div>

        {isLoading ? (
          <div className="py-12 text-center text-xs text-slate-500 space-y-2">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto text-emerald-600" />
            <p>Loading document collection...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="py-12 border border-slate-200 rounded-2xl text-center space-y-3 bg-slate-50/50">
            <FileText className="w-8 h-8 mx-auto text-slate-400" />
            <div className="space-y-1">
              <p className="text-sm font-bold text-slate-700">No stored documents found</p>
              <p className="text-xs text-slate-500">Upload product specifications or allergen guides to start building your personal knowledge base.</p>
            </div>
          </div>
        ) : (
          <div className="border border-slate-200/90 rounded-2xl overflow-hidden shadow-sm">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3 px-4">Document</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4">Chunks</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        {getFileIcon(doc.original_filename)}
                        <div>
                          <p className="font-bold text-slate-900 truncate max-w-xs">{doc.original_filename}</p>
                          <p className="text-[11px] text-slate-400 font-mono">{doc.document_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-medium">{formatBytes(doc.size_bytes)}</td>
                    <td className="py-3.5 px-4 font-medium">{doc.chunk_count || 0} chunks</td>
                    <td className="py-3.5 px-4 text-slate-500">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="py-3.5 px-4">
                      {doc.status === 'Ready' && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          Ready
                        </span>
                      )}
                      {doc.status === 'Processing' && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 text-[11px] font-bold border border-amber-200">
                          <Clock className="w-3.5 h-3.5 text-amber-600 animate-spin" />
                          Processing
                        </span>
                      )}
                      {doc.status === 'Failed' && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-100 text-rose-800 text-[11px] font-bold border border-rose-200">
                          <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                          Failed
                        </span>
                      )}
                      {doc.status === 'No extractable text' && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 text-[11px] font-bold border border-slate-300">
                          <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
                          No text
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleReindex(doc.document_id)}
                          disabled={reindexingId === doc.document_id}
                          className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600 transition"
                          title="Re-extract text and rebuild chunks"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 ${reindexingId === doc.document_id ? 'animate-spin text-emerald-600' : ''}`} />
                        </button>
                        <button
                          onClick={() => setConfirmDeleteDoc(doc)}
                          className="p-1.5 rounded-lg border border-rose-200 hover:bg-rose-50 text-rose-600 transition"
                          title="Delete document and remove chunks"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* DELETE CONFIRMATION MODAL */}
      {confirmDeleteDoc && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full space-y-4 shadow-xl border border-slate-200">
            <div className="flex items-start justify-between">
              <div className="w-10 h-10 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <button onClick={() => setConfirmDeleteDoc(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Delete Document</h3>
              <p className="text-xs text-slate-600 mt-1">
                Are you sure you want to delete <strong>{confirmDeleteDoc.original_filename}</strong>? All extracted text chunks and cached search indexes will be permanently removed.
              </p>
            </div>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setConfirmDeleteDoc(null)}
                className="px-4 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDeleteDoc.document_id)}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-sm transition"
              >
                Delete Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
