import React, { useState } from 'react';
import { X, LogIn, UserPlus, Lock, Mail, User, AlertCircle, CheckCircle2 } from 'lucide-react';
import { registerUser, loginUser } from '../services/api';

export default function AuthModal({ isOpen, onClose, onSuccess }) {
  const [activeTab, setActiveTab] = useState('login'); // 'login' or 'register'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setIsSubmitting(true);

    try {
      if (activeTab === 'register') {
        if (!name.trim()) {
          throw new Error('Please enter your full name.');
        }
        await registerUser(name, email, password);
        setSuccessMsg('Account created successfully! Please sign in with your password.');
        setPassword('');
        setTimeout(() => {
          setActiveTab('login');
          setSuccessMsg('Account created successfully! Please sign in to continue.');
        }, 1200);
      } else {
        const res = await loginUser(email, password);
        localStorage.setItem('evibite_auth_token', res.token);
        localStorage.setItem('evibite_user', JSON.stringify(res.user));
        setSuccessMsg('Welcome back!');
        setTimeout(() => {
          onSuccess(res.user);
          onClose();
        }, 800);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-modal-backdrop" onClick={onClose}>
      <div className="auth-modal-card" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>

        <div className="auth-header">
          <div className="auth-logo-badge">
            <Lock size={22} className="accent-icon" />
          </div>
          <h2>{activeTab === 'login' ? 'Sign In to EviBite AI' : 'Create an Account'}</h2>
          <p className="auth-subtitle">
            {activeTab === 'login'
              ? 'Access your product safety verification history and saved dietary preferences.'
              : 'Join EviBite AI for grounded food product safety analysis and nutrition insights.'}
          </p>
        </div>

        <div className="auth-tabs">
          <button
            className={`auth-tab-btn ${activeTab === 'login' ? 'active' : ''}`}
            onClick={() => { setActiveTab('login'); setError(null); setSuccessMsg(null); }}
          >
            <LogIn size={16} />
            Sign In
          </button>
          <button
            className={`auth-tab-btn ${activeTab === 'register' ? 'active' : ''}`}
            onClick={() => { setActiveTab('register'); setError(null); setSuccessMsg(null); }}
          >
            <UserPlus size={16} />
            Register
          </button>
        </div>

        {error && (
          <div className="auth-alert error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="auth-alert success">
            <CheckCircle2 size={18} />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          {activeTab === 'register' && (
            <div className="input-field-group">
              <label htmlFor="auth-name">Full Name</label>
              <div className="input-with-icon">
                <User size={18} className="field-icon" />
                <input
                  id="auth-name"
                  type="text"
                  placeholder="e.g. Wasika Anusanga"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          <div className="input-field-group">
            <label htmlFor="auth-email">Email Address</label>
            <div className="input-with-icon">
              <Mail size={18} className="field-icon" />
              <input
                id="auth-email"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="input-field-group">
            <label htmlFor="auth-password">Password</label>
            <div className="input-with-icon">
              <Lock size={18} className="field-icon" />
              <input
                id="auth-password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>
          </div>

          <button type="submit" className="auth-submit-btn" disabled={isSubmitting}>
            {isSubmitting ? (
              <span className="btn-spinner">Processing...</span>
            ) : activeTab === 'login' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
