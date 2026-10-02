import React, { useState, useEffect, useRef } from 'react';
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
  ShieldAlert, 
  Globe, 
  Zap, 
  Info, 
  Loader2, 
  User, 
  LogOut,
  Bookmark,
  BookmarkCheck,
  Trash2,
  Calendar,
  X,
  ChevronDown,
  MessageSquare
} from 'lucide-react';
import { generateDietPlan, saveUserDietPlan, fetchUserDietPlans, deleteUserDietPlan } from '../services/api';
import logoImg from '../logo/logo.png';
import ClinicalRationale from '../components/ClinicalRationale';

export default function DietPlannerPage({ user, onSignOut }) {
  const navigate = useNavigate();

  // Step state: 1: Biometrics, 2: Goals & Activity, 3: Diet & Allergies, 4: Preferences & Budget
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);
  const [dietPlan, setDietPlan] = useState(null);
  const [copiedList, setCopiedList] = useState(false);
  const [otherAllergyText, setOtherAllergyText] = useState('');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Profile Dropdown State
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const profileRef = useRef(null);

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return parts[0].slice(0, 2).toUpperCase();
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Saved Plans State
  const [savedPlans, setSavedPlans] = useState([]);
  const [isSavedPlansOpen, setIsSavedPlansOpen] = useState(false);
  const [isSavingPlan, setIsSavingPlan] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');
  const [planToDelete, setPlanToDelete] = useState(null);
  const [isDeletingPlan, setIsDeletingPlan] = useState(false);

  const userId = user ? (user.id || user.email) : null;

  // Load saved diet plans on mount or when user updates
  useEffect(() => {
    async function loadSavedPlans() {
      if (userId) {
        const plans = await fetchUserDietPlans(userId);
        setSavedPlans(plans);
      }
    }
    loadSavedPlans();
  }, [userId]);

  // Handle ESC key to dismiss modals cleanly
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (planToDelete && !isDeletingPlan) {
          setPlanToDelete(null);
        } else if (isSavedPlansOpen) {
          setIsSavedPlansOpen(false);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [planToDelete, isDeletingPlan, isSavedPlansOpen]);

  // Form State
  // Form State - Empty biometrics so user enters their own data cleanly without autofill
  const [formData, setFormData] = useState({
    age: '',
    gender: '',
    height: '',
    weight: '',
    goal: 'weight_loss',
    activity: 'moderate_activity',
    diet: 'non_vegetarian',
    allergies: [],
    health_conditions: ['none'],
    food_preferences: '',
    foods_to_avoid: '',
    budget: 'medium',
    meal_frequency: '3_meals',
    cooking_preference: 'normal_cooking',
    country: 'United States',
  });

  const [errors, setErrors] = useState({});

  // Calculate live BMI safely when height and weight are provided
  const parsedHeight = parseFloat(formData.height);
  const parsedWeight = parseFloat(formData.weight);
  const hasValidBmi = !isNaN(parsedHeight) && parsedHeight >= 80 && !isNaN(parsedWeight) && parsedWeight >= 25;
  const liveBmi = hasValidBmi 
    ? (parsedWeight / ((parsedHeight / 100) ** 2)).toFixed(1) 
    : '--';

  const getBmiCategory = (bmi) => {
    const num = parseFloat(bmi);
    if (isNaN(num)) return { label: 'Enter height & weight', color: '#64748b', bg: '#f1f5f9', pos: '0%' };
    if (num < 18.5) return { label: 'Underweight', color: '#f59e0b', bg: '#fef3c7', pos: '15%' };
    if (num < 25) return { label: 'Normal weight', color: '#10b981', bg: '#ecfdf5', pos: '40%' };
    if (num < 30) return { label: 'Overweight', color: '#f97316', bg: '#ffedd5', pos: '68%' };
    return { label: 'Obesity', color: '#ef4444', bg: '#fee2e2', pos: '90%' };
  };
  const bmiInfo = getBmiCategory(liveBmi);

  const validateStep = (step) => {
    const errs = {};

    if (step === 1) {
      const ageNum = parseInt(formData.age, 10);
      if (!formData.age || isNaN(ageNum)) {
        errs.age = 'Please enter your age';
      } else if (ageNum < 10 || ageNum > 120) {
        errs.age = 'Age must be between 10 and 120 years';
      }

      if (!formData.gender) {
        errs.gender = 'Please select your biological gender';
      }

      const heightNum = parseFloat(formData.height);
      if (!formData.height || isNaN(heightNum)) {
        errs.height = 'Please enter your height';
      } else if (heightNum < 80 || heightNum > 250) {
        errs.height = 'Height must be between 80 and 250 cm';
      }

      const weightNum = parseFloat(formData.weight);
      if (!formData.weight || isNaN(weightNum)) {
        errs.weight = 'Please enter your weight';
      } else if (weightNum < 25 || weightNum > 300) {
        errs.weight = 'Weight must be between 25 and 300 kg';
      }

      if (!formData.country) {
        errs.country = 'Please select your country or regional market';
      }
    }

    if (step === 2) {
      if (!formData.goal) errs.goal = 'Please select a primary health goal';
      if (!formData.activity) errs.activity = 'Please select your daily physical activity level';
    }

    if (step === 3) {
      if (!formData.diet) errs.diet = 'Please select your dietary lifestyle';
    }

    if (step === 4) {
      if (!formData.budget) errs.budget = 'Please select a budget tier';
      if (!formData.meal_frequency) errs.meal_frequency = 'Please select meal cadence';
      if (!formData.cooking_preference) errs.cooking_preference = 'Please select cooking preference';
    }

    return errs;
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => {
        const updated = { ...prev };
        delete updated[field];
        return updated;
      });
    }
  };

  const goToStep = (targetStep) => {
    if (targetStep > currentStep) {
      const stepErrors = validateStep(currentStep);
      if (Object.keys(stepErrors).length > 0) {
        setErrors(stepErrors);
        return;
      }
    }
    setErrors({});
    setCurrentStep(targetStep);
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

    // Validate all steps (1 to 4) before generating
    for (let s = 1; s <= 4; s++) {
      const stepErrors = validateStep(s);
      if (Object.keys(stepErrors).length > 0) {
        setErrors(stepErrors);
        setCurrentStep(s);
        setError(`Please fill in all required fields in Step ${s} before generating your plan.`);
        return;
      }
    }

    setIsLoading(true);
    setError(null);
    setLoadingStep(1);
    setElapsedSeconds(0);

    const stepInterval = setInterval(() => {
      setLoadingStep(prev => (prev < 4 ? prev + 1 : prev));
    }, 1800);

    const timerInterval = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);

    try {
      // Process declared allergies: combine standard allergies with custom 'other' text
      let activeAllergies = formData.allergies.filter(a => a !== 'other');
      if (formData.allergies.includes('other') && otherAllergyText.trim()) {
        const customItems = otherAllergyText
          .split(',')
          .map(s => s.trim().toLowerCase())
          .filter(Boolean);
        activeAllergies = Array.from(new Set([...activeAllergies, ...customItems]));
      } else if (formData.allergies.includes('other')) {
        activeAllergies.push('other');
      }

      const payload = {
        user_id: userId,
        age: parseInt(formData.age, 10),
        gender: formData.gender,
        height: parseFloat(formData.height),
        weight: parseFloat(formData.weight),
        goal: formData.goal,
        activity: formData.activity,
        diet: formData.diet,
        allergies: activeAllergies,
        health_conditions: formData.health_conditions,
        food_preferences: formData.food_preferences,
        foods_to_avoid: formData.foods_to_avoid,
        budget: formData.budget,
        meal_frequency: formData.meal_frequency,
        cooking_preference: formData.cooking_preference,
        country: formData.country,
      };

      const result = await generateDietPlan(payload);
      clearInterval(stepInterval);
      clearInterval(timerInterval);
      result.profile = {
        ...formData,
        allergies: activeAllergies
      };
      setDietPlan(result);

      // Auto-save to user profile in MongoDB
      if (userId) {
        try {
          const saveRes = await saveUserDietPlan(userId, result, result.profile);
          if (saveRes?.plan) {
            setSavedPlans(prev => [saveRes.plan, ...prev.filter(p => p.id !== saveRes.plan.id)]);
            setSaveSuccessMsg('Saved to Profile ✓');
          }
        } catch (saveErr) {
          console.error('Auto-save plan notice:', saveErr);
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to generate personalized diet plan. Please try again.');
    } finally {
      clearInterval(stepInterval);
      clearInterval(timerInterval);
      setIsLoading(false);
    }
  };

  const handleManualSave = async () => {
    if (!dietPlan || !userId) return;
    setIsSavingPlan(true);
    try {
      const res = await saveUserDietPlan(userId, dietPlan, dietPlan.profile || formData);
      if (res?.plan) {
        setSavedPlans(prev => [res.plan, ...prev.filter(p => p.id !== res.plan.id)]);
        setSaveSuccessMsg('Saved to Profile ✓');
        setTimeout(() => setSaveSuccessMsg(''), 3500);
      }
    } catch (err) {
      console.error('Manual save failed:', err);
    } finally {
      setIsSavingPlan(false);
    }
  };

  const handlePromptDeletePlan = (plan, e) => {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    setPlanToDelete(plan);
  };

  const handleConfirmDelete = async () => {
    if (!planToDelete) return;
    setIsDeletingPlan(true);
    try {
      const success = await deleteUserDietPlan(planToDelete.id, userId);
      if (success) {
        setSavedPlans(prev => prev.filter(p => p.id !== planToDelete.id));
        setPlanToDelete(null);
      }
    } catch (err) {
      console.error('Delete plan failed:', err);
    } finally {
      setIsDeletingPlan(false);
    }
  };

  const handleCancelDelete = () => {
    if (isDeletingPlan) return;
    setPlanToDelete(null);
  };

  const handleSelectSavedPlan = (plan) => {
    setDietPlan(plan);
    if (plan.profile) {
      setFormData(prev => ({
        ...prev,
        ...plan.profile,
      }));
    }
    setIsSavedPlansOpen(false);
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

  const handlePrintPlan = () => {
    const originalTitle = document.title;
    const country = (dietPlan?.user_country || formData?.country || 'Supermarket').replace(/\s+/g, '_');
    const goal = (dietPlan?.user_goal || 'Diet_Plan').replace(/\s+/g, '_');
    document.title = `EviBite_DietPlan_${country}_${goal}`;
    window.print();
    setTimeout(() => {
      document.title = originalTitle;
    }, 1200);
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
      {/* HEADER NAVBAR */}
      <header className="landing-nav">
        <div className="landing-nav-container">
          <div className="landing-brand" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
            <img src={logoImg} alt="EviBite AI Logo" className="landing-logo-img" style={{ width: '32px', height: '32px', objectFit: 'contain' }} />
            <span className="brand-title">EviBite AI</span>
          </div>


          <div className="nav-actions desktop-only">
            {user && (
              <button 
                type="button"
                onClick={() => setIsSavedPlansOpen(true)} 
                className="user-nav-profile-btn"
                title="View your saved diet plans"
                style={{ gap: '6px', padding: '6px 14px' }}
              >
                <Bookmark size={15} color="#10b981" />
                <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>Saved Plans</span>
                {savedPlans.length > 0 && <span className="nav-count-badge" style={{ marginLeft: '2px' }}>{savedPlans.length}</span>}
              </button>
            )}

            <button className="btn-primary" onClick={() => navigate('/chat')}>
              Go to Chatbot <ArrowRight size={16} />
            </button>

            {user ? (
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
                        setIsSavedPlansOpen(true);
                      }}
                    >
                      <Bookmark size={16} />
                      <span>Saved Plans ({savedPlans.length})</span>
                    </button>
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
            ) : (
              <button className="btn-secondary" onClick={() => navigate('/login')}>
                Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="diet-main-container">
        {/* Saved Plans Modal */}
        {isSavedPlansOpen && (
          <div className="diet-modal-overlay" onClick={() => setIsSavedPlansOpen(false)}>
            <div className="diet-saved-plans-modal animate-scale-up" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div className="modal-header-left">
                  <div className="modal-header-icon">
                    <Bookmark size={20} className="text-emerald" />
                  </div>
                  <div>
                    <h3 className="modal-title">My Saved Diet Plans</h3>
                    <p className="modal-subtitle">
                      {savedPlans.length} {savedPlans.length === 1 ? 'plan' : 'plans'} saved for {user?.name || user?.email}
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => setIsSavedPlansOpen(false)} 
                  className="modal-close-btn"
                  aria-label="Close saved plans modal"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="modal-body-plans">
                {savedPlans.length === 0 ? (
                  <div className="saved-plans-empty">
                    <Bookmark size={36} className="text-slate-300" />
                    <h4>No Saved Diet Plans Yet</h4>
                    <p>Generate a diet plan using the wizard, and it will be saved to your profile automatically.</p>
                  </div>
                ) : (
                  <div className="saved-plans-grid">
                    {savedPlans.map((plan) => (
                      <div 
                        key={plan.id} 
                        className={`saved-plan-card ${dietPlan?.id === plan.id ? 'current-active' : ''}`}
                        onClick={() => handleSelectSavedPlan(plan)}
                      >
                        <div className="saved-plan-card-header">
                          <div className="plan-card-title-group">
                            <span className="plan-country-pill">
                              <Globe size={12} />
                              {plan.user_country || plan.profile?.country || 'Global'}
                            </span>
                            <h4 className="plan-card-title">{plan.title || `${plan.user_goal} Plan`}</h4>
                          </div>
                          <button
                            type="button"
                            className="plan-delete-btn"
                            title="Delete this saved plan"
                            onClick={(e) => handlePromptDeletePlan(plan, e)}
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>

                        <div className="saved-plan-metrics-row">
                          <div className="metric-chip">
                            <Flame size={12} className="text-orange" />
                            <span>{plan.daily_targets?.daily_calories || 2000} kcal</span>
                          </div>
                          <div className="metric-chip">
                            <Dumbbell size={12} className="text-blue" />
                            <span>{plan.daily_targets?.protein_target || 120}g protein</span>
                          </div>
                          <div className="metric-chip">
                            <Clock size={12} />
                            <span>{plan.meals?.length || 3} meals</span>
                          </div>
                        </div>

                        <div className="saved-plan-footer">
                          <span className="saved-plan-date">
                            <Calendar size={12} />
                            {new Date(plan.created_at || plan.timestamp || Date.now()).toLocaleDateString(undefined, {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                            })}
                          </span>
                          <span className="btn-load-plan-text">
                            Load Plan &rarr;
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Custom Delete Confirmation Modal */}
        {planToDelete && (
          <div className="diet-confirm-overlay" onClick={handleCancelDelete}>
            <div className="diet-confirm-modal animate-scale-up" onClick={(e) => e.stopPropagation()}>
              <div className="diet-confirm-icon-box">
                <Trash2 size={24} />
              </div>
              <h3 className="diet-confirm-title">Delete Saved Diet Plan?</h3>
              <p className="diet-confirm-desc">
                Are you sure you want to delete this saved plan? This action cannot be undone and will permanently remove it from your account.
              </p>

              <div className="diet-confirm-plan-preview">
                <div className="confirm-preview-badge">
                  <Globe size={11} />
                  <span>{planToDelete.user_country || planToDelete.profile?.country || 'Global'}</span>
                </div>
                <div className="confirm-preview-title">
                  {planToDelete.title || `${planToDelete.user_goal} Plan`}
                </div>
                <div className="confirm-preview-meta">
                  <span>{planToDelete.daily_targets?.daily_calories || 2000} kcal</span>
                  <span className="dot">•</span>
                  <span>{planToDelete.daily_targets?.protein_target || 120}g protein</span>
                  <span className="dot">•</span>
                  <span>{planToDelete.meals?.length || 3} meals</span>
                </div>
              </div>

              <div className="diet-confirm-actions">
                <button
                  type="button"
                  onClick={handleCancelDelete}
                  className="btn-confirm-cancel"
                  disabled={isDeletingPlan}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmDelete}
                  className="btn-confirm-delete"
                  disabled={isDeletingPlan}
                >
                  {isDeletingPlan ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <>
                      <Trash2 size={16} />
                      <span>Delete Plan</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
        {/* Loading Overlay */}
        {isLoading && (
          <div className="diet-loading-overlay">
            <div className="diet-loading-card">
              <div className="loading-spinner-ring">
                <Sparkles size={36} className="sparkle-pulse" />
              </div>
              <h2 className="loading-title">Diet & Nutrition Planning Agent</h2>
              <p className="loading-subtitle">
                Synthesizing personalized {formData.country} supermarket diet plan
              </p>
              
              <div className="loading-progress-stages">
                {loadingSteps.map((step, idx) => (
                  <div 
                    key={idx} 
                    className={`loading-stage-item ${loadingStep === idx ? 'active' : loadingStep > idx ? 'done' : 'pending'}`}
                  >
                    <div className="stage-icon">
                      {loadingStep > idx ? (
                        <CheckCircle2 size={16} className="text-emerald" />
                      ) : loadingStep === idx ? (
                        <Loader2 size={16} className="loading-spin-icon text-emerald" />
                      ) : (
                        <div className="stage-dot" />
                      )}
                    </div>
                    <span>{step}</span>
                  </div>
                ))}
              </div>

              <div className="loading-active-indicator">
                <div className="loading-bar-track">
                  <div 
                    className="loading-bar-fill" 
                    style={{ width: `${Math.min(96, Math.max(12, (loadingStep + 1) * 18 + elapsedSeconds * 3))}%` }} 
                  />
                </div>
                <p className="loading-status-tip">
                  {loadingStep === 4 
                    ? `Generating clinical rationale via Gemini AI... (${elapsedSeconds}s)` 
                    : `Grounding verified ${formData.country} supermarket items... (${elapsedSeconds}s)`}
                </p>
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
            {/* Official Print Header (Only visible on Printed Sheet) */}
            <div className="print-doc-header">
              <div className="print-brand-left">
                <img src={logoImg} alt="EviBite AI" className="print-logo" />
                <div>
                  <h2 className="print-brand-title">EviBite AI Diet & Nutrition Planning Agent</h2>
                  <span className="print-brand-subtitle">Clinical Dietary Strategy & Grounded Supermarket Blueprint</span>
                </div>
              </div>
              <div className="print-meta-right">
                <div className="print-meta-item">
                  <span className="print-meta-label">Market:</span>
                  <span className="print-meta-val">{dietPlan.user_country || formData.country}</span>
                </div>
                <div className="print-meta-item">
                  <span className="print-meta-label">Plan Status:</span>
                  <span className="print-meta-val">Verified Safe</span>
                </div>
                <div className="print-meta-item">
                  <span className="print-meta-label">Generated:</span>
                  <span className="print-meta-val">{new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</span>
                </div>
              </div>
            </div>

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
                    <Globe size={13} className="text-emerald" />
                    <strong>Market:</strong> {dietPlan.user_country || formData.country}
                  </span>
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
                {user && (
                  <button 
                    onClick={handleManualSave} 
                    className="action-btn-save" 
                    disabled={isSavingPlan}
                    title="Save this plan to your profile"
                  >
                    <BookmarkCheck size={16} />
                    <span>{saveSuccessMsg || (isSavingPlan ? 'Saving...' : 'Saved to Profile')}</span>
                  </button>
                )}
                <button onClick={handlePrintPlan} className="action-btn-outline" title="Print or save as clean PDF without URL footers">
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
            <ClinicalRationale 
              explanation={dietPlan.explanation} 
              targets={dietPlan.daily_targets} 
              profile={dietPlan.profile || formData} 
            />

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
                    <div className="print-checkbox-box" />
                    <div className="shopping-card-body">
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
                  </div>
                ))}
              </div>
            </div>

            {/* Official Print Footer (Only visible on Printed Sheet) */}
            <div className="print-doc-footer">
              <span>EviBite AI • Grounded Supermarket Nutrition Blueprint</span>
              <span>All products verified against Open Food Facts catalog</span>
              <span>Confidential Personal Nutrition Document</span>
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
                    onClick={() => goToStep(s.step)}
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

              <form onSubmit={handleSubmit} className="diet-wizard-form" noValidate>
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
                          <label className="form-label">Age (years) <span className="text-emerald">*</span></label>
                          <div className={`input-with-unit ${errors.age ? 'has-error' : ''}`}>
                            <input 
                              type="number" 
                              min="10" 
                              max="120" 
                              value={formData.age} 
                              onChange={(e) => handleInputChange('age', e.target.value)}
                              className={`form-input ${errors.age ? 'has-error' : ''}`}
                              placeholder="e.g. 25"
                            />
                            <span className="input-unit-badge">yrs</span>
                          </div>
                          {errors.age && (
                            <span className="form-field-error">
                              <AlertTriangle size={12} />
                              <span>{errors.age}</span>
                            </span>
                          )}
                        </div>

                        <div className="form-group">
                          <label className="form-label">Biological Gender <span className="text-emerald">*</span></label>
                          <div className={`segmented-control ${errors.gender ? 'has-error' : ''}`}>
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
                          {errors.gender && (
                            <span className="form-field-error">
                              <AlertTriangle size={12} />
                              <span>{errors.gender}</span>
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Row 2: Height & Weight */}
                      <div className="form-row-2">
                        <div className="form-group">
                          <label className="form-label">Height (cm) <span className="text-emerald">*</span></label>
                          <div className={`input-with-unit ${errors.height ? 'has-error' : ''}`}>
                            <input 
                              type="number" 
                              min="80" 
                              max="250" 
                              value={formData.height} 
                              onChange={(e) => handleInputChange('height', e.target.value)}
                              className={`form-input ${errors.height ? 'has-error' : ''}`}
                              placeholder="e.g. 175"
                            />
                            <span className="input-unit-badge">cm</span>
                          </div>
                          {errors.height && (
                            <span className="form-field-error">
                              <AlertTriangle size={12} />
                              <span>{errors.height}</span>
                            </span>
                          )}
                        </div>

                        <div className="form-group">
                          <label className="form-label">Weight (kg) <span className="text-emerald">*</span></label>
                          <div className={`input-with-unit ${errors.weight ? 'has-error' : ''}`}>
                            <input 
                              type="number" 
                              min="25" 
                              max="300" 
                              value={formData.weight} 
                              onChange={(e) => handleInputChange('weight', e.target.value)}
                              className={`form-input ${errors.weight ? 'has-error' : ''}`}
                              placeholder="e.g. 70"
                            />
                            <span className="input-unit-badge">kg</span>
                          </div>
                          {errors.weight && (
                            <span className="form-field-error">
                              <AlertTriangle size={12} />
                              <span>{errors.weight}</span>
                            </span>
                          )}
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
                            <span className="bmi-cat-subtext">{hasValidBmi ? 'WHO Clinical Classification' : 'Enter height & weight to calculate'}</span>
                          </div>
                        </div>

                        <div className="bmi-gauge-right">
                          <div className="bmi-scale-bar">
                            <div className="scale-segment under" title="Underweight (<18.5)">Under</div>
                            <div className="scale-segment normal" title="Normal (18.5-24.9)">Normal</div>
                            <div className="scale-segment over" title="Overweight (25-29.9)">Over</div>
                            <div className="scale-segment obese" title="Obese (≥30)">Obese</div>
                            {hasValidBmi && (
                              <div 
                                className="scale-pin" 
                                style={{ left: bmiInfo.pos }}
                                title={`Current BMI: ${liveBmi}`}
                              />
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Country / Regional Supermarket Selection */}
                      <div className="form-group country-select-group">
                        <label className="form-label" htmlFor="country-select">
                          <Globe size={16} className="text-emerald" />
                          <span>Which country are you located in?</span>
                          <span className="label-hint"> (Filters genuine products available in your regional supermarkets)</span>
                        </label>
                        <div className="country-select-box">
                          <select
                            id="country-select"
                            value={formData.country}
                            onChange={(e) => handleInputChange('country', e.target.value)}
                            className={`form-select country-dropdown ${errors.country ? 'has-error' : ''}`}
                          >
                            <option value="United States">🇺🇸 United States (US Supermarkets & Brands)</option>
                            <option value="United Kingdom">🇬🇧 United Kingdom (UK Supermarkets & Brands)</option>
                            <option value="Sri Lanka">🇱🇰 Sri Lanka (Sri Lankan Supermarkets & Local Staples)</option>
                            <option value="India">🇮🇳 India (Indian Supermarket Staples & Dhal/Curd)</option>
                            <option value="Canada">🇨🇦 Canada (Canadian Supermarkets)</option>
                            <option value="Australia">🇦🇺 Australia (Coles, Woolworths & Local)</option>
                            <option value="France">🇫🇷 France (Carrefour, Monoprix & European)</option>
                            <option value="Germany">🇩🇪 Germany (Rewe, Edeka & European)</option>
                            <option value="Global">🌎 Global / International (All Supermarket Products)</option>
                          </select>
                        </div>
                        {errors.country && (
                          <span className="form-field-error">
                            <AlertTriangle size={12} />
                            <span>{errors.country}</span>
                          </span>
                        )}
                        <p className="country-select-hint">
                          The AI Dietitian will prioritize products and portion sizes stocked in {formData.country} grocery stores.
                        </p>
                      </div>
                    </div>

                    <div className="step-nav-bar right-only">
                      <button 
                        type="button" 
                        onClick={() => goToStep(2)} 
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
                      <button type="button" onClick={() => goToStep(1)} className="btn-step-prev">
                        <ArrowLeft size={16} />
                        <span>Back</span>
                      </button>
                      <button type="button" onClick={() => goToStep(3)} className="btn-step-next">
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

                      {/* Custom Allergy Input (Visible when 'Other' is selected) */}
                      {formData.allergies.includes('other') && (
                        <div className="other-allergy-field-wrap animate-fade-in">
                          <label className="other-allergy-label" htmlFor="custom-allergy-input">
                            <ShieldAlert size={16} className="text-amber" />
                            <span>Specify Custom Allergies / Ingredients to Exclude</span>
                          </label>
                          <div className="other-allergy-input-box">
                            <input
                              id="custom-allergy-input"
                              type="text"
                              className="other-allergy-input"
                              placeholder="e.g. Sesame, Mustard, Shellfish, Strawberries, Corn"
                              value={otherAllergyText}
                              onChange={(e) => setOtherAllergyText(e.target.value)}
                              autoFocus
                            />
                            {otherAllergyText && (
                              <button
                                type="button"
                                className="clear-other-btn"
                                onClick={() => setOtherAllergyText('')}
                                title="Clear input"
                              >
                                &times;
                              </button>
                            )}
                          </div>
                          <p className="other-allergy-hint">
                            Separate multiple ingredients with commas. The AI Dietitian will strictly exclude any supermarket items containing these.
                          </p>
                        </div>
                      )}
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
                      <button type="button" onClick={() => goToStep(2)} className="btn-step-prev">
                        <ArrowLeft size={16} />
                        <span>Back</span>
                      </button>
                      <button type="button" onClick={() => goToStep(4)} className="btn-step-next">
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
                      <button type="button" onClick={() => goToStep(3)} className="btn-step-prev">
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
