import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, Check, Lock, Sparkles, FileText, Zap, ShieldCheck, 
  Crown, ArrowRight, ArrowLeft, Flame, Globe, Printer, Layers, HelpCircle,
  ChevronDown, ChevronUp, CheckCircle2, CreditCard, Shield, Loader2, Utensils
} from 'lucide-react';

export default function PricingModal({ isOpen, onClose, currentTier = 'free', targetTier = null, onSelectTier }) {
  const navigate = useNavigate();

  const [billingCycle, setBillingCycle] = useState('monthly'); // 'monthly' | 'annual'
  const [activeTab, setActiveTab] = useState('cards'); // 'cards' | 'compare'
  const [selectedPlanForCheckout, setSelectedPlanForCheckout] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [upgradedPlan, setUpgradedPlan] = useState(null);
  const [openFaq, setOpenFaq] = useState(null);

  // Simulated card form fields
  const [cardNumber, setCardNumber] = useState('4242 •••• •••• 4242');
  const [cardExpiry, setCardExpiry] = useState('12/28');
  const [cardCvc, setCardCvc] = useState('888');
  const [cardHolder, setCardHolder] = useState('Alex Mercer');

  // Reset state when modal opens or closes
  useEffect(() => {
    if (isOpen) {
      setSelectedPlanForCheckout(null);
      setUpgradedPlan(null);
      setIsProcessingPayment(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const isAnnual = billingCycle === 'annual';

  const plans = [
    {
      id: 'free',
      name: 'Starter Plan',
      price: '$0',
      period: 'Forever free',
      icon: <Layers size={22} className="tier-icon starter" />,
      badge: 'BASIC ACCESS',
      badgeClass: 'badge-free',
      tagline: 'Ideal for quick ingredient lookups & simple supermarket queries.',
      features: [
        { text: '10 Chat Messages per Day', included: true, highlight: false },
        { text: 'Packaged Food & Ingredient Audit', included: true, highlight: false },
        { text: 'Allergen Conflict Screening', included: true, highlight: false },
        { text: 'PDF Recipe & Document Upload', included: false },
        { text: 'Diet & Nutrition Planner Agent', included: false },
        { text: 'Printable A4 Meal Blueprint Export', included: false },
      ],
      buttonText: currentTier === 'free' ? 'Current Plan' : 'Downgrade to Starter',
    },
    {
      id: 'pro',
      name: 'Pro Plan',
      price: isAnnual ? '$7.99' : '$9.99',
      period: 'per month',
      savings: isAnnual ? 'Billed $95.88 annually (Save $24)' : null,
      icon: <Zap size={22} className="tier-icon pro" />,
      badge: '🔥 MOST POPULAR',
      badgeClass: 'badge-pro',
      highlighted: targetTier === 'pro',
      tagline: 'Perfect for home chefs & shoppers who want recipe file uploads & unlimited chat.',
      features: [
        { text: 'UNLIMITED Chatbot Consultations', included: true, highlight: true },
        { text: 'UNLIMITED PDF Recipe & Doc Uploads', included: true, highlight: true },
        { text: 'Recipe Ingredient-to-Product Matching', included: true, highlight: false },
        { text: 'Allergen & Health Safety Screening', included: true, highlight: false },
        { text: 'Diet & Nutrition Planner Agent', included: false },
        { text: 'Printable A4 Meal Blueprint Export', included: false },
      ],
      buttonText: currentTier === 'pro' ? 'Current Plan' : 'Unlock Pro Features',
    },
    {
      id: 'ultimate',
      name: 'Ultimate Plan',
      price: isAnnual ? '$15.99' : '$19.99',
      period: 'per month',
      savings: isAnnual ? 'Billed $191.88 annually (Save $48)' : null,
      icon: <Crown size={22} className="tier-icon ultimate" />,
      badge: targetTier === 'ultimate' ? '👑 RECOMMENDED FOR DIET PLANNER' : '👑 ALL ACCESS PASS',
      badgeClass: 'badge-ultimate',
      highlighted: targetTier === 'ultimate' || true,
      tagline: 'The complete suite with biometric dietitian planner & regional market inventories.',
      features: [
        { text: 'UNLIMITED Chatbot Consultations', included: true, highlight: true },
        { text: 'UNLIMITED PDF Recipe & Doc Uploads', included: true, highlight: true },
        { text: 'Full Clinical Diet & Nutrition Planner', included: true, highlight: true },
        { text: 'Biometric Energy Targets (BMR, TDEE, BMI)', included: true, highlight: false },
        { text: 'Regional Catalogs (LK, UK, US, IN, Global)', included: true, highlight: false },
        { text: 'Printable A4 Meal Blueprint Export', included: true, highlight: false },
      ],
      buttonText: currentTier === 'ultimate' ? 'Current Plan' : 'Upgrade to Ultimate',
    },
  ];

  const faqs = [
    {
      q: 'Can I upgrade or downgrade my plan at any time?',
      a: 'Yes, absolutely! You can change your tier anytime. Upgrades take effect instantly with immediate access to unlocked features.'
    },
    {
      q: 'How does PDF Recipe parsing work in Pro and Ultimate?',
      a: 'You can upload any recipe PDF document directly into the chat. Our multi-agent LLM system extracts ingredients, screens for your allergens, and recommends matching products available in store.'
    },
    {
      q: 'What is included in the Ultimate Diet & Nutrition Planner?',
      a: 'The Ultimate Plan grants access to our full Clinical Diet Planner agent. It calculates your personal biometric targets (BMR, TDEE, BMI), structures meal schedules, and generates printable A4 blueprints.'
    }
  ];

  const comparisonMatrix = [
    { feature: 'Daily Chat Consultations', starter: '10 / day', pro: 'Unlimited', ultimate: 'Unlimited' },
    { feature: 'PDF Recipe & Document Upload', starter: '❌ Locked', pro: '✅ Unlimited', ultimate: '✅ Unlimited' },
    { feature: 'Ingredient & Product Matcher', starter: 'Basic', pro: 'Advanced', ultimate: 'Full Clinical' },
    { feature: 'Allergen Conflict Screening', starter: '✅ Included', pro: '✅ Included', ultimate: '✅ Included' },
    { feature: 'Diet & Nutrition Planner Agent', starter: '❌ Locked', pro: '❌ Locked', ultimate: '✅ Full Access' },
    { feature: 'Biometrics (BMR/TDEE/BMI)', starter: '❌ Locked', pro: '❌ Locked', ultimate: '✅ Included' },
    { feature: 'Regional Market Inventories', starter: 'Standard', pro: 'Standard', ultimate: 'Global & Regional' },
    { feature: 'Printable A4 Meal Blueprint', starter: '❌ Locked', pro: '❌ Locked', ultimate: '✅ Instant PDF' },
  ];

  const handleStartCheckout = (plan) => {
    if (plan.id === currentTier) {
      onClose();
      return;
    }
    setSelectedPlanForCheckout(plan);
  };

  const handleConfirmActivation = () => {
    if (!selectedPlanForCheckout) return;
    setIsProcessingPayment(true);

    // Simulate payment and provisioning token verification
    setTimeout(() => {
      onSelectTier(selectedPlanForCheckout.id);
      setUpgradedPlan(selectedPlanForCheckout);
      setIsProcessingPayment(false);
      setSelectedPlanForCheckout(null);
    }, 1100);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="pricing-modal-redesigned" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose} title="Close Modal">
          <X size={20} />
        </button>

        {/* ========================================================
            VIEW 1: SUCCESS & CELEBRATION
            ======================================================== */}
        {upgradedPlan ? (
          <div className="upgrade-success-view">
            <div className="success-icon-badge">
              <CheckCircle2 size={48} color="#46803A" />
            </div>
            <h2>{upgradedPlan.name} Activated!</h2>
            <p>
              Welcome to <strong>{upgradedPlan.name}</strong>! All premium features for your tier have been unlocked instantly for your session.
            </p>
            <div className="success-feature-pills">
              {upgradedPlan.id === 'free' && (
                <>
                  <span className="succ-pill"><Layers size={14} /> 10 Daily Chats</span>
                  <span className="succ-pill"><ShieldCheck size={14} /> Allergen Ingredient Screening</span>
                </>
              )}
              {upgradedPlan.id === 'pro' && (
                <>
                  <span className="succ-pill"><Zap size={14} /> Unlimited Chat Messages</span>
                  <span className="succ-pill"><FileText size={14} /> PDF Recipe Document Upload</span>
                  <span className="succ-pill"><ShieldCheck size={14} /> Advanced Allergen Screening</span>
                </>
              )}
              {upgradedPlan.id === 'ultimate' && (
                <>
                  <span className="succ-pill"><Crown size={14} /> Full Diet & Nutrition Planner</span>
                  <span className="succ-pill"><Utensils size={14} /> Biometric Energy Calculations</span>
                  <span className="succ-pill"><Zap size={14} /> Unlimited Consultations & PDFs</span>
                  <span className="succ-pill"><Printer size={14} /> Printable A4 Meal Blueprints</span>
                </>
              )}
            </div>

            <div className="success-action-group">
              {upgradedPlan.id === 'ultimate' ? (
                <>
                  <button
                    type="button"
                    className="success-done-btn launch-diet"
                    onClick={() => {
                      onClose();
                      navigate('/diet-plan');
                    }}
                  >
                    Open Diet & Nutrition Planner 🚀
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    style={{ padding: '12px 24px', borderRadius: '12px', fontWeight: 600 }}
                    onClick={onClose}
                  >
                    Continue to Chat
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  className="success-done-btn"
                  onClick={onClose}
                >
                  Start Using EviBite AI Now <ArrowRight size={18} />
                </button>
              )}
            </div>
          </div>
        ) : selectedPlanForCheckout ? (
          /* ========================================================
             VIEW 2: INTERACTIVE CHECKOUT & ACTIVATION
             ======================================================== */
          <div className="pricing-checkout-view">
            <button
              type="button"
              className="checkout-back-btn"
              onClick={() => setSelectedPlanForCheckout(null)}
            >
              <ArrowLeft size={16} /> Back to all plans
            </button>

            <div className="checkout-content-grid">
              {/* Left Column: Order & Plan Summary */}
              <div className="checkout-summary-col">
                <div className={`checkout-plan-card ${selectedPlanForCheckout.id}`}>
                  <div className="checkout-plan-header">
                    <div className="checkout-badge-pill">
                      {selectedPlanForCheckout.id === 'ultimate' 
                        ? '👑 ALL ACCESS PASS' 
                        : selectedPlanForCheckout.id === 'pro' 
                          ? '🔥 UNLIMITED ACCESS' 
                          : '🆓 BASIC ACCESS'
                      }
                    </div>
                    <div className="checkout-title-row">
                      {selectedPlanForCheckout.icon}
                      <h3>{selectedPlanForCheckout.name}</h3>
                    </div>
                    <p className="checkout-tagline">{selectedPlanForCheckout.tagline}</p>
                  </div>

                  <div className="checkout-price-callout">
                    <span className="checkout-price-num">
                      {selectedPlanForCheckout.id === 'free'
                        ? '$0'
                        : isAnnual 
                          ? (selectedPlanForCheckout.id === 'ultimate' ? '$15.99' : '$7.99')
                          : (selectedPlanForCheckout.id === 'ultimate' ? '$19.99' : '$9.99')
                      }
                    </span>
                    <span className="checkout-price-unit">
                      {selectedPlanForCheckout.id === 'free' ? 'forever free' : '/ month'}
                    </span>
                    <span className="checkout-billing-badge">
                      {selectedPlanForCheckout.id === 'free'
                        ? '100% Free Plan'
                        : isAnnual ? 'Billed annually (Save 20%)' : 'Billed monthly'
                      }
                    </span>
                  </div>

                  <div className="checkout-features-unlocked">
                    <h4>Included with your activation:</h4>
                    <ul className="checkout-features-list">
                      {selectedPlanForCheckout.features.map((feat, idx) => (
                        <li key={idx} className={feat.included ? 'feat-yes' : 'feat-no'}>
                          {feat.included ? (
                            <CheckCircle2 size={16} color="#46803A" />
                          ) : (
                            <Lock size={14} color="#94A3B8" />
                          )}
                          <span>{feat.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Right Column: Payment & Confirmation */}
              <div className="checkout-payment-col">
                <div className="payment-panel-card">
                  <div className="payment-panel-header">
                    <h4>Review & Activate Subscription</h4>
                    <p>
                      {selectedPlanForCheckout.id === 'free'
                        ? 'Confirm your switch to the Starter Plan below.'
                        : 'Select your preferred activation method below.'}
                    </p>
                  </div>

                  {selectedPlanForCheckout.id === 'free' ? (
                    <div className="free-plan-notice-card">
                      <CheckCircle2 size={26} color="#166534" />
                      <div>
                        <strong>100% Free • No Payment Required</strong>
                        <p>Enjoy 10 daily chats and allergen scanning at zero cost. No credit card or billing details required.</p>
                      </div>
                    </div>
                  ) : (
                    <>
                      {/* Payment Method Selector */}
                      <div className="payment-method-selector">
                        <div className="payment-method-tab active" style={{ cursor: 'default' }}>
                          <div className="tab-left">
                            <CreditCard size={16} color="#46803A" />
                            <div>
                              <strong>Credit / Debit Card</strong>
                              <p>Simulated Stripe 256-bit checkout</p>
                            </div>
                          </div>
                          <div className="radio-dot checked" />
                        </div>
                      </div>

                      {/* Simulated Card Form */}
                      <div className="simulated-card-form">
                        <div className="checkout-form-group">
                          <label>Card Number</label>
                          <div className="input-with-brand">
                            <CreditCard size={16} className="card-brand-icon" />
                            <input
                              type="text"
                              value={cardNumber}
                              onChange={(e) => setCardNumber(e.target.value)}
                              placeholder="4242 •••• •••• 4242"
                            />
                            <span className="card-brand-tag">VISA</span>
                          </div>
                        </div>

                        <div className="checkout-form-row">
                          <div className="checkout-form-group">
                            <label>Expires</label>
                            <input
                              type="text"
                              value={cardExpiry}
                              onChange={(e) => setCardExpiry(e.target.value)}
                              placeholder="MM/YY"
                            />
                          </div>
                          <div className="checkout-form-group">
                            <label>CVC</label>
                            <input
                              type="text"
                              value={cardCvc}
                              onChange={(e) => setCardCvc(e.target.value)}
                              placeholder="CVC"
                            />
                          </div>
                        </div>

                        <div className="checkout-form-group">
                          <label>Cardholder Name</label>
                          <input
                            type="text"
                            value={cardHolder}
                            onChange={(e) => setCardHolder(e.target.value)}
                            placeholder="Your Name"
                          />
                        </div>
                      </div>
                    </>
                  )}

                  {/* Summary Cost Breakdown */}
                  <div className="checkout-totals-box">
                    <div className="totals-line">
                      <span>Subscription ({selectedPlanForCheckout.name})</span>
                      <span>
                        {selectedPlanForCheckout.id === 'free'
                          ? '$0.00'
                          : isAnnual
                            ? (selectedPlanForCheckout.id === 'ultimate' ? '$239.88' : '$119.88')
                            : (selectedPlanForCheckout.id === 'ultimate' ? '$19.99' : '$9.99')}
                      </span>
                    </div>
                    {isAnnual && selectedPlanForCheckout.id !== 'free' && (
                      <div className="totals-line discount">
                        <span>Annual 20% Discount</span>
                        <span>{selectedPlanForCheckout.id === 'ultimate' ? '-$48.00' : '-$24.00'}</span>
                      </div>
                    )}
                    <div className="totals-line">
                      <span>Multi-Agent Platform Access</span>
                      <span className="text-free">FREE</span>
                    </div>
                    <div className="totals-divider" />
                    <div className="totals-line grand-total">
                      <span>Total Due Today</span>
                      <span className="total-amount-highlight">
                        {selectedPlanForCheckout.id === 'free'
                          ? '$0.00'
                          : isAnnual
                            ? (selectedPlanForCheckout.id === 'ultimate' ? '$191.88' : '$95.88')
                            : (selectedPlanForCheckout.id === 'ultimate' ? '$19.99' : '$9.99')}
                      </span>
                    </div>
                  </div>

                  {/* Activation Button */}
                  <button
                    type="button"
                    className={`confirm-activation-btn ${selectedPlanForCheckout.id}`}
                    onClick={handleConfirmActivation}
                    disabled={isProcessingPayment}
                  >
                    {isProcessingPayment ? (
                      <span className="btn-loading-flex">
                        <Loader2 size={18} className="spin-icon" /> Updating Plan...
                      </span>
                    ) : (
                      <span className="btn-loading-flex">
                        <ShieldCheck size={18} /> Confirm & Activate {selectedPlanForCheckout.name}
                      </span>
                    )}
                  </button>

                  <div className="checkout-security-notice">
                    <Shield size={14} color="#46803A" />
                    <span>256-bit encrypted checkout • Instant access • Cancel anytime</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* ========================================================
             VIEW 3: PLAN SELECTION & COMPARISON
             ======================================================== */
          <>
            {/* Context Alert when opened from locked feature */}
            {targetTier === 'ultimate' && (
              <div className="pricing-target-alert ultimate">
                <div className="alert-left-col">
                  <div className="alert-icon-circle">
                    <Crown size={20} color="#9A6700" />
                  </div>
                  <div>
                    <h4>Diet & Nutrition Planner requires Ultimate Plan</h4>
                    <p>Upgrade to the Ultimate tier below to unlock clinical meal planning, personalized biometric targets (BMR/TDEE), and printable meal blueprints.</p>
                  </div>
                </div>
                <button
                  type="button"
                  className="alert-cta-btn"
                  onClick={() => handleStartCheckout(plans.find(p => p.id === 'ultimate'))}
                >
                  Get Ultimate <ArrowRight size={14} />
                </button>
              </div>
            )}

            {targetTier !== 'ultimate' && currentTier === 'free' && (
              <div className="pricing-target-alert general">
                <div className="alert-left-col">
                  <div className="alert-icon-circle green">
                    <Sparkles size={20} color="#46803A" />
                  </div>
                  <div>
                    <h4>Unlock Unlimited Chats & Recipe PDF Document Ingestion</h4>
                    <p>Upgrade from Starter Plan to access unlimited AI queries, allergen screening, and full clinical dietitian planning.</p>
                  </div>
                </div>
              </div>
            )}

            {/* Hero Banner Header */}
            <div className="pricing-modal-hero">
              <div className="hero-sparkle-pill">
                <Sparkles size={14} color="#46803A" /> Commercial Subscription Plans
              </div>
              <h2>Supercharge Your Food & Recipe Intelligence</h2>
              <p className="hero-subtext">
                Unlock PDF recipe document parsing, unlimited multi-agent consultations, and clinical dietitian meal plans.
              </p>

              {/* View Switch (Cards vs Compare Matrix) */}
              <div className="modal-subnav-tabs">
                <button
                  type="button"
                  className={`subnav-tab-btn ${activeTab === 'cards' ? 'active' : ''}`}
                  onClick={() => setActiveTab('cards')}
                >
                  <Layers size={15} /> Pricing Tiers
                </button>
                <button
                  type="button"
                  className={`subnav-tab-btn ${activeTab === 'compare' ? 'active' : ''}`}
                  onClick={() => setActiveTab('compare')}
                >
                  <Sparkles size={15} /> Full Feature Matrix
                </button>
              </div>

              {/* Billing Toggle Switch */}
              <div className="billing-toggle-container">
                <button
                  type="button"
                  className={`billing-opt-btn ${!isAnnual ? 'active' : ''}`}
                  onClick={() => setBillingCycle('monthly')}
                >
                  Monthly Billing
                </button>
                <button
                  type="button"
                  className={`billing-opt-btn ${isAnnual ? 'active' : ''}`}
                  onClick={() => setBillingCycle('annual')}
                >
                  <span>Annual Billing</span>
                  <span className="save-badge">SAVE 20%</span>
                </button>
              </div>
            </div>

            {/* TAB 1: 3 Tier Grid */}
            {activeTab === 'cards' ? (
              <div className="pricing-grid-redesigned">
                {plans.map((plan) => {
                  const isActive = currentTier === plan.id;
                  const isTarget = targetTier === plan.id;
                  return (
                    <div
                      key={plan.id}
                      className={`pricing-card-redesigned ${plan.id} ${plan.highlighted ? 'is-highlighted' : ''} ${isActive ? 'is-active-tier' : ''} ${isTarget ? 'is-target-focus' : ''}`}
                    >
                      {/* Plan Badge */}
                      <div className={`card-top-badge ${plan.badgeClass}`}>
                        {plan.badge}
                      </div>

                      {/* Card Header */}
                      <div className="card-header-block">
                        <div className="card-title-row">
                          {plan.icon}
                          <h3>{plan.name}</h3>
                        </div>
                        <p className="card-tagline">{plan.tagline}</p>
                      </div>

                      {/* Price Block */}
                      <div className="card-price-block">
                        <div className="price-num-row">
                          <span className="price-amount">{plan.price}</span>
                          <span className="price-period">/ {plan.period}</span>
                        </div>
                        {plan.savings && <span className="price-savings-note">{plan.savings}</span>}
                      </div>

                      <div className="card-divider" />

                      {/* Feature List */}
                      <ul className="card-feature-list">
                        {plan.features.map((feat, idx) => (
                          <li
                            key={idx}
                            className={`${feat.included ? 'feat-enabled' : 'feat-disabled'} ${feat.highlight ? 'feat-bold' : ''}`}
                          >
                            {feat.included ? (
                              <div className="icon-circle check">
                                <Check size={14} />
                              </div>
                            ) : (
                              <div className="icon-circle lock">
                                <Lock size={12} />
                              </div>
                            )}
                            <span>{feat.text}</span>
                          </li>
                        ))}
                      </ul>

                      {/* Action CTA Button */}
                      <button
                        type="button"
                        className={`card-cta-btn ${plan.id} ${isActive ? 'active-cta' : ''}`}
                        onClick={() => handleStartCheckout(plan)}
                        disabled={isActive}
                      >
                        {isActive ? (
                          <span className="active-btn-text"><Check size={16} /> Active Plan</span>
                        ) : (
                          <span className="btn-flex-content">
                            {plan.buttonText} <ArrowRight size={16} />
                          </span>
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : (
              /* TAB 2: Feature Matrix Table */
              <div className="comparison-matrix-wrapper">
                <table className="comparison-matrix-table">
                  <thead>
                    <tr>
                      <th className="feature-col">Feature Comparison</th>
                      <th className="tier-col free">Starter ($0)</th>
                      <th className="tier-col pro">Pro ($9.99/mo)</th>
                      <th className="tier-col ultimate">Ultimate ($19.99/mo)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonMatrix.map((row, idx) => (
                      <tr key={idx}>
                        <td className="feature-name">{row.feature}</td>
                        <td className="tier-val free">{row.starter}</td>
                        <td className="tier-val pro">{row.pro}</td>
                        <td className="tier-val ultimate">{row.ultimate}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* FAQ Accordion Section */}
            <div className="pricing-faq-section">
              <h4 className="faq-heading"><HelpCircle size={16} color="#46803A" /> Frequently Asked Questions</h4>
              <div className="faq-grid">
                {faqs.map((faq, idx) => (
                  <div
                    key={idx}
                    className={`faq-item ${openFaq === idx ? 'open' : ''}`}
                    onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  >
                    <div className="faq-question">
                      <span>{faq.q}</span>
                      {openFaq === idx ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                    {openFaq === idx && <div className="faq-answer">{faq.a}</div>}
                  </div>
                ))}
              </div>
            </div>

            {/* Footer Guarantee */}
            <div className="pricing-modal-footer-redesigned">
              <div className="footer-guarantee-item">
                <ShieldCheck size={18} color="#46803A" />
                <span>Instant Plan Activation</span>
              </div>
              <div className="footer-dot">•</div>
              <div className="footer-guarantee-item">
                <Zap size={18} color="#9A6700" />
                <span>Switch or Cancel Anytime</span>
              </div>
              <div className="footer-dot">•</div>
              <div className="footer-guarantee-item">
                <Globe size={18} color="#2A6F78" />
                <span>Global & Regional Market Support</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
