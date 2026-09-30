import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, FileText, X } from 'lucide-react';

export default function ChatInput({ onSendMessage, disabled }) {
  const [text, setText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [text]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please select a valid PDF recipe document (.pdf)');
        return;
      }
      setSelectedFile(file);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if ((!text.trim() && !selectedFile) || disabled) return;
    onSendMessage(text.trim(), selectedFile);
    setText('');
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="input-container">
      {selectedFile && (
        <div className="file-preview-badge">
          <div className="file-badge-info">
            <FileText size={16} className="file-icon" />
            <span className="file-name">{selectedFile.name}</span>
            <span className="file-size">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
          </div>
          <button type="button" onClick={removeFile} className="remove-file-btn" title="Remove PDF">
            <X size={14} />
          </button>
        </div>
      )}
      <form onSubmit={handleSubmit} className="input-box">
        <input
          type="file"
          ref={fileInputRef}
          accept=".pdf"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <button
          type="button"
          className="attach-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title="Upload Recipe PDF"
        >
          <Paperclip size={18} />
        </button>
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder={selectedFile ? "Ask a question about this recipe PDF, or press Send..." : "Ask EviBite AI about any food product, allergens, or attach a recipe PDF..."}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={disabled}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={disabled || (!text.trim() && !selectedFile)}
          title="Send message"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
