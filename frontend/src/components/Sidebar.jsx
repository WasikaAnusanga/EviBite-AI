import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Plus, MessageSquare, ShieldCheck, Sparkles, Settings, LogOut, 
  ChevronRight, ChevronUp, User, Sliders, HelpCircle, LogIn, UserPlus 
} from 'lucide-react';

import logoImg from '../logo/logo.png';

export default function Sidebar({
  sessions,
  currentSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  user,
  onSignOut,
  onOpenSettings,
  onOpenHelp,
}) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <aside className="sidebar">
      {/* Top Header & Brand */}
      <div className="sidebar-header">
        <Link to="/" className="brand-logo" style={{ textDecoration: 'none', cursor: 'pointer' }}>
          <img src={logoImg} alt="EviBite AI Logo" className="sidebar-logo-img" />
          <span>EviBite AI</span>
        </Link>
      </div>

      {/* New Chat Button */}
      <button className="new-chat-btn" onClick={onNewChat}>
        <Plus size={18} />
        <span>New Chat</span>
      </button>

      {/* Recent Chats Navigation */}
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
              <MessageSquare size={15} style={{ flexShrink: 0 }} />
              <span className="session-title-text">{sess.title || 'Untitled Session'}</span>
              {onDeleteSession && (
                <button
                  className="delete-session-btn"
                  title="Delete conversation"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(sess.id);
                  }}
                >
                  &times;
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* Bottom Left Corner User Profile & Popup Menu */}
      <div className="sidebar-user-container" ref={menuRef}>
        {/* Popup Menu (Appears above the user profile bar when clicked) */}
        {isMenuOpen && user && (
          <div className="profile-popup-menu">
            {/* Top User Card inside popup */}
            <div className="popup-user-card">
              <div className="popup-avatar">
                {getInitials(user.name)}
              </div>
              <div className="popup-user-details">
                <span className="popup-user-name">{user.name}</span>
                <span className="popup-plan-tag">Plus</span>
              </div>
            </div>

            <div className="popup-menu-divider" />

            <button className="popup-menu-item" onClick={() => { setIsMenuOpen(false); if (onOpenSettings) onOpenSettings('general'); }}>
              <Sparkles size={16} />
              <span>Upgrade plan</span>
            </button>

            <button className="popup-menu-item" onClick={() => { setIsMenuOpen(false); if (onOpenSettings) onOpenSettings('allergens'); }}>
              <Sliders size={16} />
              <span>Personalization</span>
            </button>

            <button className="popup-menu-item" onClick={() => { setIsMenuOpen(false); if (onOpenSettings) onOpenSettings('account'); }}>
              <User size={16} />
              <span>Profile</span>
            </button>

            <button className="popup-menu-item" onClick={() => { setIsMenuOpen(false); if (onOpenSettings) onOpenSettings('general'); }}>
              <Settings size={16} />
              <span>Settings</span>
            </button>

            <div className="popup-menu-divider" />

            <button className="popup-menu-item" onClick={() => { setIsMenuOpen(false); if (onOpenHelp) onOpenHelp(); }}>
              <HelpCircle size={16} />
              <span>Help</span>
              <ChevronRight size={14} className="right-arrow" />
            </button>

            <button className="popup-menu-item text-danger" onClick={() => { setIsMenuOpen(false); onSignOut(); }}>
              <LogOut size={16} />
              <span>Log out</span>
              <ChevronRight size={14} className="right-arrow" />
            </button>
          </div>
        )}

        {/* User Profile Bar at Bottom Left Corner */}
        {user ? (
          <button
            className={`sidebar-user-profile-bar ${isMenuOpen ? 'active' : ''}`}
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <div className="user-avatar-circle">
              {getInitials(user.name)}
            </div>
            <div className="user-profile-text">
              <span className="user-profile-name">{user.name}</span>
              <span className="user-profile-sub">Plus</span>
            </div>
            <ChevronRight size={16} className={`user-bar-chevron ${isMenuOpen ? 'open' : ''}`} />
          </button>
        ) : (
          <div className="sidebar-logged-out-box">
            <Link to="/login" className="sidebar-auth-btn signin">
              <LogIn size={16} />
              <span>Sign In</span>
            </Link>
            <Link to="/register" className="sidebar-auth-btn register">
              <UserPlus size={16} />
              <span>Register</span>
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
}
