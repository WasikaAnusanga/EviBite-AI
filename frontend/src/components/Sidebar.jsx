import React from 'react';
import { Plus, MessageSquare, ShieldCheck, Sparkles, Cpu } from 'lucide-react';

export default function Sidebar({ sessions, currentSessionId, onNewChat, onSelectSession }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-logo">
          <div className="brand-icon">
            <Sparkles size={18} />
          </div>
          <span>EviBite AI</span>
        </div>
      </div>

      <button className="new-chat-btn" onClick={onNewChat}>
        <Plus size={18} />
        <span>New Chat</span>
      </button>

      <div className="sidebar-nav">
        <div className="nav-section-title">Recent Chats</div>
        {sessions.length === 0 ? (
          <div className="session-item text-dim" style={{ fontSize: '0.8rem', fontStyle: 'italic' }}>
            No chat history yet
          </div>
        ) : (
          sessions.map((sess) => (
            <div
              key={sess.id}
              className={`session-item ${sess.id === currentSessionId ? 'active' : ''}`}
              onClick={() => onSelectSession(sess.id)}
            >
              <MessageSquare size={15} />
              <span>{sess.title || 'Untitled Session'}</span>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <div className="model-badge">
          <div className="status-dot" />
          <Cpu size={14} />
          <span>Gemini 3.1 Flash-Lite</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#9ca3af', padding: '0 4px' }}>
          <ShieldCheck size={14} color="#10b981" />
          <span>Multi-Agent Triage Active</span>
        </div>
      </div>
    </aside>
  );
}
