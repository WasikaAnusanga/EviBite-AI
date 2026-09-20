import React, { useState } from 'react';
import {
  Leaf,
  ArrowRight,
  CheckCircle2,
  Mail,
  Lock,
  User,
  ShieldCheck,
  Check,
  ArrowLeft,
  Sparkles,
} from 'lucide-react';

const ALLERGY_CHIPS = [
  { id: 'peanut', label: 'Peanuts' },
  { id: 'milk', label: 'Dairy / Milk' },
  { id: 'gluten', label: 'Gluten / Wheat' },
  { id: 'soy', label: 'Soy' },
  { id: 'nuts', label: 'Tree Nuts' },
  { id: 'vegan', label: 'Vegan Preference' },
];

export function SignUpPage({ onNavigate, onAuthSuccess }) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [selectedAllergies, setSelectedAllergies] = useState(['peanut', 'milk']);
  const [agreeTerms, setAgreeTerms] = useState(true);

  const toggleAllergy = (id) => {
    setSelectedAllergies((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email || !fullName) return;
    onAuthSuccess({
      name: fullName,
      email: email,
      allergies: selectedAllergies,
    });
  };

  return (
    <div className="min-h-screen bg-[#f4f6f5] flex items-center justify-center p-6 text-slate-800 font-sans">
      <div className="max-w-md w-full space-y-6">
        {/* BACK TO HOME */}
        <button
          onClick={() => onNavigate('landing')}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </button>

        {/* AUTH CARD */}
        <div className="bg-white border border-slate-200/90 rounded-3xl p-8 shadow-sm space-y-6">
          {/* HEADER */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-[#1d5c31]">
              <Leaf className="w-6 h-6 fill-current" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 leading-none">Create Your Account</h1>
              <p className="text-xs text-slate-500 font-medium mt-1">Join EviBite AI Food Assistant</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* FULL NAME */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-700">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Demo User"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-600 focus:bg-white transition"
                />
              </div>
            </div>

            {/* EMAIL */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-700">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="demo@evibite.ai"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-600 focus:bg-white transition"
                />
              </div>
            </div>

            {/* PASSWORD */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-700">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-600 focus:bg-white transition"
                />
              </div>
            </div>

            {/* ALLERGY PROFILE SELECTION */}
            <div className="space-y-2 pt-1">
              <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                <span>Select Your Food Allergies & Diets</span>
                <span className="text-[10px] text-slate-400 font-normal">Optional</span>
              </label>

              <div className="flex flex-wrap gap-2">
                {ALLERGY_CHIPS.map((chip) => {
                  const isSelected = selectedAllergies.includes(chip.id);
                  return (
                    <button
                      type="button"
                      key={chip.id}
                      onClick={() => toggleAllergy(chip.id)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition flex items-center gap-1.5 ${
                        isSelected
                          ? 'bg-emerald-100/90 border-emerald-300 text-[#1d5c31] font-bold'
                          : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                      <span>{chip.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* TERMS CHECKBOX */}
            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="terms"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                className="rounded border-slate-300 text-[#1d5c31] focus:ring-emerald-500"
              />
              <label htmlFor="terms" className="text-xs text-slate-600">
                I agree to the <span className="font-semibold text-slate-900">Terms of Service</span> & Privacy Policy
              </label>
            </div>

            {/* SUBMIT BUTTON */}
            <button
              type="submit"
              className="w-full py-3 rounded-xl bg-[#1d5c31] hover:bg-[#154724] text-white font-bold text-sm shadow-md transition flex items-center justify-center gap-2 mt-2"
            >
              <span>Complete Registration</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* FOOTER SWITCH */}
          <div className="text-center pt-2 border-t border-slate-100 text-xs text-slate-500">
            Already have an account?{' '}
            <button
              onClick={() => onNavigate('signin')}
              className="font-bold text-[#1d5c31] hover:underline"
            >
              Sign In
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SignInPage({ onNavigate, onAuthSuccess }) {
  const [email, setEmail] = useState('demo@evibite.ai');
  const [password, setPassword] = useState('password123');

  const handleSubmit = (e) => {
    e.preventDefault();
    onAuthSuccess({
      name: 'Demo User',
      email: email || 'demo@evibite.ai',
      allergies: ['peanut', 'milk'],
    });
  };

  return (
    <div className="min-h-screen bg-[#f4f6f5] flex items-center justify-center p-6 text-slate-800 font-sans">
      <div className="max-w-md w-full space-y-6">
        {/* BACK TO HOME */}
        <button
          onClick={() => onNavigate('landing')}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </button>

        {/* AUTH CARD */}
        <div className="bg-white border border-slate-200/90 rounded-3xl p-8 shadow-sm space-y-6">
          {/* HEADER */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-[#1d5c31]">
              <Leaf className="w-6 h-6 fill-current" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 leading-none">Welcome Back</h1>
              <p className="text-xs text-slate-500 font-medium mt-1">Sign in to EviBite AI</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* EMAIL */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-700">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="demo@evibite.ai"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-emerald-600 focus:bg-white transition"
                />
              </div>
            </div>

            {/* PASSWORD */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700">Password</label>
                <a href="#" className="text-[11px] text-[#1d5c31] font-semibold hover:underline">
                  Forgot?
                </a>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-emerald-600 focus:bg-white transition"
                />
              </div>
            </div>

            {/* SUBMIT BUTTON */}
            <button
              type="submit"
              className="w-full py-3 rounded-xl bg-[#1d5c31] hover:bg-[#154724] text-white font-bold text-sm shadow-md transition flex items-center justify-center gap-2 mt-2"
            >
              <span>Sign In</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* DEMO QUICK LOGIN BUTTON */}
          <button
            onClick={() =>
              onAuthSuccess({
                name: 'Demo User',
                email: 'demo@evibite.ai',
                allergies: ['peanut', 'milk'],
              })
            }
            className="w-full py-2.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-[#1d5c31] font-bold text-xs border border-emerald-200 transition flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4 text-[#1d5c31]" />
            <span>Instant Demo Sign In</span>
          </button>

          {/* FOOTER SWITCH */}
          <div className="text-center pt-2 border-t border-slate-100 text-xs text-slate-500">
            Don't have an account?{' '}
            <button
              onClick={() => onNavigate('signup')}
              className="font-bold text-[#1d5c31] hover:underline"
            >
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
