import React, { useState } from 'react';
import { X, Settings as SettingsIcon, ShieldAlert, Cpu, User, Sliders, Check, Moon, Bell } from 'lucide-react';

export default function SettingsModal({ isOpen, onClose, user }) {
  const [activeTab, setActiveTab] = useState('general');
  const [sessionMemoryEnabled, setSessionMemoryEnabled] = useState(true);
  const [allergens, setAllergens] = useState({
    peanut: true,
    milk: true,
    egg: false,
    soy: false,
    gluten: true,
    nuts: true,
  });
  const [dietary, setDietary] = useState({
    vegan: false,
    vegetarian: false,
    lowSugar: true,
  });
  const [savedSuccess, setSavedSuccess] = useState(false);

  if (!isOpen) return null;

  const toggleAllergen = (key) => {
    setAllergens(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const toggleDietary = (key) => {
    setDietary(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 800);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="settings-modal-card" onClick={(e) => e.stopPropagation()}>
        <button className="settings-close-btn" onClick={onClose} aria-label="Close settings">
          <X size={20} />
        </button>

        <div className="settings-header">
          <div className="settings-icon-badge">
            <SettingsIcon size={22} className="accent-icon" />
          </div>
          <div>
            <h2>Settings & Preferences</h2>
            <p className="settings-subtitle">Manage system configuration, AI models, and allergen safety alerts.</p>
          </div>
        </div>

        <div className="settings-layout">
          {/* Left Tab Navigation */}
          <div className="settings-tabs-sidebar">
            <button
              className={`settings-tab-item ${activeTab === 'general' ? 'active' : ''}`}
              onClick={() => setActiveTab('general')}
            >
              <Cpu size={16} />
              <span>General & AI</span>
            </button>
            <button
              className={`settings-tab-item ${activeTab === 'allergens' ? 'active' : ''}`}
              onClick={() => setActiveTab('allergens')}
            >
              <ShieldAlert size={16} />
              <span>Diet & Allergens</span>
            </button>
            <button
              className={`settings-tab-item ${activeTab === 'account' ? 'active' : ''}`}
              onClick={() => setActiveTab('account')}
            >
              <User size={16} />
              <span>Account Info</span>
            </button>
          </div>

          {/* Right Tab Content */}
          <div className="settings-tab-content">
            {activeTab === 'general' && (
              <div className="settings-section">
                <h3>General Settings</h3>
                
                <div className="setting-row">
                  <div>
                    <div className="setting-title">Primary LLM Model Engine</div>
                    <div className="setting-desc">Selected model for intent extraction and grounded response synthesis.</div>
                  </div>
                  <span className="setting-badge-emerald">Gemini 3.1 Flash-Lite</span>
                </div>

                <div className="setting-row">
                  <div>
                    <div className="setting-title">Multi-Turn Session Memory</div>
                    <div className="setting-desc">Remembers previously discussed products (e.g. Coca-Cola) across follow-up turns.</div>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={sessionMemoryEnabled}
                      onChange={() => setSessionMemoryEnabled(!sessionMemoryEnabled)}
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-row">
                  <div>
                    <div className="setting-title">System Theme</div>
                    <div className="setting-desc">Current application appearance theme.</div>
                  </div>
                  <span className="setting-badge">
                    <Moon size={14} style={{ marginRight: '6px' }} />
                    Dark Glassmorphism
                  </span>
                </div>
              </div>
            )}

            {activeTab === 'allergens' && (
              <div className="settings-section">
                <h3>Allergen Safeguards & Dietary Profiles</h3>
                <p className="setting-desc" style={{ marginBottom: '16px' }}>
                  Enable default allergen warnings for safety evaluation when querying packaged supermarket products.
                </p>

                <div className="checkbox-grid">
                  <label className={`checkbox-card ${allergens.peanut ? 'selected' : ''}`}>
                    <input
                      type="checkbox"
                      checked={allergens.peanut}
                      onChange={() => toggleAllergen('peanut')}
                    />
                    <span>🥜 Peanut Allergy</span>
                  </label>

                  <label className={`checkbox-card ${allergens.milk ? 'selected' : ''}`}>
                    <input
                      type="checkbox"
                      checked={allergens.milk}
                      onChange={() => toggleAllergen('milk')}
                    />
                    <span>🥛 Dairy / Milk</span>
                  </label>

                  <label className={`checkbox-card ${allergens.gluten ? 'selected' : ''}`}>
                    <input
                      type="checkbox"
                      checked={allergens.gluten}
                      onChange={() => toggleAllergen('gluten')}
                    />
                    <span>🌾 Gluten / Wheat</span>
                  </label>

                  <label className={`checkbox-card ${allergens.nuts ? 'selected' : ''}`}>
                    <input
                      type="checkbox"
                      checked={allergens.nuts}
                      onChange={() => toggleAllergen('nuts')}
                    />
                    <span>🌰 Tree Nuts</span>
                  </label>

                  <label className={`checkbox-card ${dietary.vegan ? 'selected' : ''}`}>
                    <input
                      type="checkbox"
                      checked={dietary.vegan}
                      onChange={() => toggleDietary('vegan')}
                    />
                    <span>🌱 100% Vegan</span>
                  </label>

                  <label className={`checkbox-card ${dietary.lowSugar ? 'selected' : ''}`}>
                    <input
                      type="checkbox"
                      checked={dietary.lowSugar}
                      onChange={() => toggleDietary('lowSugar')}
                    />
                    <span>🍬 Low Sugar Preference</span>
                  </label>
                </div>
              </div>
            )}

            {activeTab === 'account' && (
              <div className="settings-section">
                <h3>Account Information</h3>
                
                <div className="setting-row">
                  <div>
                    <div className="setting-title">Full Name</div>
                    <div className="setting-desc">{user ? user.name : 'Guest User'}</div>
                  </div>
                  <span className="setting-badge">{user ? 'Registered' : 'Guest'}</span>
                </div>

                <div className="setting-row">
                  <div>
                    <div className="setting-title">Email Address</div>
                    <div className="setting-desc">{user ? user.email : 'Not signed in'}</div>
                  </div>
                </div>

                <div className="setting-row">
                  <div>
                    <div className="setting-title">Account Status</div>
                    <div className="setting-desc">Active EviBite AI Member</div>
                  </div>
                  <span className="setting-badge-emerald">Verified</span>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="settings-footer">
          {savedSuccess && (
            <span className="save-success-tag">
              <Check size={16} /> Saved preferences!
            </span>
          )}
          <button className="settings-save-btn" onClick={handleSave}>
            Save & Close
          </button>
        </div>
      </div>
    </div>
  );
}
