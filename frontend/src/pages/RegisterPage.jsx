import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerUser } from '../services/api';
import logoImg from '../logo/logo.png';
import { Sparkles, User, Mail, Lock, ArrowRight, ShieldCheck, Eye, EyeOff, AlertCircle, CheckCircle2, ChevronLeft } from 'lucide-react';

export default function RegisterPage({ onRegisterSuccess }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please verify your password.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setIsSubmitting(true);

    try {
      const res = await registerUser(name, email, password);
      localStorage.setItem('evibite_auth_token', res.token);
      localStorage.setItem('evibite_user', JSON.stringify(res.user));
      setSuccessMsg('Account registered successfully! Redirecting...');
      if (onRegisterSuccess) onRegisterSuccess(res.user);
      setTimeout(() => {
        navigate('/');
      }, 1000);
    } catch (err) {
      setError(err.message || 'Registration failed. Please check your details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page-container">
      <div className="auth-page-content">
        {/* Left Side: Brand & Benefits Showcase */}
        <div className="auth-hero-section">
          <div className="hero-brand-badge">
            <img src={logoImg} alt="EviBite AI Logo" className="auth-hero-logo-img" />
            <span className="hero-brand-name">EviBite AI</span>
          </div>

          <h1 className="hero-headline">
            Create Your <br />
            <span className="gradient-text">Food Intelligence Account</span>
          </h1>

          <p className="hero-description">
            Register to save your personalized dietary requirements, search history, and allergen safety alerts powered by multi-agent AI.
          </p>

          <div className="hero-features-list">
            <div className="hero-feature-card">
              <div className="feature-icon-wrapper cyan">
                <User size={20} />
              </div>
              <div>
                <h4>Personalized Preferences</h4>
                <p>Tailor ingredient scans to your specific diet or allergy profile.</p>
              </div>
            </div>

            <div className="hero-feature-card">
              <div className="feature-icon-wrapper emerald">
                <ShieldCheck size={20} />
              </div>
              <div>
                <h4>Grounded Multi-Agent Checks</h4>
                <p>All answers verified with OpenFoodFacts nutrition facts.</p>
              </div>
            </div>
          </div>

          <div className="hero-trust-footer">
            <span className="dot-active" /> Fast & Free Registration
          </div>
        </div>

        {/* Right Side: Sign Up Form Card */}
        <div className="auth-card-section">
          <div className="auth-card-glass">
            <div className="auth-card-header">
              <h2>Create Account</h2>
              <p>Sign up to get started with EviBite AI.</p>
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

            <form onSubmit={handleSubmit} className="auth-page-form">
              <div className="form-group">
                <label htmlFor="reg-name">Full Name</label>
                <div className="input-wrapper">
                  <User size={18} className="input-icon" />
                  <input
                    id="reg-name"
                    type="text"
                    placeholder="e.g. Wasika Anusanga"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="reg-email">Email Address</label>
                <div className="input-wrapper">
                  <Mail size={18} className="input-icon" />
                  <input
                    id="reg-email"
                    type="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="reg-password">Password</label>
                <div className="input-wrapper">
                  <Lock size={18} className="input-icon" />
                  <input
                    id="reg-password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="reg-confirm-password">Confirm Password</label>
                <div className="input-wrapper">
                  <Lock size={18} className="input-icon" />
                  <input
                    id="reg-confirm-password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={6}
                  />
                </div>
              </div>

              <button type="submit" className="auth-primary-btn" disabled={isSubmitting}>
                {isSubmitting ? (
                  <span>Registering...</span>
                ) : (
                  <>
                    <span>Create Account</span>
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            </form>

            <div className="auth-card-footer">
              <p>
                Already have an account?{' '}
                <Link to="/login" className="auth-switch-link">
                  Sign In
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
