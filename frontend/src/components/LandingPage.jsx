import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  Sparkles, 
  Cpu, 
  Search, 
  Scale, 
  HeartPulse, 
  ChevronDown, 
  ChevronRight, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRight, 
  Zap, 
  UserCheck, 
  FileText, 
  Lock,
  Layers,
  Bot,
  Activity,
  Menu,
  X,
  User,
  LogOut,
  MessageSquare,
  Utensils
} from 'lucide-react';

export default function LandingPage({ user, onSignOut }) {
  const [activeTab, setActiveTab] = useState('allergen');
  const [openFaq, setOpenFaq] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const profileRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileDropdownOpen(false);
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

  const handleSignInClick = () => {
    if (user) {
      navigate('/chat');
    } else {
      navigate('/login');
    }
  };

  const handleTryClick = () => {
    if (user) {
      navigate('/chat');
    } else {
      navigate('/register');
    }
  };

  const demoScenarios = {
    allergen: {
      title: 'Peanut & Nut Allergy Verification',
      query: 'I have a severe peanut allergy. Can I safely eat Nutella hazelnut spread?',
      agents: [
        { name: 'Intent Router', status: 'Passed', detail: 'Identified query category: Severe Allergen Check & Dietary Risk' },
        { name: 'Knowledge Retrieval', status: 'Passed', detail: 'Fetched verified ingredient list from Ferrero product database & USDA DB' },
        { name: 'Safety Guardrail', status: 'Flagged Risk', detail: 'Detected Hazelnuts (Tree Nut) & Skimmed Milk. Facility processes peanuts.' },
        { name: 'Response Synthesizer', status: 'Completed', detail: 'Generated warning statement with ingredient breakdown and evidence citations' }
      ],
      result: {
        safetyScore: 'High Caution Required',
        safetyColor: 'rose',
        verdict: 'Nutella contains Hazelnuts (tree nut) and Milk. May contain traces of peanuts depending on manufacturing region.',
        ingredients: ['Sugar', 'Palm Oil', 'Hazelnuts (13%)', 'Skimmed Milk Powder (8.7%)', 'Fat-Reduced Cocoa (7.4%)', 'Lecithin (Soy)', 'Vanillin'],
        citations: [
          { title: 'USDA FoodData Central #171267', confidence: '99%' },
          { title: 'EviBite Allergen Mapping - Tree Nuts / Peanuts', confidence: '100%' }
        ]
      }
    },
    nutrition: {
      title: 'Nutritional Breakdown & Sugar Alert',
      query: 'What is the exact sugar and calorie content of a 330ml Coca-Cola Original, and what artificial additives are present?',
      agents: [
        { name: 'Intent Router', status: 'Passed', detail: 'Identified query category: Macro Analysis & Additive Inspection' },
        { name: 'Knowledge Retrieval', status: 'Passed', detail: 'Retrieved official nutritional table & ingredient deck for 330ml Can' },
        { name: 'Safety Guardrail', status: 'Passed', detail: 'Calculated 139 kcal and 35g Added Sugar (70% Daily Value limit)' },
        { name: 'Response Synthesizer', status: 'Completed', detail: 'Structured nutritional facts table with glycemic index warnings' }
      ],
      result: {
        safetyScore: 'High Sugar Content Warning',
        safetyColor: 'amber',
        verdict: 'A single 330ml can contains 35g of sugar (equivalent to ~9 teaspoons), contributing 139 kcal with zero dietary fiber.',
        ingredients: ['Carbonated Water', 'Sugar', 'Color (Caramel E150d)', 'Phosphoric Acid', 'Natural Flavourings (including Caffeine)'],
        citations: [
          { title: 'Open Food Facts Database #5449000000996', confidence: '98%' },
          { title: 'EviBite Glycemic Index Engine', confidence: '95%' }
        ]
      }
    },
    vegan: {
      title: 'Vegan & Halal Suitability Audit',
      query: 'Are Oreo Original Biscuits suitable for a strict vegan and halal diet?',
      agents: [
        { name: 'Intent Router', status: 'Passed', detail: 'Identified query category: Certification & Dietary Restrictions' },
        { name: 'Knowledge Retrieval', status: 'Passed', detail: 'Queried Mondelez allergen declaration & cross-contamination statements' },
        { name: 'Safety Guardrail', status: 'Cross-Contact Alert', detail: 'No direct animal products in UK/US recipe, but milk cross-contact possible.' },
        { name: 'Response Synthesizer', status: 'Completed', detail: 'Formulated precise breakdown for vegans vs strict dairy-free individuals' }
      ],
      result: {
        safetyScore: 'Vegan Friendly (Cross-Contact Risk)',
        safetyColor: 'emerald',
        verdict: 'Oreo Biscuits contain no direct dairy/animal ingredients in standard recipe, making them vegan-friendly. However, milk cross-contact is noted.',
        ingredients: ['Wheat Flour', 'Sugar', 'Palm Oil', 'Fat Reduced Cocoa Powder 4.6%', 'Wheat Starch', 'Raising Agents', 'Emulsifiers (Soy Lecithin)'],
        citations: [
          { title: 'Mondelez Allergen & Vegan Disclosure 2026', confidence: '99%' },
          { title: 'Halal Food Authority Standards', confidence: '96%' }
        ]
      }
    }
  };

  const currentScenario = demoScenarios[activeTab];

  const faqs = [
    {
      q: 'What is EviBite AI and how does it protect against allergen risks?',
      a: 'EviBite AI is a specialized multi-agent food intelligence platform. Unlike generic LLMs that might make assumptions, EviBite AI uses dedicated agents to parse food safety data, cross-reference official USDA and food databases, enforce zero-hallucination safety guardrails, and provide transparent evidence citations for every answer.'
    },
    {
      q: 'How does the multi-agent architecture work?',
      a: 'When you ask a question, our system routes it through 4 specialized AI agents: 1) Intent Router parses your dietary profile and inquiry, 2) Knowledge Retrieval pulls verified ingredient decks, 3) Safety Guardrail checks severe allergen thresholds and cross-contamination alerts, and 4) Response Synthesizer crafts clear, transparent answers with citations.'
    },
    {
      q: 'Does EviBite AI support custom user health profiles?',
      a: 'Yes! You can configure your health profile with severe allergies (Peanuts, Tree Nuts, Dairy, Gluten, Soy, Shellfish), dietary regimes (Keto, Vegan, Halal, Kosher, Low-Carb), and calorie thresholds. The Safety Guardrail agent evaluates all queries specifically against your saved profile.'
    },
    {
      q: 'Is EviBite AI a replacement for official medical advice?',
      a: 'No. EviBite AI provides evidence-backed food safety information for educational guidance. Individuals with life-threatening allergies should always verify packaging labels directly and consult qualified medical professionals for personal health advice.'
    }
  ];

  return (
    <div className="landing-page">
      {/* HEADER NAVBAR */}
      <header className="landing-nav">
        <div className="landing-nav-container">
          <div className="landing-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} style={{ cursor: 'pointer' }}>
            <div className="brand-icon">
              <Sparkles size={18} color="#10b981" />
            </div>
            <span className="brand-title">EviBite AI</span>
            <span className="version-badge">v2.4</span>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="nav-links desktop-only">
            <a href="#features">Features</a>
            <a href="#architecture">Architecture</a>
            <a href="/diet-plan" onClick={(e) => { e.preventDefault(); navigate('/diet-plan'); }} style={{ color: '#10b981', fontWeight: 600 }}>Diet Planner</a>
            <a href="#demo">Live Demo</a>
            <a href="#faq">FAQ</a>
          </nav>

          <div className="nav-actions desktop-only">
            {user ? (
              <>
                <button className="btn-primary" onClick={handleTryClick}>
                  Go to Chatbot <ArrowRight size={16} />
                </button>

                <div className="user-profile-dropdown-wrapper" ref={profileRef}>
                  <button
                    className={`user-nav-profile-btn ${profileDropdownOpen ? 'active' : ''}`}
                    onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                    aria-label="User Profile Menu"
                  >
                    <div className="user-nav-avatar">
                      {getInitials(user.name || user.email)}
                    </div>
                    <span className="user-nav-name">{user.name || user.email}</span>
                    <ChevronDown size={14} className={`dropdown-chevron ${profileDropdownOpen ? 'open' : ''}`} />
                  </button>

                  {profileDropdownOpen && (
                    <div className="user-profile-dropdown-menu">
                      <div className="dropdown-user-header">
                        <div className="dropdown-avatar-large">
                          {getInitials(user.name || user.email)}
                        </div>
                        <div className="dropdown-user-details">
                          <span className="dropdown-user-name">{user.name || 'User'}</span>
                          <span className="dropdown-user-email">{user.email}</span>
                        </div>
                      </div>
                      <div className="dropdown-divider" />
                      <button
                        className="dropdown-menu-item"
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          navigate('/chat');
                        }}
                      >
                        <MessageSquare size={16} />
                        <span>Go to Chatbot</span>
                      </button>
                      <button
                        className="dropdown-menu-item logout-item"
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          if (onSignOut) onSignOut();
                        }}
                      >
                        <LogOut size={16} />
                        <span>Log out</span>
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <button className="btn-secondary" onClick={handleSignInClick}>
                  Sign In
                </button>
                <button className="btn-primary" onClick={handleTryClick}>
                  Try Free <ArrowRight size={16} />
                </button>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            className="mobile-toggle mobile-only"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="mobile-dropdown">
            <a href="/diet-plan" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/diet-plan'); }} style={{ color: '#10b981', fontWeight: 600 }}>Diet & Nutrition Planner</a>
            <a href="#features" onClick={() => setMobileMenuOpen(false)}>Features</a>
            <a href="#architecture" onClick={() => setMobileMenuOpen(false)}>Architecture</a>
            <a href="#demo" onClick={() => setMobileMenuOpen(false)}>Live Demo</a>
            <a href="#faq" onClick={() => setMobileMenuOpen(false)}>FAQ</a>
            <div className="mobile-actions">
              {user ? (
                <>
                  <div className="mobile-user-info">
                    <div className="user-nav-avatar">
                      {getInitials(user.name || user.email)}
                    </div>
                    <div className="mobile-user-details">
                      <span className="mobile-user-name">{user.name || user.email}</span>
                      <span className="mobile-user-email">{user.email}</span>
                    </div>
                  </div>
                  <button className="btn-primary full-width" onClick={() => { setMobileMenuOpen(false); handleTryClick(); }}>
                    Go to Chatbot <ArrowRight size={16} />
                  </button>
                  <button className="btn-secondary full-width logout-btn" onClick={() => { setMobileMenuOpen(false); if (onSignOut) onSignOut(); }}>
                    <LogOut size={16} /> Log out
                  </button>
                </>
              ) : (
                <>
                  <button className="btn-secondary full-width" onClick={() => { setMobileMenuOpen(false); handleSignInClick(); }}>
                    Sign In
                  </button>
                  <button className="btn-primary full-width" onClick={() => { setMobileMenuOpen(false); handleTryClick(); }}>
                    Try Free <ArrowRight size={16} />
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* HERO SECTION */}
      <section className="hero-section">
        <div className="hero-glow hero-glow-1"></div>
        <div className="hero-glow hero-glow-2"></div>

        <div className="hero-content">
          <div className="hero-badge">
            <ShieldCheck size={16} className="text-emerald" />
            <span>Multi-Agent Food Safety & AI Nutrition Intelligence</span>
          </div>

          <h1 className="hero-title">
            Eat Safe. Know Every Ingredient. <br />
            <span className="gradient-text">Powered by Verifiable Multi-Agent AI.</span>
          </h1>

          <p className="hero-subtitle">
            EviBite AI instantly analyzes allergens, food safety, and nutritional profiles using a 4-agent collaborative intelligence system with zero-hallucination guardrails and real-time database citations.
          </p>

          <div className="hero-ctas">
            <button className="btn-primary hero-btn" onClick={handleTryClick}>
              <Zap size={18} /> {user ? 'Go to Chatbot' : 'Try EviBite AI Free'}
            </button>
            <button className="btn-secondary hero-btn" onClick={() => navigate('/diet-plan')} style={{ borderColor: '#10b981', color: '#10b981' }}>
              <Utensils size={18} /> Diet Planner
            </button>
            <a href="#demo" className="btn-outline hero-btn">
              <Sparkles size={18} /> Explore Prompts Demo
            </a>
          </div>

          <div className="hero-metrics">
            <div className="metric-item">
              <span className="metric-val">99.8%</span>
              <span className="metric-lbl">Allergen Accuracy Rate</span>
            </div>
            <div className="metric-divider"></div>
            <div className="metric-item">
              <span className="metric-val">4 Agents</span>
              <span className="metric-lbl">Collaborative Pipeline</span>
            </div>
            <div className="metric-divider"></div>
            <div className="metric-item">
              <span className="metric-val">10,000+</span>
              <span className="metric-lbl">Verified Food Products</span>
            </div>
            <div className="metric-divider"></div>
            <div className="metric-item">
              <span className="metric-val">&lt; 250ms</span>
              <span className="metric-lbl">Guardrail Response Time</span>
            </div>
          </div>
        </div>

        {/* HERO INTERACTIVE PREVIEW CARD */}
        <div className="hero-visual">
          <div className="hero-card-window">
            <div className="window-header">
              <div className="window-dots">
                <span className="dot dot-red"></span>
                <span className="dot dot-yellow"></span>
                <span className="dot dot-green"></span>
              </div>
              <div className="window-title">EviBite AI Agent Pipeline — Active Analysis</div>
              <div className="status-indicator">
                <span className="pulse-dot"></span> System Operational
              </div>
            </div>

            <div className="window-body">
              <div className="mock-user-prompt">
                <div className="user-avatar">U</div>
                <div className="user-bubble">
                  "Does Coca-Cola Zero contain phenylalanine or allergens for someone with PKU?"
                </div>
              </div>

              <div className="mock-agent-trace">
                <div className="trace-step step-complete">
                  <CheckCircle2 size={14} className="text-emerald" />
                  <span><strong>Router Agent:</strong> Classified query as Phenylketonuria (PKU) Metabolic Safety Check.</span>
                </div>
                <div className="trace-step step-complete">
                  <CheckCircle2 size={14} className="text-emerald" />
                  <span><strong>Retrieval Agent:</strong> Fetched Aspartame formulation data from USDA & Coca-Cola Product Deck.</span>
                </div>
                <div className="trace-step step-warning">
                  <AlertTriangle size={14} className="text-rose" />
                  <span><strong>Safety Guardrail:</strong> Critical Warning — Aspartame metabolizes into Phenylalanine. High risk for PKU.</span>
                </div>
              </div>

              <div className="mock-ai-response">
                <div className="ai-avatar">
                  <Sparkles size={16} color="#10b981" />
                </div>
                <div className="ai-card">
                  <div className="ai-alert-banner alert-danger">
                    <AlertTriangle size={18} />
                    <div>
                      <strong>HIGH SAFETY RISK — Contains Phenylalanine</strong>
                      <p>Coca-Cola Zero Sugar uses Aspartame, which metabolizes into Phenylalanine. Not suitable for individuals with PKU.</p>
                    </div>
                  </div>

                  <div className="ai-ingredients-deck">
                    <span className="deck-title">Ingredient Risk Map:</span>
                    <div className="tag-group">
                      <span className="ing-tag tag-safe">Carbonated Water</span>
                      <span className="ing-tag tag-safe">Caramel Color (E150d)</span>
                      <span className="ing-tag tag-danger">Aspartame (Phenylalanine Source)</span>
                      <span className="ing-tag tag-warn">Acesulfame K</span>
                      <span className="ing-tag tag-safe">Phosphoric Acid</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES SECTION */}
      <section id="features" className="features-section">
        <div className="section-header center">
          <span className="section-tag">Intelligent Capabilities</span>
          <h2>Why EviBite AI Outperforms Standard Chatbots</h2>
          <p>Designed specifically for food safety, dietary security, and ingredient precision.</p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon icon-emerald">
              <ShieldCheck size={24} />
            </div>
            <h3>Instant Allergen Detection</h3>
            <p>
              Scans product ingredients against severe allergens including peanuts, tree nuts, dairy, gluten, soy, shellfish, and sesame with cross-contamination risk warnings.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-cyan">
              <Cpu size={24} />
            </div>
            <h3>Multi-Agent Orchestration</h3>
            <p>
              Uses 4 specialized agents working in tandem: Router, Knowledge Retrieval, Safety Guardrail, and Response Synthesizer for high-precision validation.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-amber">
              <FileText size={24} />
            </div>
            <h3>Verifiable Evidence Tracing</h3>
            <p>
              Every claim is backed by transparent citations from official USDA FoodData Central databases and verified food manufacturer disclosures.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-rose">
              <Scale size={24} />
            </div>
            <h3>Nutritional & Additive Auditing</h3>
            <p>
              Evaluates sugar levels, calories, artificial sweeteners, preservatives (E-numbers), and processed food risk factors in real time.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-emerald">
              <Zap size={24} />
            </div>
            <h3>Zero-Latency Guardrails</h3>
            <p>
              Patented safety engine evaluates ingredient safety thresholds before response generation to prevent dangerous dietary advice.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-cyan">
              <UserCheck size={24} />
            </div>
            <h3>Personalized Health Profiles</h3>
            <p>
              Save your unique dietary restrictions (Vegan, Keto, Halal, Gluten-Free) and receive tailored warnings customized to your exact needs.
            </p>
          </div>
        </div>
      </section>

      {/* MULTI-AGENT ARCHITECTURE SECTION */}
      <section id="architecture" className="architecture-section">
        <div className="section-header center">
          <span className="section-tag">Deep Tech Architecture</span>
          <h2>The 4-Agent Intelligence Pipeline</h2>
          <p>How EviBite AI eliminates LLM hallucinations in food safety analysis.</p>
        </div>

        <div className="pipeline-grid">
          <div className="pipeline-card">
            <div className="step-num">01</div>
            <div className="pipeline-header">
              <Bot size={22} className="text-emerald" />
              <h4>Intent Router Agent</h4>
            </div>
            <p>
              Parses the user query and dietary profile to determine inquiry type: severe allergy risk, macro nutrition, or certification check.
            </p>
          </div>

          <div className="pipeline-arrow"><ChevronRight size={24} /></div>

          <div className="pipeline-card">
            <div className="step-num">02</div>
            <div className="pipeline-header">
              <Search size={22} className="text-cyan" />
              <h4>Knowledge Retrieval Agent</h4>
            </div>
            <p>
              Fetches verified product formulations, USDA nutrient profiles, and official manufacturer allergen cross-contact disclosures.
            </p>
          </div>

          <div className="pipeline-arrow"><ChevronRight size={24} /></div>

          <div className="pipeline-card highlight-card">
            <div className="step-num">03</div>
            <div className="pipeline-header">
              <Lock size={22} className="text-rose" />
              <h4>Safety Guardrail Agent</h4>
            </div>
            <p>
              Executes strict safety evaluation, testing ingredient lists against known user sensitivities, toxicity limits, and contamination alerts.
            </p>
          </div>

          <div className="pipeline-arrow"><ChevronRight size={24} /></div>

          <div className="pipeline-card">
            <div className="step-num">04</div>
            <div className="pipeline-header">
              <Layers size={22} className="text-amber" />
              <h4>Response Synthesizer</h4>
            </div>
            <p>
              Constructs a concise, structured response with confidence metrics, ingredient breakdowns, and direct evidence citations.
            </p>
          </div>
        </div>
      </section>

      {/* INTERACTIVE DEMO SECTION */}
      <section id="demo" className="demo-section">
        <div className="section-header center">
          <span className="section-tag">Interactive Preview</span>
          <h2>See EviBite AI in Action</h2>
          <p>Test real sample scenarios and inspect how the multi-agent pipeline reasons through food safety.</p>
        </div>

        <div className="demo-container">
          <div className="demo-tabs">
            <button 
              className={`demo-tab ${activeTab === 'allergen' ? 'active' : ''}`}
              onClick={() => setActiveTab('allergen')}
            >
              <ShieldCheck size={18} /> Severe Peanut Allergy Check
            </button>
            <button 
              className={`demo-tab ${activeTab === 'nutrition' ? 'active' : ''}`}
              onClick={() => setActiveTab('nutrition')}
            >
              <HeartPulse size={18} /> Sugar & Calorie Breakdown
            </button>
            <button 
              className={`demo-tab ${activeTab === 'vegan' ? 'active' : ''}`}
              onClick={() => setActiveTab('vegan')}
            >
              <UserCheck size={18} /> Vegan & Halal Audit
            </button>
          </div>

          <div className="demo-content-card">
            <div className="demo-query-box">
              <span className="query-label">Sample Inquiry:</span>
              <div className="query-text">"{currentScenario.query}"</div>
            </div>

            <div className="demo-split">
              {/* Agent execution trace */}
              <div className="demo-agent-panel">
                <h4>Agent Execution Trace</h4>
                <div className="agent-trace-list">
                  {currentScenario.agents.map((agent, idx) => (
                    <div key={idx} className="trace-item">
                      <div className="trace-header">
                        <span className="agent-name">{agent.name}</span>
                        <span className={`status-tag status-${agent.status.toLowerCase().replace(/\s+/g, '-')}`}>
                          {agent.status}
                        </span>
                      </div>
                      <p className="trace-detail">{agent.detail}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Final Synthesized Output */}
              <div className="demo-result-panel">
                <div className="result-header">
                  <h4>Synthesized Safety Assessment</h4>
                  <span className={`safety-badge badge-${currentScenario.result.safetyColor}`}>
                    {currentScenario.result.safetyScore}
                  </span>
                </div>

                <p className="verdict-text">{currentScenario.result.verdict}</p>

                <div className="ingredients-box">
                  <span className="box-title">Verified Ingredient Deck:</span>
                  <div className="ingredients-pills">
                    {currentScenario.result.ingredients.map((ing, i) => (
                      <span key={i} className="ing-pill">{ing}</span>
                    ))}
                  </div>
                </div>

                <div className="citations-box">
                  <span className="box-title">Verifiable Sources & Confidence:</span>
                  <div className="citation-list">
                    {currentScenario.result.citations.map((cit, i) => (
                      <div key={i} className="citation-item">
                        <FileText size={14} className="text-emerald" />
                        <span>{cit.title}</span>
                        <span className="confidence-val">{cit.confidence} match</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ SECTION */}
      <section id="faq" className="faq-section">
        <div className="section-header center">
          <span className="section-tag">Frequently Asked Questions</span>
          <h2>Got Questions? We Have Answers</h2>
        </div>

        <div className="faq-accordion">
          {faqs.map((faq, idx) => (
            <div 
              key={idx} 
              className={`faq-item ${openFaq === idx ? 'open' : ''}`}
              onClick={() => setOpenFaq(openFaq === idx ? -1 : idx)}
            >
              <div className="faq-question">
                <h3>{faq.q}</h3>
                <ChevronDown size={20} className="faq-icon" />
              </div>
              {openFaq === idx && (
                <div className="faq-answer">
                  <p>{faq.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CTA BANNER */}
      <section className="cta-section">
        <div className="cta-card">
          <div className="cta-content">
            <h2>Ready to Take Control of Your Food Safety?</h2>
            <p>Experience the power of multi-agent AI for allergen detection and ingredient auditing today.</p>
            <button className="btn-primary hero-btn" onClick={handleTryClick}>
              {user ? 'Launch EviBite AI App' : 'Get Started Free'} <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="landing-footer">
        <div className="footer-container">
          <div className="footer-col brand-col">
            <div className="landing-brand">
              <div className="brand-icon">
                <Sparkles size={18} color="#10b981" />
              </div>
              <span className="brand-title">EviBite AI</span>
            </div>
            <p className="footer-desc">
              Verifiable food safety & nutrition intelligence platform powered by collaborative multi-agent architecture.
            </p>
            <span className="copyright">© {new Date().getFullYear()} EviBite AI. All rights reserved.</span>
          </div>

          <div className="footer-col">
            <h4>Product</h4>
            <a href="#features">Allergen Checker</a>
            <a href="#features">Nutrition Analyzer</a>
            <a href="#architecture">Multi-Agent Engine</a>
            <a href="#demo">Live Demo</a>
          </div>

          <div className="footer-col">
            <h4>Safety & Science</h4>
            <a href="#architecture">Guardrail Engine</a>
            <a href="#architecture">USDA Database</a>
            <a href="#faq">Allergen Mappings</a>
            <a href="#faq">Medical Disclaimer</a>
          </div>

          <div className="footer-col">
            <h4>Contact & Legal</h4>
            <a href="#faq">Privacy Policy</a>
            <a href="#faq">Terms of Service</a>
            <a href="#faq">Contact Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
