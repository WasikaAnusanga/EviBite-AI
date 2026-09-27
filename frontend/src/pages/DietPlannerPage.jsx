import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Sparkles, 
  ShieldCheck, 
  HeartPulse, 
  Scale, 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle2, 
  AlertTriangle, 
  ShoppingCart, 
  Utensils, 
  Flame, 
  Dna, 
  Activity, 
  DollarSign, 
  ChefHat, 
  Clock, 
  Printer, 
  Copy, 
  RotateCcw,
  Check,
  TrendingDown,
  TrendingUp,
  Dumbbell,
  Shield,
  Zap,
  Info
} from 'lucide-react';
import { generateDietPlan } from '../services/api';
import logoImg from '../logo/logo.png';

export default function DietPlannerPage({ user, onSignOut }) {
  const navigate = useNavigate();

  // Step state: 1: Biometrics, 2: Goals & Activity, 3: Diet & Allergies, 4: Preferences & Budget
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);
  const [dietPlan, setDietPlan] = useState(null);
  const [copiedList, setCopiedList] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    age: 25,
    gender: 'male',
    height: 175,
    weight: 70,
    goal: 'muscle_gain',
    activity: 'moderate_activity',
    diet: 'high_protein',
    allergies: [],
    health_conditions: ['none'],
    food_preferences: 'Oats, chicken, brown rice, greek yogurt',
    foods_to_avoid: '',
    budget: 'medium',
    meal_frequency: '3_meals',
    cooking_preference: 'normal_cooking',
  });

  // Calculate live BMI
  const heightM = (Number(formData.height) || 170) / 100;
  const liveBmi = ((Number(formData.weight) || 70) / (heightM * heightM)).toFixed(1);
  const getBmiCategory = (bmi) => {
    const num = parseFloat(bmi);
    if (num < 18.5) return { label: 'Underweight', color: '#f59e0b', bg: '#fef3c7', pos: '15%' };
    if (num < 25) return { label: 'Normal weight', color: '#10b981', bg: '#ecfdf5', pos: '40%' };
    if (num < 30) return { label: 'Overweight', color: '#f97316', bg: '#ffedd5', pos: '68%' };
    return { label: 'Obesity', color: '#ef4444', bg: '#fee2e2', pos: '90%' };
  };
  const bmiInfo = getBmiCategory(liveBmi);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleAllergy = (allergy) => {
    setFormData(prev => {
      const exists = prev.allergies.includes(allergy);
      const updated = exists 
        ? prev.allergies.filter(a => a !== allergy)
        : [...prev.allergies, allergy];
      return { ...prev, allergies: updated };
    });
  };

  const toggleCondition = (cond) => {
    setFormData(prev => {
      if (cond === 'none') return { ...prev, health_conditions: ['none'] };
      const withoutNone = prev.health_conditions.filter(c => c !== 'none');
      const exists = withoutNone.includes(cond);
      const updated = exists 
        ? withoutNone.filter(c => c !== cond)
        : [...withoutNone, cond];
      return { ...prev, health_conditions: updated.length ? updated : ['none'] };
    });
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setError(null);
    setLoadingStep(1);

    const stepInterval = setInterval(() => {
      setLoadingStep(prev => (prev < 4 ? prev + 1 : prev));
    }, 1800);

    try {
      const payload = {
        age: parseInt(formData.age, 10),
        gender: formData.gender,
        height: parseFloat(formData.height),
        weight: parseFloat(formData.weight),
        goal: formData.goal,
        activity: formData.activity,
        diet: formData.diet,
        allergies: formData.allergies,
        health_conditions: formData.health_conditions,
        food_preferences: formData.food_preferences,
        foods_to_avoid: formData.foods_to_avoid,
        budget: formData.budget,
        meal_frequency: formData.meal_frequency,
        cooking_preference: formData.cooking_preference,
      };

      const result = await generateDietPlan(payload);
      clearInterval(stepInterval);
      setDietPlan(result);
    } catch (err) {
      clearInterval(stepInterval);
      setError(err.message || 'Failed to generate personalized diet plan. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyShoppingList = () => {
    if (!dietPlan?.shopping_list) return;
    const itemsText = dietPlan.shopping_list
      .map(item => `• ${item.name} (${item.brand || 'Supermarket'}) - ${item.quantity} [${item.category}]`)
      .join('\n');
    const fullText = `🛒 EviBite AI - Personalized Supermarket Shopping List\nGoal: ${dietPlan.user_goal}\nTarget Calories: ${dietPlan.daily_targets.daily_calories} kcal\n\n${itemsText}`;
    navigator.clipboard.writeText(fullText);
    setCopiedList(true);
    setTimeout(() => setCopiedList(false), 2500);
  };

  const loadingSteps = [
    'Computing biometric energy profile and Mifflin-St Jeor BMR...',
    'Scanning live supermarket database for goal-compatible foods...',
    'Ranking products via multi-factor nutrition & budget engine...',
    'Running safety guardrails & allergen conflict checks...',
    'Synthesizing clinical dietitian meal strategy via Gemini AI...',
  ];

  return (
    <div className="diet-planner-layout">
      {/* Top Navbar */}
      <header className="diet-header">
        <div className="diet-header-left">
          <Link to="/" className="diet-logo-link">
            <img src={logoImg} alt="EviBite AI" className="diet-logo-img" />
            <div className="diet-brand-text">
              <span className="brand-title">EviBite AI</span>
              <span className="brand-badge">Diet & Nutrition Planning Agent</span>
            </div>
          </Link>
        </div>
        <div className="diet-header-right">
          <Link to="/chat" className="diet-nav-btn secondary">
            <Utensils size={15} />
            <span>Chat Assistant</span>
          </Link>
          {dietPlan && (
            <button 
              onClick={() => setDietPlan(null)} 
              className="diet-nav-btn primary"
            >
              <RotateCcw size={15} />
              <span>New Plan</span>
            </button>
          )}
        </div>
      </header>

      <main className="diet-main-container">
        {/* Loading Overlay */}
        {isLoading && (
          <div className="diet-loading-overlay">
            <div className="diet-loading-card">
              <div className="loading-spinner-ring">
                <Sparkles size={36} className="sparkle-pulse" />
              </div>
              <h2 className="loading-title">Diet & Nutrition Planning Agent</h2>
              <p className="loading-subtitle">Synthesizing personalized supermarket diet plan</p>
              
              <div className="loading-progress-stages">
                {loadingSteps.map((step, idx) => (
                  <div 
                    key={idx} 
                    className={`loading-stage-item ${loadingStep === idx ? 'active' : loadingStep > idx ? 'done' : 'pending'}`}
                  >
                    <div className="stage-icon">
                      {loadingStep > idx ? <CheckCircle2 size={16} className="text-emerald" /> : <div className="stage-dot" />}
                    </div>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ERROR NOTICE */}
        {error && (
          <div className="diet-error-banner">
            <AlertTriangle size={20} />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="error-close-btn">&times;</button>
          </div>
        )}

        {/* ============================================================== */}
        {/* RESULT VIEW (PART 10) */}
        {/* ============================================================== */}
        {dietPlan && !isLoading && (
          <div className="diet-result-view animate-fade-in">
            {/* Hero Summary Card */}
            <div className="result-hero-banner">
              <div className="result-hero-content">
                <div className="hero-pill-badge">
                  <Sparkles size={14} />
                  <span>Agent Personalized Plan</span>
                </div>
                <h1 className="result-hero-title">Your Nutrition Blueprint</h1>
                <p className="result-hero-desc">
                  Optimized for <strong>{dietPlan.user_goal}</strong> under a <strong>{dietPlan.user_diet}</strong> lifestyle.
                  All items verified against live supermarket inventory.
                </p>
                <div className="result-meta-tags">
                  <span className="meta-tag">
                    <strong>BMI:</strong> {dietPlan.daily_targets.bmi} ({dietPlan.daily_targets.bmi_category})
                  </span>
                  <span className="meta-tag">
                    <strong>BMR:</strong> {dietPlan.daily_targets.bmr} kcal
                  </span>
                  <span className="meta-tag">
                    <strong>TDEE:</strong> {dietPlan.daily_targets.tdee} kcal
                  </span>
                  <span className="meta-tag safe">
                    <ShieldCheck size={14} />
                    {dietPlan.safety_summary}
                  </span>
                </div>
              </div>
              <div className="result-hero-actions">
                <button onClick={() => window.print()} className="action-btn-outline">
                  <Printer size={16} />
                  <span>Print Plan</span>
                </button>
                <button onClick={handleCopyShoppingList} className="action-btn-primary">
                  {copiedList ? <Check size={16} /> : <Copy size={16} />}
                  <span>{copiedList ? 'Copied List!' : 'Copy Shopping List'}</span>
                </button>
              </div>
            </div>

            {/* Daily Target Dashboard */}
            <div className="targets-grid">
              <div className="target-card calories-card">
                <div className="target-card-header">
                  <Flame size={18} className="text-orange" />
                  <span>Daily Calories</span>
                </div>
                <div className="target-value">{dietPlan.daily_targets.daily_calories}</div>
                <div className="target-unit">kcal / day</div>
                <div className="target-subtext">Calibrated for {dietPlan.user_goal}</div>
              </div>

              <div className="target-card protein-card">
                <div className="target-card-header">
                  <Dna size={18} className="text-indigo" />
                  <span>Protein Target</span>
                </div>
                <div className="target-value">{dietPlan.daily_targets.protein_target}g</div>
                <div className="target-unit">{Math.round((dietPlan.daily_targets.protein_target * 4 / dietPlan.daily_targets.daily_calories) * 100)}% of daily energy</div>
                <div className="target-subtext">Supports muscle repair & retention</div>
              </div>

              <div className="target-card carbs-card">
                <div className="target-card-header">
                  <Activity size={18} className="text-emerald" />
                  <span>Carbohydrates</span>
                </div>
                <div className="target-value">{dietPlan.daily_targets.carbs_target}g</div>
                <div className="target-unit">{Math.round((dietPlan.daily_targets.carbs_target * 4 / dietPlan.daily_targets.daily_calories) * 100)}% of daily energy</div>
                <div className="target-subtext">Sustained glycemic energy fuel</div>
              </div>

              <div className="target-card fat-card">
                <div className="target-card-header">
                  <HeartPulse size={18} className="text-rose" />
                  <span>Essential Fats</span>
                </div>
                <div className="target-value">{dietPlan.daily_targets.fat_target}g</div>
                <div className="target-unit">{Math.round((dietPlan.daily_targets.fat_target * 9 / dietPlan.daily_targets.daily_calories) * 100)}% of daily energy</div>
                <div className="target-subtext">Hormone balance & joint health</div>
              </div>
            </div>

            {/* Micro Limits Banner */}
            <div className="micro-limits-banner">
              <div className="micro-item">
                <span className="micro-label">Dietary Fiber</span>
                <span className="micro-val">≥ {dietPlan.daily_targets.fiber_target}g</span>
              </div>
              <div className="micro-item">
                <span className="micro-label">Max Refined Sugar</span>
                <span className="micro-val">≤ {dietPlan.daily_targets.sugar_limit}g</span>
              </div>
              <div className="micro-item">
                <span className="micro-label">Max Sodium Limit</span>
                <span className="micro-val">≤ {dietPlan.daily_targets.sodium_limit_mg}mg</span>
              </div>
              <div className="micro-item">
                <span className="micro-label">Meal Cadence</span>
                <span className="micro-val">{dietPlan.meals.length} Scheduled Meals</span>
              </div>
            </div>

            {/* Dietitian Clinical Strategy (Gemini Explanation) */}
            <div className="explanation-card">
              <div className="explanation-header">
                <div className="explanation-title-wrap">
                  <Sparkles size={20} className="text-emerald" />
                  <h2>AI Dietitian Clinical Strategy & Rationale</h2>
                </div>
                <span className="llm-model-badge">Gemini Flash Intelligence</span>
              </div>
              <div className="explanation-body markdown-prose">
                {dietPlan.explanation.split('\n\n').map((paragraph, pIdx) => {
                  if (paragraph.startsWith('### ') || paragraph.startsWith('#### ')) {
                    return <h3 key={pIdx} className="prose-heading">{paragraph.replace(/^#+\s*/, '')}</h3>;
                  }
                  if (paragraph.startsWith('* ') || paragraph.startsWith('- ')) {
                    return (
                      <ul key={pIdx} className="prose-list">
                        {paragraph.split('\n').map((line, lIdx) => (
                          <li key={lIdx}>{line.replace(/^[\*\-]\s*/, '')}</li>
                        ))}
                      </ul>
                    );
                  }
                  return <p key={pIdx}>{paragraph}</p>;
                })}
              </div>
            </div>

            {/* Daily Meals Section */}
            <div className="meals-section">
              <div className="section-title-wrap">
                <Utensils size={22} className="text-emerald" />
                <div>
                  <h2 className="section-title">Personalized Supermarket Meal Structure</h2>
                  <p className="section-desc">Genuine packaged products with calculated portions and nutritional values</p>
                </div>
              </div>

              <div className="meal-slots-grid">
                {dietPlan.meals.map((meal, mIdx) => (
                  <div key={mIdx} className="meal-slot-card">
                    <div className="meal-slot-header">
                      <div>
                        <h3 className="meal-slot-name">{meal.meal_name}</h3>
                        <span className="slot-target-tag">Target: {meal.target_calories} kcal</span>
                      </div>
                      <div className="slot-macro-pill">
                        <span className="actual-cal">{meal.actual_calories} kcal</span>
                        <span className="macro-breakdown">
                          P: {meal.actual_protein_g}g | C: {meal.actual_carbs_g}g | F: {meal.actual_fat_g}g
                        </span>
                      </div>
                    </div>

                    <div className="meal-items-list">
                      {meal.items.map((item, iIdx) => (
                        <div key={iIdx} className="product-meal-card">
                          <div className="product-card-top-content">
                            <div className="product-title-row">
                              <h4 className="product-item-name">{item.product.name}</h4>
                            </div>
                            <div className="product-meta-row">
                              {item.product.brand && (
                                <span className="brand-pill">{item.product.brand}</span>
                              )}
                              <span className="portion-pill">{item.serving_label}</span>
                              {item.product.barcode && (
                                <span className="barcode-pill">#{item.product.barcode}</span>
                              )}
                              <span className="safe-pill">
                                <ShieldCheck size={12} />
                                <span>Verified Safe</span>
                              </span>
                            </div>
                          </div>
                          
                          <div className="product-macros-ribbon">
                            <div className="macro-chip cal">
                              <Flame size={13} />
                              <span><strong>{item.calories}</strong> kcal</span>
                            </div>
                            <div className="macro-chip prot">
                              <Dna size={13} />
                              <span><strong>{item.protein_g}g</strong> protein</span>
                            </div>
                            <div className="macro-chip carbs">
                              <Activity size={13} />
                              <span><strong>{item.carbs_g}g</strong> carbs</span>
                            </div>
                            <div className="macro-chip fat">
                              <HeartPulse size={13} />
                              <span><strong>{item.fat_g}g</strong> fat</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Shopping List Section */}
            <div className="shopping-section">
              <div className="shopping-header">
                <div className="section-title-wrap">
                  <ShoppingCart size={22} className="text-emerald" />
                  <div>
                    <h2 className="section-title">Consolidated Supermarket Shopping List</h2>
                    <p className="section-desc">Grounded supermarket items to pick up at your local grocery store</p>
                  </div>
                </div>
                <button onClick={handleCopyShoppingList} className="copy-list-btn">
                  {copiedList ? <Check size={15} /> : <Copy size={15} />}
                  <span>{copiedList ? 'Copied to Clipboard!' : 'Copy Shopping List'}</span>
                </button>
              </div>

              <div className="shopping-grid">
                {dietPlan.shopping_list.map((item, sIdx) => (
                  <div key={sIdx} className="shopping-card">
                    <div className="shopping-card-top">
                      <span className="shopping-cat-badge">{item.category}</span>
                      <span className="shopping-meal-badge">{item.meal_slot}</span>
                    </div>
                    <h4 className="shopping-item-name">{item.name}</h4>
                    {item.brand && <div className="shopping-brand">{item.brand}</div>}
                    <div className="shopping-bottom-row">
                      <span className="shopping-qty">{item.quantity}</span>
                      {item.barcode && <span className="shopping-code">#{item.barcode}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="result-bottom-bar">
              <button onClick={() => setDietPlan(null)} className="btn-secondary">
                <ArrowLeft size={16} />
                <span>Adjust Health Profile & Regenerate</span>
              </button>
              <Link to="/chat" className="btn-primary">
                <span>Ask EviBite AI About This Plan</span>
                <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* INTERACTIVE FORM VIEW (PART 1) */}
        {/* ============================================================== */}
        {!dietPlan && (
          <div className="diet-form-wrapper">
            <div className="diet-form-card animate-fade-in">
              {/* Form Header */}
              <div className="form-header">
                <div className="agent-badge">
                  <Sparkles size={14} />
                  <span>AI Diet & Nutrition Planning Agent</span>
                </div>
                <h1 className="form-title">Personalized Diet & Nutrition Planner</h1>
                <p className="form-desc">
                  Provide your health parameters and dietary preferences. Our intelligent agent calculates 
                  your nutritional requirements, validates against your allergies, and selects products from 
                  the supermarket database.
                </p>
              </div>

              {/* Step Wizard Tracker */}
              <div className="step-tracker-grid">
                {[
                  { step: 1, label: 'Biometrics', desc: 'Age, gender & body stats' },
                  { step: 2, label: 'Goals & Activity', desc: 'Caloric targets & energy' },
                  { step: 3, label: 'Diet & Allergies', desc: 'Safety guardrails' },
                  { step: 4, label: 'Preferences', desc: 'Budget & meal cadence' },
                ].map((s) => (
                  <button
                    key={s.step}
                    type="button"
                    onClick={() => {
                      if (currentStep > s.step) setCurrentStep(s.step);
                    }}
                    className={`step-card ${currentStep === s.step ? 'active' : currentStep > s.step ? 'completed' : 'pending'}`}
                  >
                    <div className="step-card-top">
                      <div className="step-circle">
                        {currentStep > s.step ? <Check size={14} /> : s.step}
                      </div>
                      <span className="step-card-num">Step {s.step}</span>
                    </div>
                    <span className="step-card-title">{s.label}</span>
                    <span className="step-card-desc">{s.desc}</span>
                  </button>
                ))}
              </div>

              <form onSubmit={handleSubmit} className="diet-wizard-form">
                {/* STEP 1: BIOMETRICS */}
                {currentStep === 1 && (
                  <div className="step-content animate-slide">
                    <div className="step-section-heading">
                      <Scale size={20} className="text-emerald" />
                      <div>
                        <h3>Basic Biometric Information</h3>
                        <p>Used to calculate your Basal Metabolic Rate (BMR) and daily energy expenditure</p>
                      </div>
                    </div>

                    <div className="form-fields-stack">
                      {/* Row 1: Age & Biological Gender */}
                      <div className="form-row-2">
                        <div className="form-group">
                          <label className="form-label">Age (years)</label>
                          <div className="input-with-unit">
                            <input 
                              type="number" 
                              min="10" 
                              max="110" 
                              value={formData.age} 
                              onChange={(e) => handleInputChange('age', e.target.value)}
                              className="form-input"
                              placeholder="25"
                              required 
                            />
                            <span className="input-unit-badge">yrs</span>
                          </div>
                        </div>

                        <div className="form-group">
                          <label className="form-label">Biological Gender</label>
                          <div className="segmented-control">
                            {['male', 'female', 'other'].map(g => (
                              <button
                                key={g}
                                type="button"
                                onClick={() => handleInputChange('gender', g)}
                                className={`segment-btn ${formData.gender === g ? 'active' : ''}`}
                              >
                                {g.charAt(0).toUpperCase() + g.slice(1)}
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Row 2: Height & Weight */}
                      <div className="form-row-2">
                        <div className="form-group">
                          <label className="form-label">Height (cm)</label>
                          <div className="input-with-unit">
                            <input 
                              type="number" 
                              min="90" 
                              max="240" 
                              value={formData.height} 
                              onChange={(e) => handleInputChange('height', e.target.value)}
                              className="form-input"
                              placeholder="175"
                              required 
                            />
                            <span className="input-unit-badge">cm</span>
                          </div>
                        </div>

                        <div className="form-group">
                          <label className="form-label">Weight (kg)</label>
                          <div className="input-with-unit">
                            <input 
                              type="number" 
                              min="30" 
                              max="260" 
                              value={formData.weight} 
                              onChange={(e) => handleInputChange('weight', e.target.value)}
                              className="form-input"
                              placeholder="70"
                              required 
                            />
                            <span className="input-unit-badge">kg</span>
                          </div>
                        </div>
                      </div>

                      {/* Live BMI Visual Gauge Banner */}
                      <div className="bmi-gauge-card">
                        <div className="bmi-gauge-left">
                          <div className="bmi-score-pill" style={{ backgroundColor: bmiInfo.bg, borderColor: bmiInfo.color }}>
                            <span className="bmi-score-num" style={{ color: bmiInfo.color }}>{liveBmi}</span>
                            <span className="bmi-score-lbl">BMI</span>
                          </div>
                          <div className="bmi-gauge-details">
                            <div className="bmi-cat-name" style={{ color: bmiInfo.color }}>
                              {bmiInfo.label}
                            </div>
                            <span className="bmi-cat-subtext">WHO Clinical Classification</span>
                          </div>
                        </div>

                        <div className="bmi-gauge-right">
                          <div className="bmi-scale-bar">
                            <div className="scale-segment under" title="Underweight (<18.5)">Under</div>
                            <div className="scale-segment normal" title="Normal (18.5-24.9)">Normal</div>
                            <div className="scale-segment over" title="Overweight (25-29.9)">Over</div>
                            <div className="scale-segment obese" title="Obese (≥30)">Obese</div>
                            <div 
                              className="scale-pin" 
                              style={{ left: bmiInfo.pos }}
                              title={`Current BMI: ${liveBmi}`}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="step-nav-bar right-only">
                      <button 
                        type="button" 
                        onClick={() => setCurrentStep(2)} 
                        className="btn-step-next"
                      >
                        <span>Continue to Goals & Activity</span>
                        <ArrowRight size={16} />
                      </button>
                    </div>
                  </div>
                )}

                {/* STEP 2: GOALS & ACTIVITY */}
                {currentStep === 2 && (
                  <div className="step-content animate-slide">
                    <div className="step-section-heading">
                      <Flame size={20} className="text-emerald" />
                      <div>
                        <h3>Primary Health Goal & Physical Activity</h3>
                        <p>Determines your caloric surplus or deficit and macronutrient targets</p>
                      </div>
                    </div>

                    {/* Goals Grid */}
                    <div className="form-group mb-6">
                      <label className="form-label">Select Your Health Goal</label>
                      <div className="goals-cards-grid">
                        {[
                          { id: 'weight_loss', label: 'Weight Loss', desc: 'Caloric deficit with high protein satiety', icon: TrendingDown },
                          { id: 'weight_gain', label: 'Weight Gain', desc: 'Calorie surplus with nutrient-dense fuel', icon: TrendingUp },
                          { id: 'muscle_gain', label: 'Muscle Gain', desc: 'Lean surplus + high protein for hypertrophy', icon: Dumbbell },
                          { id: 'maintain_weight', label: 'Maintain Weight', desc: 'Energetic maintenance equilibrium', icon: Shield },
                          { id: 'general_health', label: 'General Health', desc: 'Balanced macronutrients & micronutrients', icon: HeartPulse },
                        ].map(g => {
                          const IconComp = g.icon;
                          const isSelected = formData.goal === g.id;
                          return (
                            <div 
                              key={g.id}
                              onClick={() => handleInputChange('goal', g.id)}
                              className={`card-tile ${isSelected ? 'active' : ''}`}
                            >
                              <div className="card-tile-top">
                                <div className={`tile-icon-box ${isSelected ? 'active' : ''}`}>
                                  <IconComp size={18} />
                                </div>
                                {isSelected && <CheckCircle2 size={16} className="text-emerald" />}
                              </div>
                              <span className="card-tile-title">{g.label}</span>
                              <span className="card-tile-desc">{g.desc}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Activity Level Grid */}
                    <div className="form-group mb-6">
                      <label className="form-label">Daily Physical Activity Level</label>
                      <div className="activity-cards-grid">
                        {[
                          { id: 'sedentary', label: 'Sedentary', factor: '1.20x', desc: 'Desk job, little to no exercise' },
                          { id: 'light_activity', label: 'Light Activity', factor: '1.38x', desc: 'Light workouts 1-3 days/week' },
                          { id: 'moderate_activity', label: 'Moderate Activity', factor: '1.55x', desc: 'Moderate exercise 3-5 days/week' },
                          { id: 'very_active', label: 'Very Active', factor: '1.73x', desc: 'Hard training 6-7 days/week' },
                          { id: 'athlete', label: 'Athlete', factor: '1.90x', desc: 'Intensive daily training or physical labor' },
                        ].map(a => {
                          const isSelected = formData.activity === a.id;
                          return (
                            <div 
                              key={a.id}
                              onClick={() => handleInputChange('activity', a.id)}
                              className={`card-tile ${isSelected ? 'active' : ''}`}
                            >
                              <div className="card-tile-top">
                                <span className="factor-tag">{a.factor}</span>
                                {isSelected && <CheckCircle2 size={16} className="text-emerald" />}
                              </div>
                              <span className="card-tile-title">{a.label}</span>
                              <span className="card-tile-desc">{a.desc}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="step-nav-bar">
                      <button type="button" onClick={() => setCurrentStep(1)} className="btn-step-prev">
                        <ArrowLeft size={16} />
                        <span>Back</span>
                      </button>
                      <button type="button" onClick={() => setCurrentStep(3)} className="btn-step-next">
                        <span>Continue to Diet & Allergies</span>
                        <ArrowRight size={16} />
                      </button>
                    </div>
                  </div>
                )}

                {/* STEP 3: DIET & ALLERGIES */}
                {currentStep === 3 && (
                  <div className="step-content animate-slide">
                    <div className="step-section-heading">
                      <ShieldCheck size={20} className="text-emerald" />
                      <div>
                        <h3>Dietary Pattern, Allergies & Health Conditions</h3>
                        <p>Strict safety guardrails to ensure 100% compliant supermarket foods</p>
                      </div>
                    </div>

                    {/* Diet Preference */}
                    <div className="form-group mb-6">
                      <label className="form-label">Dietary Lifestyle</label>
                      <div className="diet-options-grid">
                        {[
                          { id: 'non_vegetarian', label: 'Non Vegetarian', desc: 'All supermarket proteins & dairy' },
                          { id: 'vegetarian', label: 'Vegetarian', desc: 'Plant-based foods, dairy & eggs' },
                          { id: 'vegan', label: 'Vegan', desc: '100% plant-based, zero animal ingredients' },
                          { id: 'high_protein', label: 'High Protein', desc: '35% protein distribution target' },
                          { id: 'keto', label: 'Keto Diet', desc: 'Ultra low carb (< 30g net carbs) & healthy fats' },
                          { id: 'low_carb', label: 'Low Carb', desc: 'Controlled complex carbohydrate intake' },
                        ].map(d => {
                          const isSelected = formData.diet === d.id;
                          return (
                            <button
                              key={d.id}
                              type="button"
                              onClick={() => handleInputChange('diet', d.id)}
                              className={`diet-option-card ${isSelected ? 'active' : ''}`}
                            >
                              <div className="diet-option-top">
                                <span className="diet-option-name">{d.label}</span>
                                {isSelected && <CheckCircle2 size={16} className="text-emerald" />}
                              </div>
                              <span className="diet-option-desc">{d.desc}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Allergies Multi-Select */}
                    <div className="form-group mb-6">
                      <label className="form-label">
                        Declared Allergies 
                        <span className="label-hint"> (Multi-select: items containing these ingredients will be strictly removed)</span>
                      </label>
                      <div className="allergy-options-grid">
                        {[
                          'Milk', 
                          'Eggs', 
                          'Peanuts', 
                          'Tree Nuts', 
                          'Gluten', 
                          'Seafood', 
                          'Soy', 
                          'Other'
                        ].map(alg => {
                          const algLower = alg.toLowerCase();
                          const isSelected = formData.allergies.includes(algLower);
                          return (
                            <button
                              key={alg}
                              type="button"
                              onClick={() => toggleAllergy(algLower)}
                              className={`allergy-card-btn ${isSelected ? 'selected-danger' : ''}`}
                            >
                              <div className={`checkbox-indicator ${isSelected ? 'checked' : ''}`}>
                                {isSelected && <Check size={12} />}
                              </div>
                              <span className="allergy-text">{alg}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Health Conditions */}
                    <div className="form-group mb-6">
                      <label className="form-label">
                        Diagnosed Health Conditions 
                        <span className="label-hint"> (Automatically enforces clinical sodium, sugar & fiber thresholds)</span>
                      </label>
                      <div className="condition-options-grid">
                        {[
                          { id: 'none', label: 'None', hint: 'Standard healthy parameters' },
                          { id: 'diabetes', label: 'Diabetes', hint: 'Sugar capped at ≤ 20g/day, fiber boost' },
                          { id: 'high_blood_pressure', label: 'High Blood Pressure', hint: 'DASH sodium capped at ≤ 1500mg' },
                          { id: 'high_cholesterol', label: 'High Cholesterol', hint: 'Low saturated fat & high soluble fiber' },
                        ].map(cond => {
                          const isSelected = formData.health_conditions.includes(cond.id);
                          return (
                            <button
                              key={cond.id}
                              type="button"
                              onClick={() => toggleCondition(cond.id)}
                              className={`condition-card-btn ${isSelected ? 'active' : ''}`}
                            >
                              <div className={`checkbox-indicator ${isSelected ? 'checked' : ''}`}>
                                {isSelected && <Check size={12} />}
                              </div>
                              <div className="condition-info">
                                <span className="cond-title">{cond.label}</span>
                                <span className="cond-hint">{cond.hint}</span>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="step-nav-bar">
                      <button type="button" onClick={() => setCurrentStep(2)} className="btn-step-prev">
                        <ArrowLeft size={16} />
                        <span>Back</span>
                      </button>
                      <button type="button" onClick={() => setCurrentStep(4)} className="btn-step-next">
                        <span>Continue to Preferences & Routine</span>
                        <ArrowRight size={16} />
                      </button>
                    </div>
                  </div>
                )}

                {/* STEP 4: PREFERENCES & BUDGET */}
                {currentStep === 4 && (
                  <div className="step-content animate-slide">
                    <div className="step-section-heading">
                      <ChefHat size={20} className="text-emerald" />
                      <div>
                        <h3>Food Preferences, Budget & Meal Routine</h3>
                        <p>Tailors product recommendations, meal frequency, and cooking complexity</p>
                      </div>
                    </div>

                    <div className="form-fields-stack">
                      {/* Free Text Preferences */}
                      <div className="form-row-2">
                        <div className="form-group">
                          <label className="form-label">Food Preferences</label>
                          <input 
                            type="text" 
                            value={formData.food_preferences} 
                            onChange={(e) => handleInputChange('food_preferences', e.target.value)}
                            placeholder="e.g. Rice, chicken, oats, greek yogurt, berries"
                            className="form-input" 
                          />
                          <span className="field-hint">Ingredients or foods you love</span>
                        </div>

                        <div className="form-group">
                          <label className="form-label">Foods to Avoid</label>
                          <input 
                            type="text" 
                            value={formData.foods_to_avoid} 
                            onChange={(e) => handleInputChange('foods_to_avoid', e.target.value)}
                            placeholder="e.g. Pork, spicy food, artificial sweeteners"
                            className="form-input" 
                          />
                          <span className="field-hint">Disliked or unwanted ingredients</span>
                        </div>
                      </div>

                      {/* 3-Column Routine Setup */}
                      <div className="form-row-3 mt-4">
                        <div className="form-group">
                          <label className="form-label">Budget Level</label>
                          <div className="segmented-vertical">
                            {[
                              { id: 'low', label: 'Low', desc: 'Cost-effective bulk staples' },
                              { id: 'medium', label: 'Medium', desc: 'Balanced grocery mix' },
                              { id: 'high', label: 'High', desc: 'Specialty & organic brands' },
                            ].map(b => (
                              <button
                                key={b.id}
                                type="button"
                                onClick={() => handleInputChange('budget', b.id)}
                                className={`segment-card-btn ${formData.budget === b.id ? 'active' : ''}`}
                              >
                                <span className="btn-main-txt">{b.label}</span>
                                <span className="btn-sub-txt">{b.desc}</span>
                              </button>
                            ))}
                          </div>
                        </div>

                        <div className="form-group">
                          <label className="form-label">Daily Meal Cadence</label>
                          <div className="segmented-vertical">
                            {[
                              { id: '3_meals', label: '3 Meals', desc: 'Breakfast, Lunch, Dinner' },
                              { id: '4_meals', label: '4 Meals', desc: 'With 1 snack' },
                              { id: '5_meals', label: '5 Meals', desc: 'With 2 snacks' },
                              { id: '6_meals', label: '6 Meals', desc: 'Frequent smaller portions' },
                            ].map(f => (
                              <button
                                key={f.id}
                                type="button"
                                onClick={() => handleInputChange('meal_frequency', f.id)}
                                className={`segment-card-btn ${formData.meal_frequency === f.id ? 'active' : ''}`}
                              >
                                <span className="btn-main-txt">{f.label}</span>
                                <span className="btn-sub-txt">{f.desc}</span>
                              </button>
                            ))}
                          </div>
                        </div>

                        <div className="form-group">
                          <label className="form-label">Cooking Preference</label>
                          <div className="segmented-vertical">
                            {[
                              { id: 'no_cooking', label: 'No Cooking', desc: 'Ready-to-eat packaged items' },
                              { id: 'simple_cooking', label: 'Simple Cooking', desc: 'Quick 10-min preparation' },
                              { id: 'normal_cooking', label: 'Normal Cooking', desc: 'Standard recipes & cooking' },
                            ].map(c => (
                              <button
                                key={c.id}
                                type="button"
                                onClick={() => handleInputChange('cooking_preference', c.id)}
                                className={`segment-card-btn ${formData.cooking_preference === c.id ? 'active' : ''}`}
                              >
                                <span className="btn-main-txt">{c.label}</span>
                                <span className="btn-sub-txt">{c.desc}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="step-nav-bar mt-8">
                      <button type="button" onClick={() => setCurrentStep(3)} className="btn-step-prev">
                        <ArrowLeft size={16} />
                        <span>Back</span>
                      </button>
                      <button type="submit" className="btn-generate-plan">
                        <Sparkles size={18} />
                        <span>Generate Personalized Diet Plan</span>
                      </button>
                    </div>
                  </div>
                )}
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
