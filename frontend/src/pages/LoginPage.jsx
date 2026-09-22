import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { loginUser } from '../services/api';
import { Sparkles, Mail, Lock, ArrowRight, ShieldCheck, Eye, EyeOff, AlertCircle, CheckCircle2, ChevronLeft } from 'lucide-react';

export default function LoginPage({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const res = await loginUser(email, password);
      localStorage.setItem('evibite_auth_token', res.token);
      localStorage.setItem('evibite_user', JSON.stringify(res.user));
      if (onLoginSuccess) onLoginSuccess(res.user);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Invalid email or password. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page-container">
      {/* Top back navigation bar */}
      <div className="auth-page-nav">
        <Link to="/" className="back-link-btn">
          <ChevronLeft size={18} />
          <span>Back to EviBite AI</span>
        </Link>
      </div>

      <div className="auth-page-content">
        {/* Left Side: Brand & Feature Showcase */}
        <div className="auth-hero-section">
          <div className="hero-brand-badge">
            <Sparkles size={24} className="hero-icon-sparkle" />
            <span className="hero-brand-name">EviBite AI</span>
          </div>

          <h1 className="hero-headline">
            Smart & Grounded <br />
            <span className="gradient-text">Food Intelligence</span>
          </h1>

          <p className="hero-description">
            Sign in to access personalized allergen safety alerts, nutrient comparisons, and multi-agent evidence reasoning across supermarket packaged foods.
          </p>

          <div className="hero-features-list">
            <div className="hero-feature-card">
              <div className="feature-icon-wrapper red">
                <ShieldCheck size={20} />
              </div>
              <div>
                <h4>Allergen Safeguards</h4>
                <p>Instant safety verification against peanuts, dairy, gluten & soy.</p>
              </div>
            </div>

            <div className="hero-feature-card">
              <div className="feature-icon-wrapper emerald">
                <Sparkles size={20} />
              </div>
              <div>
                <h4>Multi-Agent Orchestration</h4>
                <p>Ground answers strictly from authoritative open food databases.</p>
              </div>
            </div>
          </div>

          <div className="hero-trust-footer">
            <span className="dot-active" /> Verified OpenFoodFacts Integration
          </div>
        </div>

        {/* Right Side: Sign In Form Card */}
        <div className="auth-card-section">
          <div className="auth-card-glass">
            <div className="auth-card-header">
              <h2>Sign In</h2>
              <p>Welcome back! Please enter your details.</p>
            </div>

            {error && (
              <div className="auth-alert error">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-page-form">
              <div className="form-group">
                <label htmlFor="login-email">Email Address</label>
                <div className="input-wrapper">
                  <Mail size={18} className="input-icon" />
                  <input
                    id="login-email"
                    type="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="login-password">Password</label>
                <div className="input-wrapper">
                  <Lock size={18} className="input-icon" />
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
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

              <button type="submit" className="auth-primary-btn" disabled={isSubmitting}>
                {isSubmitting ? (
                  <span>Signing in...</span>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            </form>

            <div className="auth-card-footer">
              <p>
                Don't have an account?{' '}
                <Link to="/register" className="auth-switch-link">
                  Create an account
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
