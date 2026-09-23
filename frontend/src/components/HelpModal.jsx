import React, { useState } from 'react';
import { 
  X, 
  HelpCircle, 
  ShieldCheck, 
  Search, 
  FileText, 
  Sparkles, 
  BookOpen, 
  ChevronRight, 
  ChevronDown,
  Mail
} from 'lucide-react';

export default function HelpModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('getting-started');
  const [expandedFaq, setExpandedFaq] = useState(0);

  if (!isOpen) return null;

  const faqs = [
    {
      q: 'How does EviBite AI verify packaged food safety?',
      a: 'EviBite AI utilizes a 4-agent collaborative pipeline. When you ask about a food item, our Intent Router categorizes your query, the Knowledge Retrieval Agent pulls ingredient facts from USDA FoodData Central and Open Food Facts, the Safety Guardrail evaluates allergens and additives against health thresholds, and the Response Synthesizer crafts an evidence-backed answer with citations.'
    },
    {
      q: 'Can EviBite AI detect hidden allergens like nut traces or gluten?',
      a: 'Yes! Our database scans declare both direct ingredients and manufacturer allergen cross-contact warnings (such as "may contain traces of peanuts or tree nuts").'
    },
    {
      q: 'How can I customize my dietary allergies or preferences?',
      a: 'Click on your profile at the bottom left of the sidebar, select "Personalization" (or "Settings" -> "Diet & Allergens"), and toggle your specific restrictions (Peanuts, Milk, Gluten, Vegan, Low Sugar, etc.).'
    },
    {
      q: 'Is EviBite AI a replacement for professional medical advice?',
      a: 'No. EviBite AI is an educational food intelligence tool. Always read physical package labels before consumption and consult a certified allergist or physician for personal medical diagnoses.'
    }
  ];

  const samplePrompts = [
    {
      label: 'Allergen Verification',
      text: 'I have a peanut allergy. Can I safely eat Nutella hazelnut spread?',
      icon: <ShieldCheck size={16} className="text-emerald" />
    },
    {
      label: 'Sugar & Calorie Audit',
      text: 'How much sugar and caffeine is in a 330ml can of Coca-Cola Original?',
      icon: <FileText size={16} className="text-cyan" />
    },
    {
      label: 'Product Comparison',
      text: 'Compare artificial sweeteners between Coca-Cola Zero and Pepsi Max.',
      icon: <Sparkles size={16} className="text-amber" />
    },
    {
      label: 'Dietary Suitability',
      text: 'Are Oreo Original biscuits suitable for a strict vegan or halal diet?',
      icon: <Search size={16} className="text-rose" />
    }
  ];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="help-modal-card" onClick={(e) => e.stopPropagation()}>
        <button className="settings-close-btn" onClick={onClose} aria-label="Close help modal">
          <X size={20} />
        </button>

        {/* Modal Header */}
        <div className="settings-header">
          <div className="settings-icon-badge help-badge">
            <HelpCircle size={22} color="#46803A" />
          </div>
          <div>
            <h2>EviBite AI Help & Support</h2>
            <p className="settings-subtitle">Learn how to verify food ingredients, interpret safety badges, and query the multi-agent system.</p>
          </div>
        </div>

        {/* Modal Body Layout */}
        <div className="settings-layout">
          {/* Left Tab Navigation */}
          <div className="settings-tabs-sidebar">
            <button
              className={`settings-tab-item ${activeTab === 'getting-started' ? 'active' : ''}`}
              onClick={() => setActiveTab('getting-started')}
            >
              <BookOpen size={16} />
              <span>Getting Started</span>
            </button>

            <button
              className={`settings-tab-item ${activeTab === 'safety-badges' ? 'active' : ''}`}
              onClick={() => setActiveTab('safety-badges')}
            >
              <ShieldCheck size={16} />
              <span>Safety Badges</span>
            </button>

            <button
              className={`settings-tab-item ${activeTab === 'faq' ? 'active' : ''}`}
              onClick={() => setActiveTab('faq')}
            >
              <HelpCircle size={16} />
              <span>FAQs</span>
            </button>

            <button
              className={`settings-tab-item ${activeTab === 'contact' ? 'active' : ''}`}
              onClick={() => setActiveTab('contact')}
            >
              <Mail size={16} />
              <span>Support & Contact</span>
            </button>
          </div>

          {/* Right Tab Content */}
          <div className="settings-tab-content help-tab-scroll">
            {/* TAB 1: Getting Started */}
            {activeTab === 'getting-started' && (
              <div className="help-section">
                <h3>How to Query EviBite AI</h3>
                <p className="help-text">
                  EviBite AI is designed to audit packaged supermarket goods with zero-hallucination evidence. You can ask directly in the chat box using natural language.
                </p>

                <h4 className="help-subheading">Try These Sample Prompts:</h4>
                <div className="sample-prompt-list">
                  {samplePrompts.map((p, idx) => (
                    <div key={idx} className="sample-prompt-item">
                      <div className="sample-prompt-header">
                        {p.icon}
                        <span className="sample-prompt-tag">{p.label}</span>
                      </div>
                      <p className="sample-prompt-query">"{p.text}"</p>
                    </div>
                  ))}
                </div>

                <div className="help-tip-box">
                  <Sparkles size={16} className="text-emerald" />
                  <span><strong>Tip:</strong> Mention your specific allergens (e.g. "I am lactose intolerant" or "Celiac disease") in your prompt for personalized risk mapping.</span>
                </div>
              </div>
            )}

            {/* TAB 2: Safety Badges */}
            {activeTab === 'safety-badges' && (
              <div className="help-section">
                <h3>Interpreting AI Safety Scores</h3>
                <p className="help-text">
                  The Safety Guardrail Agent assigns a color-coded indicator to every verified product analysis:
                </p>

                <div className="badge-guide-list">
                  <div className="badge-guide-card safe">
                    <div className="badge-pill pill-safe">Safe / Verified</div>
                    <div className="badge-guide-info">
                      <strong>Low or No Risk Detected</strong>
                      <p>Product ingredients do not match your saved allergen alerts or high risk dietary triggers.</p>
                    </div>
                  </div>

                  <div className="badge-guide-card warning">
                    <div className="badge-pill pill-warning">Caution / Warning</div>
                    <div className="badge-guide-info">
                      <strong>Moderate Risk or Cross-Contact</strong>
                      <p>Product may be manufactured in a facility handling allergens, or contains high sugar/sodium additives.</p>
                    </div>
                  </div>

                  <div className="badge-guide-card danger">
                    <div className="badge-pill pill-danger">High Risk Alert</div>
                    <div className="badge-guide-info">
                      <strong>Direct Allergen Match</strong>
                      <p>Severe danger. The product explicitly lists an ingredient conflicting with your allergies or medical conditions.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: FAQ */}
            {activeTab === 'faq' && (
              <div className="help-section">
                <h3>Frequently Asked Questions</h3>
                <div className="help-faq-list">
                  {faqs.map((faq, idx) => (
                    <div 
                      key={idx} 
                      className={`help-faq-item ${expandedFaq === idx ? 'expanded' : ''}`}
                      onClick={() => setExpandedFaq(expandedFaq === idx ? -1 : idx)}
                    >
                      <div className="help-faq-q">
                        <span>{faq.q}</span>
                        {expandedFaq === idx ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </div>
                      {expandedFaq === idx && (
                        <div className="help-faq-a">
                          <p>{faq.a}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 4: Support & Contact */}
            {activeTab === 'contact' && (
              <div className="help-section">
                <h3>Support & Team Information</h3>
                <p className="help-text">
                  Have a suggestion, noticed missing supermarket data, or encountered an issue? Our engineering team is here to help.
                </p>

                <div className="contact-card">
                  <div className="contact-row">
                    <Mail size={18} className="text-emerald" />
                    <div>
                      <strong>Technical Support & Inquiries</strong>
                      <p>support@evibite-ai.org</p>
                    </div>
                  </div>

                  <div className="contact-row">
                    <BookOpen size={18} className="text-cyan" />
                    <div>
                      <strong>Platform Version</strong>
                      <p>EviBite AI v2.4 (Collaborative Multi-Agent Architecture)</p>
                    </div>
                  </div>

                  <div className="contact-row">
                    <FileText size={18} className="text-amber" />
                    <div>
                      <strong>Integrated Knowledge Bases</strong>
                      <p>USDA FoodData Central API & Open Food Facts Global DB</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
