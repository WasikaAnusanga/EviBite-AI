import React from 'react';
import {
  Leaf,
  Sparkles,
  ShieldCheck,
  Zap,
  Layers,
  ArrowRight,
  Barcode,
  CheckCircle2,
  DollarSign,
  Activity,
  ChevronRight,
  Globe,
  Lock,
} from 'lucide-react';

export default function LandingPage({ onNavigate }) {
  return (
    <div className="min-h-screen bg-[#f4f6f5] text-slate-800 flex flex-col font-sans selection:bg-emerald-600 selection:text-white">
      {/* NAVBAR */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-200/80 px-6 py-4 flex items-center justify-between shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-[#1d5c31] shadow-sm">
            <Leaf className="w-6 h-6 fill-current" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 leading-none">EviBite AI</h1>
            <p className="text-[11px] text-slate-500 font-medium mt-0.5">Food Information & Safety Assistant</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('signin')}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 transition"
          >
            Sign In
          </button>
          <button
            onClick={() => onNavigate('signup')}
            className="px-5 py-2.5 rounded-xl bg-[#1d5c31] hover:bg-[#154724] text-white text-xs font-bold transition shadow-sm flex items-center gap-2"
          >
            <span>Try Out Our App</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="max-w-6xl w-full mx-auto px-6 pt-16 pb-20 text-center flex flex-col items-center space-y-6">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-100/80 border border-emerald-300/80 text-[#1d5c31] text-xs font-semibold">
          <Sparkles className="w-4 h-4" />
          <span>Multi-Agent Supermarket Product Intelligence</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl leading-[1.15]">
          Evidence-Grounded Food Safety & Allergen Intelligence
        </h1>

        <p className="text-base md:text-lg text-slate-600 max-w-2xl leading-relaxed">
          Ask natural-language questions about packaged food ingredients, verify allergen safety with zero LLM hallucinations, and scan Open Food Facts barcodes instantly.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <button
            onClick={() => onNavigate('signup')}
            className="px-8 py-4 rounded-2xl bg-[#1d5c31] hover:bg-[#154724] text-white font-bold text-base shadow-lg shadow-emerald-900/10 transition flex items-center gap-3 group"
          >
            <span>Try Out Our App</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
          </button>

          <button
            onClick={() => onNavigate('app')}
            className="px-8 py-4 rounded-2xl bg-white border border-slate-300 hover:border-slate-400 text-slate-800 font-bold text-base shadow-2xs transition flex items-center gap-2"
          >
            <Sparkles className="w-5 h-5 text-emerald-700" />
            <span>Instant Guest Demo</span>
          </button>
        </div>

        {/* STATS & REASSURANCE */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-12 max-w-4xl w-full border-t border-slate-200/80 mt-12 text-slate-700">
          <div>
            <p className="text-2xl font-extrabold text-[#1d5c31]">4 Autonomous</p>
            <p className="text-xs text-slate-500 font-medium">Cooperating AI Agents</p>
          </div>
          <div>
            <p className="text-2xl font-extrabold text-[#1d5c31]">Zero</p>
            <p className="text-xs text-slate-500 font-medium">Hallucination Rules</p>
          </div>
          <div>
            <p className="text-2xl font-extrabold text-[#1d5c31]">3M+ Products</p>
            <p className="text-xs text-slate-500 font-medium">Open Food Facts API</p>
          </div>
          <div>
            <p className="text-2xl font-extrabold text-[#1d5c31]">100% Verified</p>
            <p className="text-xs text-slate-500 font-medium">Deterministic Safety</p>
          </div>
        </div>
      </section>

      {/* FEATURE GRID */}
      <section className="bg-white border-y border-slate-200/80 py-20 px-6">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Designed for Food Safety & Retail Intelligence
            </h2>
            <p className="text-sm text-slate-500">
              Combining Large Language Models with deterministic safety engines for complete peace of mind.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* FEATURE 1 */}
            <div className="p-8 rounded-3xl bg-[#f8faf9] border border-slate-200/80 space-y-4 hover:border-emerald-300 transition">
              <div className="w-12 h-12 rounded-2xl bg-emerald-100 flex items-center justify-center text-[#1d5c31]">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Zero-Hallucination Safety</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Medical and allergy decisions use deterministic Python rule engines to evaluate ingredient lists, trace declarations, and dietary compliance.
              </p>
            </div>

            {/* FEATURE 2 */}
            <div className="p-8 rounded-3xl bg-[#f8faf9] border border-slate-200/80 space-y-4 hover:border-emerald-300 transition">
              <div className="w-12 h-12 rounded-2xl bg-emerald-100 flex items-center justify-center text-[#1d5c31]">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">4-Agent Architecture</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Cooperating agents for Triage, Retrieval, Safety Analysis, and Response Generation communicate seamlessly over Pydantic JSON contracts.
              </p>
            </div>

            {/* FEATURE 3 */}
            <div className="p-8 rounded-3xl bg-[#f8faf9] border border-slate-200/80 space-y-4 hover:border-emerald-300 transition">
              <div className="w-12 h-12 rounded-2xl bg-emerald-100 flex items-center justify-center text-[#1d5c31]">
                <Barcode className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Barcode GTIN Scanner</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Instant barcode lookup retrieves Nutri-Score, Eco-Score, ingredients, and allergen badges directly from Open Food Facts data.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* MULTI-AGENT WORKFLOW PIPELINE */}
      <section className="max-w-6xl w-full mx-auto px-6 py-20 space-y-12">
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Multi-Agent Execution Pipeline
          </h2>
          <p className="text-sm text-slate-500">
            Every user query flows dynamically through specialized autonomous agents.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { step: 'Agent 1', title: 'Triage & Routing', desc: 'Parses intent, food entities, dietary rules, and risk level via Gemini LLM.' },
            { step: 'Agent 2', title: 'Product Retrieval', desc: 'Fetches product data from Open Food Facts API and scores data completeness.' },
            { step: 'Agent 3', title: 'Safety Analysis', desc: 'Evaluates allergen conflicts and dietary suitability deterministically.' },
            { step: 'Agent 4', title: 'Response Ranker', desc: 'Synthesizes natural-language answers strictly grounded in evidence.' },
          ].map((item, idx) => (
            <div key={idx} className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-2xs space-y-2">
              <span className="text-[11px] font-bold text-[#1d5c31] px-2.5 py-1 rounded-full bg-emerald-100/80">
                {item.step}
              </span>
              <h4 className="text-base font-bold text-slate-900 pt-1">{item.title}</h4>
              <p className="text-xs text-slate-500 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA BANNER */}
      <section className="bg-[#1d5c31] text-white py-16 px-6 text-center">
        <div className="max-w-4xl mx-auto space-y-6">
          <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight">
            Ready to Experience Intelligent Food Safety?
          </h2>
          <p className="text-emerald-100 text-sm max-w-xl mx-auto">
            Join shoppers and grocery retailers using EviBite AI for instant, evidence-grounded food product intelligence.
          </p>
          <button
            onClick={() => onNavigate('signup')}
            className="px-8 py-4 rounded-2xl bg-white text-[#1d5c31] hover:bg-emerald-50 font-bold text-base shadow-lg transition inline-flex items-center gap-2"
          >
            <span>Try Out Our App</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-white border-t border-slate-200 px-6 py-8 text-center text-xs text-slate-500 space-y-2">
        <p className="font-semibold text-slate-700">EviBite AI — IT3041 Information Retrieval & Web Analytics</p>
        <p>EviBite AI provides food information for general guidance only, not medical advice.</p>
      </footer>
    </div>
  );
}
