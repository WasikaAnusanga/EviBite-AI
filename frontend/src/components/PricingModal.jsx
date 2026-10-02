import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, Check, Minus, Sparkles, FileText, Zap, ShieldCheck, 
  Crown, ArrowRight, ArrowLeft, Globe, Printer, Layers, HelpCircle,
  ChevronDown, ChevronUp, CheckCircle2, CreditCard, Shield, Loader2, Utensils, Info
} from 'lucide-react';

// ============================================================================
// SINGLE SOURCE OF TRUTH: PLANS CONFIGURATION
// ============================================================================
export const PLANS_CONFIG = [
  {
    id: 'free',
    name: 'Starter',
    progressionLabel: 'CHECK',
    tagline: 'Check what you eat',
    description: 'Core evidence-grounded food, nutrition and allergen intelligence.',
    monthlyPrice: 0,
    annualMonthlyPrice: 0,
    annualTotal: 0,
    usageLabel: '10 chats per day',
    fairUseNote: null,
    popular: false,
    badge: 'CHECK',
    badgeClass: 'badge-starter',
    ctaStyle: 'secondary-outline',
    cta: 'Get Started Free',
    features: [
      { text: 'Packaged food analysis', highlight: false },
      { text: 'Allergen conflict screening', highlight: false },
      { text: 'Nutrition information', highlight: false },
      { text: 'Open Food Facts & USDA data search', highlight: false },
      { text: 'Product comparisons', highlight: false },
      { text: 'Evidence-grounded responses', highlight: false },
      { text: 'Source citations', highlight: false },
      { text: 'Basic chat history', highlight: false },
    ],
    unavailableFeatures: [
      { text: 'PDF recipe analysis' },
      { text: 'Advanced ingredient extraction' },
      { text: 'Personalized diet planner' },
      { text: 'Biometric nutrition calculations' },
      { text: 'Saved meal plans' },
      { text: 'Printable meal plans' },
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    progressionLabel: 'ANALYSE',
    tagline: 'Understand what you eat',
    description: 'Advanced product, ingredient and recipe analysis for frequent users.',
    monthlyPrice: 1490,
    annualMonthlyPrice: 1190,
    annualTotal: 14280,
    usageLabel: 'High monthly AI usage',
    fairUseNote: 'Subject to reasonable fair-use limits to ensure service quality.',
    popular: true,
    badge: 'MOST POPULAR',
    badgeClass: 'badge-pro',
    ctaStyle: 'solid-primary',
    cta: 'Upgrade to Pro',
    features: [
      { text: 'Everything in Starter', highlight: true },
      { text: 'High monthly AI usage', highlight: true },
      { text: 'Full allergen & cross-contact analysis', highlight: false },
      { text: 'Advanced product comparisons', highlight: false },
      { text: 'Generous PDF recipe uploads', highlight: true },
      { text: 'Recipe ingredient extraction', highlight: false },
      { text: 'Product ingredient matching', highlight: false },
      { text: 'Priority AI processing', highlight: false },
      { text: 'Extended chat history', highlight: false },
      { text: 'Evidence-backed safety explanations', highlight: false },
    ],
    unavailableFeatures: [
      { text: 'Personalized AI diet planner' },
      { text: 'BMR / TDEE / BMI calculations' },
      { text: '7-day meal plans' },
      { text: 'Personalized grocery lists' },
      { text: 'Saved diet plans' },
      { text: 'Printable meal blueprints' },
    ],
  },
  {
    id: 'ultimate',
    name: 'Ultimate',
    progressionLabel: 'PLAN',
    tagline: 'Plan what you eat',
    description: 'Personalized nutrition targets, meal planning and grocery guidance.',
    monthlyPrice: 2990,
    annualMonthlyPrice: 2390,
    annualTotal: 28680,
    usageLabel: 'Highest monthly AI usage',
    fairUseNote: 'Subject to reasonable fair-use limits to ensure service quality.',
    popular: false,
    badge: 'PLAN • PERSONALIZED',
    badgeClass: 'badge-ultimate',
    ctaStyle: 'solid-premium',
    cta: 'Go Ultimate',
    features: [
      { text: 'Everything in Pro', highlight: true },
      { text: 'Highest monthly AI usage', highlight: true },
      { text: 'Autonomous AI diet planning', highlight: true },
      { text: 'Generous PDF recipe uploads', highlight: false },
      { text: 'Personalized biometric profiling (BMR/TDEE)', highlight: true },
      { text: 'Personalized calorie & macro targets', highlight: true },
      { text: '7-day personalized meal plans', highlight: true },
      { text: 'Personalized grocery lists', highlight: true },
      { text: 'Dietary preference customization', highlight: false },
      { text: 'Allergen-aware meal planning', highlight: false },
      { text: 'Budget-aware meal planning', highlight: false },
      { text: 'Cooking-preference adaptation', highlight: false },
      { text: 'Sri Lanka regional food support', highlight: true },
      { text: 'US, UK, India & Global food support', highlight: false },
      { text: 'Saved personalized diet plans', highlight: false },
      { text: 'Printable A4 meal blueprint', highlight: false },
    ],
    unavailableFeatures: [],
  },
];

// Helper: Format LKR Currency amounts
export const formatLKR = (amount) => {
  if (amount === 0 || amount === '0') return 'Free';
  return `LKR ${Number(amount).toLocaleString('en-US')}`;
};

// Helper: Derive active pricing details for a plan
export const getPlanPricing = (plan, isAnnual) => {
  if (!plan || plan.monthlyPrice === 0) {
    return {
      price: 'Free',
      period: '',
      secondaryText: null,
      rawMonthly: 0,
      rawTotal: 0,
      rawUndiscountedAnnual: 0,
      rawDiscount: 0,
    };
  }
  if (isAnnual) {
    return {
      price: formatLKR(plan.annualMonthlyPrice),
      period: '/month',
      secondaryText: `Billed ${formatLKR(plan.annualTotal)} annually`,
      rawMonthly: plan.annualMonthlyPrice,
      rawTotal: plan.annualTotal,
      rawUndiscountedAnnual: plan.monthlyPrice * 12,
      rawDiscount: (plan.monthlyPrice * 12) - plan.annualTotal,
    };
  }
  return {
    price: formatLKR(plan.monthlyPrice),
    period: '/month',
    secondaryText: null,
    rawMonthly: plan.monthlyPrice,
    rawTotal: plan.monthlyPrice,
    rawUndiscountedAnnual: plan.monthlyPrice * 12,
    rawDiscount: 0,
  };
};

const getPlanIcon = (id) => {
  switch (id) {
    case 'free': return <ShieldCheck size={22} className="tier-icon starter" />;
    case 'pro': return <Zap size={22} className="tier-icon pro" />;
    case 'ultimate': return <Crown size={22} className="tier-icon ultimate" />;
    default: return <Sparkles size={22} />;
  }
};

const comparisonMatrixRows = [
  {
    feature: 'Price — Monthly',
    starter: formatLKR(PLANS_CONFIG.find(p => p.id === 'free').monthlyPrice),
    pro: formatLKR(PLANS_CONFIG.find(p => p.id === 'pro').monthlyPrice),
    ultimate: formatLKR(PLANS_CONFIG.find(p => p.id === 'ultimate').monthlyPrice),
  },
  {
    feature: 'Annual billing',
    starter: 'Free',
    pro: `${formatLKR(PLANS_CONFIG.find(p => p.id === 'pro').annualTotal)}/year`,
    ultimate: `${formatLKR(PLANS_CONFIG.find(p => p.id === 'ultimate').annualTotal)}/year`,
  },
  {
    feature: 'AI consultations',
    starter: '10/day',
    pro: 'High usage',
    ultimate: 'Highest usage',
  },
  {
    feature: 'Evidence-grounded food search',
    starter: true,
    pro: true,
    ultimate: true,
  },
  {
    feature: 'Open Food Facts & USDA retrieval',
    starter: true,
    pro: true,
    ultimate: true,
  },
  {
    feature: 'Allergen conflict screening',
    starter: true,
    pro: true,
    ultimate: true,
  },
  {
    feature: 'Product comparisons',
    starter: true,
    pro: true,
    ultimate: true,
  },
  {
    feature: 'Source citations',
    starter: true,
    pro: true,
    ultimate: true,
  },
  {
    feature: 'PDF recipe/document analysis',
    starter: false,
    pro: true,
    ultimate: true,
  },
  {
    feature: 'Recipe ingredient extraction',
    starter: false,
    pro: true,
    ultimate: true,
  },
  {
    feature: 'Advanced ingredient matching',
    starter: false,
    pro: true,
    ultimate: true,
  },
  {
    feature: 'Priority AI processing',
    starter: false,
    pro: true,
    ultimate: true,
  },
  {
    feature: 'Personalized diet planner',
    starter: false,
    pro: false,
    ultimate: true,
  },
  {
    feature: 'BMR/TDEE/BMI profiling',
    starter: false,
    pro: false,
    ultimate: true,
  },
  {
    feature: 'Personalized calorie & macro targets',
    starter: false,
    pro: false,
    ultimate: true,
  },
  {
    feature: '7-day meal planning',
    starter: false,
    pro: false,
    ultimate: true,
  },
  {
    feature: 'Regional meal adaptation',
    starter: 'Basic/global product search',
    pro: 'Basic/global product search',
    ultimate: 'Sri Lanka + US + UK + India + Global',
  },
  {
    feature: 'Budget-aware planning',
    starter: false,
    pro: false,
    ultimate: true,
  },
  {
    feature: 'Cooking preference adaptation',
    starter: false,
    pro: false,
    ultimate: true,
  },
  {
    feature: 'Personalized grocery list',
    starter: false,
    pro: false,
    ultimate: true,
  },
  {
    feature: 'Saved diet plans',
    starter: false,
    pro: false,
    ultimate: true,
  },
  {
    feature: 'Printable meal blueprint',
    starter: false,
    pro: false,
    ultimate: true,
  },
];

export default function PricingModal({ isOpen, onClose, currentTier = 'free', targetTier = null, onSelectTier }) {
  const navigate = useNavigate();

  const [billingCycle, setBillingCycle] = useState('monthly'); // 'monthly' | 'annual'
  const [activeTab, setActiveTab] = useState('cards'); // 'cards' | 'compare'
  const [selectedPlanForCheckout, setSelectedPlanForCheckout] = useState(null);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [upgradedPlan, setUpgradedPlan] = useState(null);
  const [openFaq, setOpenFaq] = useState(null);

  // Simulated card form fields (empty by default with example placeholders)
  const [cardNumber, setCardNumber] = useState('');
  const [cardExpiry, setCardExpiry] = useState('');
  const [cardCvc, setCardCvc] = useState('');
  const [cardHolder, setCardHolder] = useState('');
  const [formErrors, setFormErrors] = useState({});

  // Reset state when modal opens or closes
  useEffect(() => {
    if (isOpen) {
      setSelectedPlanForCheckout(null);
      setUpgradedPlan(null);
      setIsProcessingPayment(false);
      setCardNumber('');
      setCardExpiry('');
      setCardCvc('');
      setCardHolder('');
      setFormErrors({});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const isAnnual = billingCycle === 'annual';

  // Build rendered card list by combining config and dynamic pricing
  const plans = PLANS_CONFIG.map((plan) => {
    const pricing = getPlanPricing(plan, isAnnual);
    const allFeatures = [
      ...plan.features.map(f => ({ text: f.text, included: true, highlight: !!f.highlight })),
      ...plan.unavailableFeatures.map(f => ({ text: f.text, included: false, highlight: false })),
    ];

    return {
      ...plan,
      valueStatement: plan.tagline,
      price: pricing.price,
      period: pricing.period,
      savings: pricing.secondaryText,
      usage: plan.usageLabel,
      icon: getPlanIcon(plan.id),
      highlighted: plan.popular || (targetTier === plan.id),
      allFeatures,
      buttonText: currentTier === plan.id ? 'Current Plan' : plan.cta,
    };
  });

  const faqs = [
    {
      q: 'Can I upgrade or downgrade my plan at any time?',
      a: 'Yes, absolutely! You can change your tier anytime. Upgrades take effect instantly with immediate access to unlocked features.'
    },
    {
      q: 'How does PDF Recipe parsing work in Pro and Ultimate?',
      a: 'You can upload recipe PDF documents directly into the chat. Our multi-agent system extracts ingredients, screens for your declared allergens, and recommends matching products available in store.'
    },
    {
      q: 'What is included in the Ultimate Diet & Nutrition Planner?',
      a: 'The Ultimate Plan grants access to our AI Diet Planner agent. It calculates your personal biometric targets (BMR, TDEE, BMI), structures 7-day meal schedules, supports Sri Lankan and global markets, and generates printable A4 blueprints.'
    }
  ];

  const handleCardNumberChange = (e) => {
    const rawDigits = e.target.value.replace(/\D/g, '').slice(0, 16);
    const formatted = rawDigits.match(/.{1,4}/g)?.join(' ') || rawDigits;
    setCardNumber(formatted);
    if (formErrors.cardNumber) {
      setFormErrors((prev) => ({ ...prev, cardNumber: undefined }));
    }
  };

  const handleExpiryChange = (e) => {
    const rawDigits = e.target.value.replace(/\D/g, '').slice(0, 4);
    if (rawDigits.length <= 2) {
      setCardExpiry(rawDigits);
    } else {
      setCardExpiry(`${rawDigits.slice(0, 2)}/${rawDigits.slice(2)}`);
    }
    if (formErrors.cardExpiry) {
      setFormErrors((prev) => ({ ...prev, cardExpiry: undefined }));
    }
  };

  const handleCvcChange = (e) => {
    const rawDigits = e.target.value.replace(/\D/g, '').slice(0, 4);
    setCardCvc(rawDigits);
    if (formErrors.cardCvc) {
      setFormErrors((prev) => ({ ...prev, cardCvc: undefined }));
    }
  };

  const handleCardHolderChange = (e) => {
    setCardHolder(e.target.value);
    if (formErrors.cardHolder) {
      setFormErrors((prev) => ({ ...prev, cardHolder: undefined }));
    }
  };

  const validatePaymentForm = () => {
    if (!selectedPlanForCheckout || selectedPlanForCheckout.id === 'free') {
      return true;
    }

    const errors = {};
    const rawCardDigits = cardNumber.replace(/\D/g, '');
    if (!rawCardDigits || rawCardDigits.length < 15) {
      errors.cardNumber = 'Please enter a valid 15 or 16-digit card number';
    }

    const rawExpiryDigits = cardExpiry.replace(/\D/g, '');
    if (rawExpiryDigits.length < 4) {
      errors.cardExpiry = 'Enter MM/YY';
    } else {
      const month = parseInt(rawExpiryDigits.slice(0, 2), 10);
      if (month < 1 || month > 12) {
        errors.cardExpiry = 'Invalid month (01-12)';
      }
    }

    const rawCvcDigits = cardCvc.replace(/\D/g, '');
    if (!rawCvcDigits || rawCvcDigits.length < 3) {
      errors.cardCvc = '3 or 4 digits required';
    }

    if (!cardHolder.trim() || cardHolder.trim().length < 2) {
      errors.cardHolder = 'Please enter the cardholder name';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleStartCheckout = (plan) => {
    if (plan.id === currentTier) {
      onClose();
      return;
    }
    setFormErrors({});
    setSelectedPlanForCheckout(plan);
  };

  const handleConfirmActivation = () => {
    if (!selectedPlanForCheckout) return;

    if (selectedPlanForCheckout.id !== 'free') {
      const isValid = validatePaymentForm();
      if (!isValid) return;
    }

    setIsProcessingPayment(true);

    setTimeout(async () => {
      try {
        if (onSelectTier) {
          await onSelectTier(selectedPlanForCheckout.id);
        }
      } catch (err) {
        console.error('Tier upgrade error:', err);
      } finally {
        setUpgradedPlan(selectedPlanForCheckout);
        setIsProcessingPayment(false);
        setSelectedPlanForCheckout(null);
      }
    }, 800);
  };

  const renderCellContent = (val, tier) => {
    if (val === true || val === 'Yes') {
      return (
        <span className={`table-badge yes ${tier}`}>
          <Check size={16} />
        </span>
      );
    }
    if (val === false || val === 'No') {
      return (
        <span className="table-badge no">
          <Minus size={16} />
        </span>
      );
    }
    return <span className={`table-text-val ${tier}`}>{val}</span>;
  };

  const checkoutPricing = selectedPlanForCheckout ? getPlanPricing(selectedPlanForCheckout, isAnnual) : null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="pricing-modal-redesigned" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose} title="Close Modal">
          <X size={20} />
        </button>

        {/* VIEW 1: SUCCESS & CELEBRATION */}
        {upgradedPlan ? (
          <div className="upgrade-success-view">
            <div className="success-icon-badge">
              <CheckCircle2 size={48} color="#46803A" />
            </div>
            <h2>{upgradedPlan.name} Activated!</h2>
            <p>
              Welcome to <strong>{upgradedPlan.name}</strong>! All features for your tier have been unlocked instantly for your session.
            </p>
            <div className="success-feature-pills">
              {upgradedPlan.id === 'free' && (
                <>
                  <span className="succ-pill"><ShieldCheck size={14} /> 10 Daily Chats</span>
                  <span className="succ-pill"><Check size={14} /> Allergen Screening</span>
                </>
              )}
              {upgradedPlan.id === 'pro' && (
                <>
                  <span className="succ-pill"><Zap size={14} /> High Monthly AI Usage</span>
                  <span className="succ-pill"><FileText size={14} /> Generous PDF Recipe Uploads</span>
                  <span className="succ-pill"><ShieldCheck size={14} /> Full Cross-Contact Analysis</span>
                </>
              )}
              {upgradedPlan.id === 'ultimate' && (
                <>
                  <span className="succ-pill"><Crown size={14} /> Highest Monthly AI Usage</span>
                  <span className="succ-pill"><FileText size={14} /> Generous PDF Recipe Uploads</span>
                  <span className="succ-pill"><Utensils size={14} /> Biometric Energy Calculations (BMR/TDEE)</span>
                  <span className="succ-pill"><Globe size={14} /> Sri Lanka & Global Market Catalogs</span>
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
          /* VIEW 2: INTERACTIVE CHECKOUT & ACTIVATION (LKR) */
          <div className="pricing-checkout-view">
            <button
              type="button"
              className="checkout-back-btn"
              onClick={() => setSelectedPlanForCheckout(null)}
            >
              <ArrowLeft size={16} /> Back to all plans
            </button>

            <div className="checkout-content-grid">
              <div className="checkout-summary-col">
                <div className={`checkout-plan-card ${selectedPlanForCheckout.id}`}>
                  <div className="checkout-plan-header">
                    <div className="checkout-badge-pill">
                      {selectedPlanForCheckout.id === 'ultimate' 
                        ? '👑 ALL ACCESS PASS' 
                        : selectedPlanForCheckout.id === 'pro' 
                          ? '🔥 MOST POPULAR' 
                          : '🆓 BASIC ACCESS'
                      }
                    </div>
                    <div className="checkout-title-row">
                      {selectedPlanForCheckout.icon}
                      <h3>{selectedPlanForCheckout.name}</h3>
                    </div>
                    <div className="checkout-value-statement">{selectedPlanForCheckout.valueStatement}</div>
                    <p className="checkout-tagline">{selectedPlanForCheckout.description}</p>
                  </div>

                  <div className="checkout-price-callout">
                    <span className="checkout-price-num">
                      {checkoutPricing.price}
                    </span>
                    <span className="checkout-price-unit">
                      {selectedPlanForCheckout.id === 'free' ? 'forever free' : checkoutPricing.period}
                    </span>
                    <span className="checkout-billing-badge">
                      {selectedPlanForCheckout.id === 'free'
                        ? 'Free Plan'
                        : isAnnual 
                          ? `${checkoutPricing.secondaryText} (Save ~20%)`
                          : 'Billed monthly'
                      }
                    </span>
                  </div>

                  <div className="checkout-features-unlocked">
                    <h4>Included with your activation:</h4>
                    <ul className="checkout-features-list">
                      {selectedPlanForCheckout.allFeatures.map((feat, idx) => (
                        <li key={idx} className={feat.included ? 'feat-yes' : 'feat-no'}>
                          {feat.included ? (
                            <CheckCircle2 size={16} color="#46803A" />
                          ) : (
                            <X size={14} color="#94A3B8" />
                          )}
                          <span>{feat.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

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
                        <strong>Free Plan • No Payment Required</strong>
                        <p>Enjoy 10 daily chats and allergen scanning at zero cost. No credit card or billing details required.</p>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="payment-method-selector">
                        <div className="payment-method-tab active" style={{ cursor: 'default' }}>
                          <div className="tab-left">
                            <CreditCard size={16} color="#46803A" />
                            <div>
                              <strong>Credit / Debit Card (LKR)</strong>
                              <p>Secure 256-bit payment gateway</p>
                            </div>
                          </div>
                          <div className="radio-dot checked" />
                        </div>
                      </div>

                      <div className="simulated-card-form">
                        <div className={`checkout-form-group ${formErrors.cardNumber ? 'has-error' : ''}`}>
                          <label>Card Number</label>
                          <div className={`input-with-brand ${formErrors.cardNumber ? 'input-error' : ''}`}>
                            <CreditCard size={16} className="card-brand-icon" />
                            <input
                              type="text"
                              inputMode="numeric"
                              value={cardNumber}
                              onChange={handleCardNumberChange}
                              placeholder="e.g. 4532 0123 4567 8910"
                              maxLength={19}
                            />
                            <span className="card-brand-tag">VISA</span>
                          </div>
                          {formErrors.cardNumber && (
                            <span className="checkout-field-error">{formErrors.cardNumber}</span>
                          )}
                        </div>

                        <div className="checkout-form-row">
                          <div className={`checkout-form-group ${formErrors.cardExpiry ? 'has-error' : ''}`}>
                            <label>Expires</label>
                            <input
                              type="text"
                              inputMode="numeric"
                              className={formErrors.cardExpiry ? 'input-error' : ''}
                              value={cardExpiry}
                              onChange={handleExpiryChange}
                              placeholder="e.g. 09/28"
                              maxLength={5}
                            />
                            {formErrors.cardExpiry && (
                              <span className="checkout-field-error">{formErrors.cardExpiry}</span>
                            )}
                          </div>
                          <div className={`checkout-form-group ${formErrors.cardCvc ? 'has-error' : ''}`}>
                            <label>CVC / CVV</label>
                            <input
                              type="text"
                              inputMode="numeric"
                              className={formErrors.cardCvc ? 'input-error' : ''}
                              value={cardCvc}
                              onChange={handleCvcChange}
                              placeholder="e.g. 123"
                              maxLength={4}
                            />
                            {formErrors.cardCvc && (
                              <span className="checkout-field-error">{formErrors.cardCvc}</span>
                            )}
                          </div>
                        </div>

                        <div className={`checkout-form-group ${formErrors.cardHolder ? 'has-error' : ''}`}>
                          <label>Cardholder Name</label>
                          <input
                            type="text"
                            className={formErrors.cardHolder ? 'input-error' : ''}
                            value={cardHolder}
                            onChange={handleCardHolderChange}
                            placeholder="e.g. Kasun Perera"
                          />
                          {formErrors.cardHolder && (
                            <span className="checkout-field-error">{formErrors.cardHolder}</span>
                          )}
                        </div>
                      </div>
                    </>
                  )}

                  <div className="checkout-totals-box">
                    <div className="totals-line">
                      <span>Subscription ({selectedPlanForCheckout.name})</span>
                      <span>
                        {selectedPlanForCheckout.id === 'free'
                          ? 'LKR 0'
                          : isAnnual
                            ? formatLKR(checkoutPricing.rawUndiscountedAnnual)
                            : formatLKR(checkoutPricing.rawMonthly)}
                      </span>
                    </div>
                    {isAnnual && selectedPlanForCheckout.id !== 'free' && (
                      <div className="totals-line discount">
                        <span>Annual ~20% Discount</span>
                        <span>{`- ${formatLKR(checkoutPricing.rawDiscount)}`}</span>
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
                        {formatLKR(checkoutPricing.rawTotal)}
                      </span>
                    </div>
                  </div>

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
          /* VIEW 3: PLAN SELECTION & COMPARISON (LKR MODEL) */
          <>
            <div className="pricing-modal-hero">
              <div className="hero-sparkle-pill">
                <Sparkles size={14} color="#46803A" /> EviBite AI Plans & Pricing
              </div>
              <h2>Supercharge Your Food & Recipe Intelligence</h2>
              <p className="hero-subtext">
                Choose the plan that fits your food safety, recipe analysis, and personalized nutrition needs.
              </p>

              {/* Billing Toggle Switch with Save ~20% badge */}
              <div className="billing-toggle-wrapper">
                <div className="billing-toggle-container">
                  <button
                    type="button"
                    className={`billing-opt-btn ${!isAnnual ? 'active' : ''}`}
                    onClick={() => setBillingCycle('monthly')}
                  >
                    Monthly
                  </button>
                  <button
                    type="button"
                    className={`billing-opt-btn ${isAnnual ? 'active' : ''}`}
                    onClick={() => setBillingCycle('annual')}
                  >
                    <span>Annual</span>
                    <span className="save-badge">Save ~20%</span>
                  </button>
                </div>
                <p className="billing-subnote">Save approximately 20% with annual billing.</p>
              </div>
            </div>

            {/* TAB 1: 3 Tier Grid */}
            <div className="pricing-grid-redesigned">
              {plans.map((plan) => {
                const isActive = currentTier === plan.id;
                const isTarget = targetTier === plan.id;
                const isPro = plan.id === 'pro';
                return (
                  <div
                    key={plan.id}
                    className={`pricing-card-redesigned ${plan.id} ${plan.highlighted ? 'is-highlighted is-pro-elevated' : ''} ${isActive ? 'is-active-tier' : ''} ${isTarget ? 'is-target-focus' : ''}`}
                  >
                    <div className={`card-top-badge ${plan.badgeClass}`}>
                      {plan.badge}
                    </div>

                    <div className="card-header-block">
                      <div className="card-title-row">
                        {plan.icon}
                        <h3>{plan.name}</h3>
                      </div>
                      <div className={`card-value-statement ${plan.id}`}>{plan.valueStatement}</div>
                      <p className="card-tagline">{plan.description}</p>
                    </div>

                    <div 
                      className={`card-usage-pill ${plan.id !== 'free' ? 'has-fair-use-tooltip' : ''}`}
                      title={plan.id !== 'free' ? "Paid plans are subject to reasonable fair-use limits to maintain service quality and prevent automated or abusive usage." : undefined}
                    >
                      <Info size={13} />
                      <span>{plan.usage}</span>
                    </div>

                    <div className="card-price-block">
                      <div className="price-num-row">
                        <span className={`price-amount ${isPro ? 'pro-emphasized-price' : ''}`}>{plan.price}</span>
                        {plan.price !== 'Free' && <span className="price-period">{plan.period}</span>}
                      </div>
                      {plan.savings && <span className="price-savings-note">{plan.savings}</span>}
                      {plan.fairUseNote && (
                        <span 
                          className="fair-use-note"
                          title="Paid plans are subject to reasonable fair-use limits to maintain service quality and prevent automated or abusive usage."
                        >
                          <Info size={12} /> {plan.fairUseNote}
                        </span>
                      )}
                    </div>

                    <div className="card-divider" />

                    <ul className="card-feature-list">
                      {plan.allFeatures.map((feat, idx) => (
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
                              <X size={12} />
                            </div>
                          )}
                          <span>{feat.text}</span>
                        </li>
                      ))}
                    </ul>

                    <button
                      type="button"
                      className={`card-cta-btn ${plan.id} ${plan.ctaStyle} ${isActive ? 'active-cta' : ''}`}
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

            {/* TAB 2 & EMBEDDED: Feature Comparison Table underneath pricing cards */}
            <div className="pricing-comparison-section" id="feature-comparison-matrix">
              <div className="comparison-header-row">
                <h4>
                  <Sparkles size={16} color="#46803A" /> Detailed Feature Comparison
                </h4>
                <span className="comparison-subtext">Comprehensive side-by-side breakdown</span>
              </div>

              <div className="comparison-matrix-wrapper">
                <table className="comparison-matrix-table">
                  <thead>
                    <tr>
                      <th className="feature-col">Feature</th>
                      <th className="tier-col free">Starter</th>
                      <th className="tier-col pro">
                        <div className="tier-th-badge">
                          <span>Pro</span>
                          <span className="th-pill-badge">POPULAR</span>
                        </div>
                      </th>
                      <th className="tier-col ultimate">
                        <div className="tier-th-badge">
                          <span>Ultimate</span>
                          <Crown size={13} className="text-amber" />
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonMatrixRows.map((row, idx) => (
                      <tr key={idx} className={row.feature.includes('Price') ? 'price-row' : ''}>
                        <td className="feature-name">{row.feature}</td>
                        <td className="tier-val free">{renderCellContent(row.starter, 'free')}</td>
                        <td className="tier-val pro">{renderCellContent(row.pro, 'pro')}</td>
                        <td className="tier-val ultimate">{renderCellContent(row.ultimate, 'ultimate')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Why These Plans Section */}
            <div className="pricing-why-section">
              <h4 className="why-heading">
                <HelpCircle size={16} color="#46803A" /> Why these plans?
              </h4>
              <div className="why-grid">
                <div className="why-card">
                  <div className="why-card-header">
                    <ShieldCheck size={16} className="text-emerald" />
                    <strong>Starter</strong>
                  </div>
                  <p>Try EviBite's core evidence-grounded food and allergen intelligence at no cost.</p>
                </div>
                <div className="why-card">
                  <div className="why-card-header">
                    <Zap size={16} className="text-emerald" />
                    <strong>Pro</strong>
                  </div>
                  <p>Designed for frequent shoppers who need deeper product, recipe and ingredient analysis.</p>
                </div>
                <div className="why-card">
                  <div className="why-card-header">
                    <Crown size={16} className="text-amber" />
                    <strong>Ultimate</strong>
                  </div>
                  <p>Designed for users who want personalized nutrition targets, meal planning and grocery guidance.</p>
                </div>
              </div>
            </div>

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

            {/* Final Legal & Medical Disclaimer */}
            <div className="pricing-legal-disclaimer">
              <p>
                EviBite AI provides evidence-grounded food and nutrition information. It does not provide certified allergen-free guarantees or replace professional medical or dietary advice.
              </p>
              <p className="pricing-usage-scaling-note">
                Usage limits are designed for normal individual use and may be adjusted as the service scales.
              </p>
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
                <span>Sri Lanka & Global Regional Support</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
