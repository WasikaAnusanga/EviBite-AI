import React, { useState, useEffect, useRef } from 'react';
import {
  Leaf,
  MessageSquare,
  History,
  UtensilsCrossed,
  Activity,
  ShieldAlert,
  Sparkles,
  Sliders,
  Settings,
  Trash2,
  Send,
  Paperclip,
  CheckCircle2,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Barcode,
  DollarSign,
  ChevronDown,
  AlertCircle,
  Layers,
  Search,
  Check,
  Zap,
  User,
} from 'lucide-react';


import LandingPage from './LandingPage';
import { SignUpPage, SignInPage } from './AuthPages';

const API_BASE_URL = '';

const SUGGESTED_QUESTIONS = [
  'What are the allergens in Nutella?',
  'Show me dairy-free chocolate options',
  'What is the calorie & sugar count?',
];

const PRESET_BARCODES = [
  { name: 'Nutella Hazelnut Spread', barcode: '3017620422003', brand: 'Ferrero' },
  { name: 'Coca-Cola Original', barcode: '5449000000996', brand: 'Coca-Cola' },
  { name: 'Oreo Original Biscuits', barcode: '7622210449283', brand: 'Mondelez' },
];

export default function App() {
  const [currentView, setCurrentView] = useState('landing');
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('evibite_token') || null);
  const [currentUser, setCurrentUser] = useState(() => {
    const savedUser = localStorage.getItem('evibite_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: "Hello! I'm EviBite AI, your multi-agent supermarket product intelligence assistant. How can I help you today?",
      evidenceText: 'Ask me any question about food ingredients, allergen safety, dietary preferences, or scan a product barcode!',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [previousProduct, setPreviousProduct] = useState(null);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [userSessions, setUserSessions] = useState([]);

  const [showPricingModal, setShowPricingModal] = useState(false);
  const [showBarcodeModal, setShowBarcodeModal] = useState(false);
  const [pricingData, setPricingData] = useState(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [serverStatus, setServerStatus] = useState('checking');
  const chatEndRef = useRef(null);

  // Auto-redirect unauthenticated users trying to access 'app'
  useEffect(() => {
    if (currentView === 'app' && !authToken) {
      setCurrentView('signup');
    }
  }, [currentView, authToken]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    fetch('/health')
      .then((res) => (res.ok ? setServerStatus('online') : setServerStatus('offline')))
      .catch(() => setServerStatus('offline'));

    fetch('/api/commercialization/tiers')
      .then((res) => res.json())
      .then((data) => setPricingData(data))
      .catch(() => {});
  }, []);

  // Fetch user sessions when logged in
  useEffect(() => {
    if (authToken && (currentView === 'app' || activeTab === 'history')) {
      fetchUserSessions();
    }
  }, [authToken, currentView, activeTab]);

  const fetchUserSessions = async () => {
    if (!authToken) return;
    try {
      const res = await fetch('/api/history', {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUserSessions(data.sessions || []);
      }
    } catch (err) {
      console.error('Failed to fetch user history', err);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    if (!authToken || !sessionId) return;
    setIsLoading(true);
    try {
      const res = await fetch(`/api/history/${sessionId}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setActiveSessionId(sessionId);
        const formatted = data.messages.map((m, idx) => ({
          id: m.id || idx,
          sender: m.sender === 'user' ? 'user' : 'ai',
          text: m.message,
          triage_output: m.triage_output,
          trace: m.triage_output ? { triage_output: m.triage_output, execution_path: ['triage', 'retrieval', 'safety', 'response'] } : null,
          timestamp: m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
        }));
        setMessages(formatted);
      }
    } catch (err) {
      console.error('Failed to load session messages', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthSuccess = ({ token, user }) => {
    setAuthToken(token);
    setCurrentUser(user);
    localStorage.setItem('evibite_token', token);
    localStorage.setItem('evibite_user', JSON.stringify(user));
    setCurrentView('app');
  };

  const handleSignOut = () => {
    setAuthToken(null);
    setCurrentUser(null);
    localStorage.removeItem('evibite_token');
    localStorage.removeItem('evibite_user');
    setCurrentView('landing');
  };

  const handleSendMessage = async (queryText = inputQuery) => {
    const textToSend = queryText.trim();
    if (!textToSend || isLoading) return;

    if (!authToken) {
      setCurrentView('signup');
      return;
    }

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    const safePrevProduct = previousProduct && (previousProduct.name || previousProduct.barcode)
      ? {
          name: previousProduct.name || null,
          brand: previousProduct.brand || null,
          barcode: previousProduct.barcode || null,
        }
      : null;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          message: textToSend,
          session_id: activeSessionId,
          previous_product: safePrevProduct,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        if (data.session_id) {
          setActiveSessionId(data.session_id);
        }
        if (data.triage_output?.products && data.triage_output.products.length > 0) {
          const firstProduct = data.triage_output.products[0];
          if (firstProduct.name || firstProduct.barcode) {
            setPreviousProduct(firstProduct);
          }
        }

        const aiMsg = {
          id: Date.now() + 1,
          sender: 'ai',
          text: data.final_response,
          trace: data,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, aiMsg]);
        fetchUserSessions();
      } else {
        if (response.status === 401) {
          handleSignOut();
          return;
        }
        const errorMsg = {
          id: Date.now() + 1,
          sender: 'ai',
          text: `Error: ${data.detail || 'Unable to process query at this time.'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    } catch (err) {
      const offlineMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: 'Network Error: Could not connect to EviBite AI backend server.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, offlineMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setActiveSessionId(null);
    setPreviousProduct(null);
    setMessages([
      {
        id: Date.now(),
        sender: 'ai',
        text: "Started new conversation. How can I help you with food safety or ingredients today?",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };


  if (currentView === 'landing') {
    return <LandingPage onNavigate={(view) => setCurrentView(view)} />;
  }

  if (currentView === 'signup') {
    return (
      <SignUpPage
        onNavigate={(view) => setCurrentView(view)}
        onAuthSuccess={handleAuthSuccess}
      />
    );
  }

  if (currentView === 'signin') {
    return (
      <SignInPage
        onNavigate={(view) => setCurrentView(view)}
        onAuthSuccess={handleAuthSuccess}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f6f5] flex font-sans text-slate-800">

      {/* LEFT SIDEBAR NAVIGATION */}
      <aside className="w-64 bg-white border-r border-slate-200/80 p-5 flex flex-col justify-between shrink-0 shadow-sm">
        <div className="space-y-6 overflow-y-auto">
          {/* LOGO */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-[#1d5c31]">
              <Leaf className="w-6 h-6 fill-current" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 leading-tight">EviBite AI</h1>
              <p className="text-[11px] text-slate-500 font-medium">Food Information & Safety Assistant</p>
            </div>
          </div>

          {/* NEW CHAT BUTTON */}
          <button
            onClick={clearChat}
            className="w-full flex items-center gap-2.5 px-4 py-3 rounded-xl bg-emerald-50/80 hover:bg-emerald-100/80 text-[#1d5c31] font-semibold text-sm transition text-left"
          >
            <MessageSquare className="w-4 h-4 text-[#1d5c31]" />
            <span>New Chat</span>
          </button>

          {/* NAV LINKS */}
          <nav className="space-y-1">
            {[
              { id: 'chat', label: 'Chat Assistant', icon: MessageSquare },
              { id: 'history', label: 'History', icon: History },
              { id: 'explorer', label: 'Product Explorer', icon: UtensilsCrossed },
              { id: 'nutrition', label: 'Nutrition Analyzer', icon: Activity },
              { id: 'allergen', label: 'Allergen Checker', icon: ShieldAlert },
              { id: 'recommendations', label: 'Recommendations', icon: Sparkles },
            ].map((item) => {
              const IconComponent = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                    activeTab === item.id
                      ? 'bg-slate-100 text-slate-900 font-semibold'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <IconComponent className="w-4 h-4 text-slate-500" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* USER RECENT SESSIONS DRAWER */}
          {userSessions.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block px-1">
                Recent Conversations
              </span>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {userSessions.map((session) => (
                  <button
                    key={session.session_id}
                    onClick={() => loadSessionMessages(session.session_id)}
                    className={`w-full text-left px-3 py-2 rounded-xl text-xs truncate transition flex items-center gap-2 ${
                      activeSessionId === session.session_id
                        ? 'bg-emerald-50 text-[#1d5c31] font-bold border border-emerald-200'
                        : 'text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                    <span className="truncate">{session.title}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* BOTTOM SIDEBAR CARDS */}
        <div className="space-y-4 pt-4 border-t border-slate-100">
          {/* SYSTEM STATUS CARD */}
          <div className="bg-[#f0fdf4] border border-emerald-200/80 rounded-2xl p-3.5 space-y-2.5">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-emerald-950">System Status</span>
            </div>
            <p className="text-[11px] text-emerald-800 font-medium">All 4 multi-agents operational</p>

            <div className="grid grid-cols-4 gap-1 text-center pt-1 border-t border-emerald-200/60">
              {[
                { name: 'Router', key: '1' },
                { name: 'Retrieval', key: '2' },
                { name: 'Safety', key: '3' },
                { name: 'Response', key: '4' },
              ].map((agent) => (
                <div key={agent.key} className="flex flex-col items-center">
                  <div className="w-6 h-6 rounded-full bg-emerald-200/70 flex items-center justify-center text-emerald-900 text-[10px] font-bold">
                    <Check className="w-3 h-3 stroke-[3]" />
                  </div>
                  <span className="text-[9px] text-emerald-900 font-medium mt-1">{agent.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* USER PROFILE */}
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-[#1d5c31] text-white font-bold flex items-center justify-center text-xs">
                {currentUser?.full_name || currentUser?.name ? (currentUser.full_name || currentUser.name).substring(0, 2).toUpperCase() : 'EU'}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-slate-900 truncate">
                  {currentUser?.full_name || currentUser?.name || 'Logged User'}
                </p>
                <p className="text-[11px] text-slate-500 truncate">
                  {currentUser?.email || 'user@example.com'}
                </p>
              </div>
            </div>
            <button
              onClick={handleSignOut}
              className="text-xs font-bold text-slate-500 hover:text-rose-600 transition px-1.5 py-1"
              title="Sign Out to Landing Page"
            >
              Exit
            </button>
          </div>
        </div>
      </aside>



      {/* RIGHT MAIN CONTENT PANEL */}
      <main className="flex-1 flex flex-col bg-white m-3 rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
        {/* TOP HEADER */}
        <header className="px-8 py-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">EviBite AI Assistant</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Ask me anything about food products, ingredients, nutrition and allergen safety!
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowBarcodeModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
            >
              <Barcode className="w-4 h-4 text-emerald-700" />
              <span>Scan Barcode</span>
            </button>

            <button
              onClick={() => setShowPricingModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-emerald-300 bg-emerald-50 hover:bg-emerald-100 text-[#1d5c31] text-xs font-semibold transition"
            >
              <DollarSign className="w-4 h-4 text-[#1d5c31]" />
              <span>Commercialization Tiers</span>
            </button>

            <button
              onClick={clearChat}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
            >
              <Trash2 className="w-4 h-4 text-slate-500" />
              <span>Clear Chat</span>
            </button>
          </div>
        </header>

        {/* CHAT MESSAGES FEED */}
        <div className="flex-1 p-8 overflow-y-auto space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className="space-y-4">
              {msg.sender === 'user' ? (
                /* USER MESSAGE BUBBLE */
                <div className="flex items-start justify-end gap-3">
                  <div className="bg-[#1d5c31] text-white px-5 py-3 rounded-2xl rounded-tr-none text-sm font-medium shadow-sm max-w-lg">
                    <p>{msg.text}</p>
                    <span className="block text-[10px] text-emerald-200/80 text-right mt-1">
                      {msg.timestamp}
                    </span>
                  </div>
                  <div className="w-9 h-9 rounded-full bg-[#1d5c31] text-white flex items-center justify-center shrink-0">
                    <User className="w-5 h-5" />
                  </div>
                </div>
              ) : (
                /* ASSISTANT MESSAGE CARD (FRESHBITE STYLE) */
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-[#1d5c31] text-white flex items-center justify-center shrink-0 shadow-md">
                    <Leaf className="w-5 h-5 fill-current" />
                  </div>

                  <div className="flex-1 bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm space-y-4 max-w-3xl">
                    {/* PRIMARY SUMMARY STATEMENT */}
                    <h3 className="text-base font-bold text-slate-900 leading-snug">{msg.text}</h3>

                    {/* EVIDENCE SUMMARY TEXT */}
                    {msg.evidenceText && (
                      <p className="text-xs text-slate-600 leading-relaxed">{msg.evidenceText}</p>
                    )}

                    {/* KEY INGREDIENTS RELEVANT */}
                    {msg.ingredients && msg.ingredients.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-bold text-slate-900 block">
                          Key Ingredients (relevant)
                        </span>
                        <div className="flex flex-wrap gap-2 items-center">
                          {msg.ingredients.map((ing, idx) => (
                            <span
                              key={idx}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${
                                ing.allergen
                                  ? 'bg-slate-100 border-slate-300 text-slate-900 font-semibold'
                                  : 'bg-slate-100/70 border-slate-200 text-slate-700'
                              }`}
                            >
                              {ing.name}
                            </span>
                          ))}
                          <span className="text-xs font-bold text-[#1d5c31] cursor-pointer hover:underline ml-1">
                            View all ingredients →
                          </span>
                        </div>
                      </div>
                    )}

                    {/* ALLERGEN / DIETARY NOTE BOX */}
                    <div className="bg-[#f0fdf4] border border-emerald-300/80 rounded-xl p-4 flex gap-3 items-start">
                      <div className="w-7 h-7 rounded-full bg-emerald-700 text-white flex items-center justify-center shrink-0 mt-0.5">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                      <div className="space-y-1 text-xs">
                        <h4 className="font-bold text-emerald-950 text-xs">Allergen / Dietary Note</h4>
                        {msg.allergenNote ? (
                          <>
                            <p className="text-slate-800">
                              <span className="font-semibold text-slate-900">Contains:</span>{' '}
                              {msg.allergenNote.contains}
                            </p>
                            <p className="text-slate-600">
                              <span className="font-semibold text-slate-700">May contain traces of:</span>{' '}
                              {msg.allergenNote.mayContain}
                            </p>
                            <p className="text-slate-500 text-[11px] pt-1">{msg.allergenNote.disclaimer}</p>
                          </>
                        ) : (
                          <p className="text-slate-700">
                            Verified food safety parameters evaluated across Open Food Facts ingredient lists.
                          </p>
                        )}
                      </div>
                    </div>

                    {/* MULTI-AGENT TRACE STEP BADGES */}
                    {msg.trace && (
                      <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                        <div className="flex items-center gap-1.5">
                          <span className="font-semibold text-slate-600">Agent Path:</span>
                          {msg.trace.execution_path?.map((step, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 text-[11px] font-mono"
                            >
                              {step}
                            </span>
                          ))}
                        </div>

                        {msg.trace.triage_output?.risk_level && (
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                              msg.trace.triage_output.risk_level === 'HIGH'
                                ? 'bg-rose-100 text-rose-800 border border-rose-300'
                                : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            }`}
                          >
                            Risk: {msg.trace.triage_output.risk_level}
                          </span>
                        )}
                      </div>
                    )}

                    {/* FEEDBACK ROW */}
                    <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                      <div className="flex items-center gap-2">
                        <span>Was this helpful?</span>
                        <button className="p-1 hover:text-slate-700 transition">
                          <ThumbsUp className="w-3.5 h-3.5" />
                        </button>
                        <button className="p-1 hover:text-slate-700 transition">
                          <ThumbsDown className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <span>{msg.timestamp}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-3 text-slate-500 text-xs italic pl-14">
              <RefreshCw className="w-4 h-4 animate-spin text-[#1d5c31]" />
              <span>Analyzing product ingredients & allergy safety across 4 agents...</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* SUGGESTED FOLLOW-UP QUESTIONS ROW */}
        <div className="px-8 py-3 bg-slate-50/60 border-t border-slate-100 flex items-center justify-between gap-3">
          <div className="flex-1 flex gap-2 overflow-x-auto no-scrollbar">
            {SUGGESTED_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(q)}
                className="px-4 py-2 rounded-xl bg-white border border-slate-200/90 hover:border-emerald-500 text-slate-700 text-xs font-medium transition shadow-2xs whitespace-nowrap"
              >
                {q}
              </button>
            ))}
          </div>

          <button
            onClick={() => handleSendMessage('Suggest alternative healthy options')}
            className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-emerald-800 transition"
            title="Refresh suggestions"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* INPUT BAR AT BOTTOM */}
        <div className="p-6 pt-2 bg-white border-t border-slate-100 space-y-2">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center bg-white border border-slate-300 rounded-2xl px-4 py-2 shadow-sm focus-within:border-emerald-600 focus-within:ring-2 focus-within:ring-emerald-500/20 transition"
          >
            <Paperclip className="w-5 h-5 text-slate-400 cursor-pointer hover:text-slate-600 mr-3" />
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask a question about our food..."
              className="flex-1 bg-transparent text-slate-900 text-sm placeholder-slate-400 focus:outline-none"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !inputQuery.trim()}
              className="w-10 h-10 bg-[#1d5c31] hover:bg-[#154724] disabled:opacity-40 text-white rounded-full flex items-center justify-center transition shadow-sm ml-2"
            >
              <Send className="w-4 h-4 fill-current ml-0.5" />
            </button>
          </form>

          <p className="text-[11px] text-center text-slate-400">
            EviBite AI provides information for general guidance only, not medical advice.
          </p>
        </div>
      </main>

      {/* BARCODE MODAL */}
      {showBarcodeModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Barcode className="w-5 h-5 text-[#1d5c31]" />
                <h3 className="text-base font-bold text-slate-900">Barcode Scanner Simulator</h3>
              </div>
              <button onClick={() => setShowBarcodeModal(false)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>

            <div className="space-y-2">
              {PRESET_BARCODES.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setShowBarcodeModal(false);
                    handleSendMessage(item.barcode);
                  }}
                  className="w-full text-left p-3 rounded-xl bg-slate-50 hover:bg-emerald-50/80 border border-slate-200 hover:border-emerald-300 transition flex items-center justify-between"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{item.name}</p>
                    <p className="text-xs text-slate-500">Brand: {item.brand}</p>
                  </div>
                  <span className="text-xs font-mono text-[#1d5c31] font-bold px-2.5 py-1 rounded bg-emerald-100/80">
                    {item.barcode}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* COMMERCIALIZATION MODAL */}
      {showPricingModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white border border-slate-200 rounded-3xl max-w-4xl w-full p-8 shadow-2xl space-y-6 my-8">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Commercialization & Pricing Model</h2>
                <p className="text-xs text-slate-500">Dual B2C SaaS Subscription & B2B Retail Enterprise API</p>
              </div>
              <button onClick={() => setShowPricingModal(false)} className="text-slate-400 hover:text-slate-600 text-lg">
                ✕
              </button>
            </div>

            {/* B2C SECTION */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-[#1d5c31] uppercase tracking-wider">1. B2C Shopper Subscriptions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {pricingData?.b2c_subscriptions?.map((tier, i) => (
                  <div key={i} className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex justify-between items-center">
                      <h4 className="text-base font-bold text-slate-900">{tier.name}</h4>
                      <span className="text-sm font-bold text-[#1d5c31]">{tier.price}</span>
                    </div>
                    <p className="text-xs text-slate-500">{tier.target_audience}</p>
                    <ul className="space-y-1.5 text-xs text-slate-700">
                      {tier.features.map((f, fi) => (
                        <li key={fi} className="flex items-center gap-2">
                          <Check className="w-3.5 h-3.5 text-[#1d5c31]" />
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            {/* B2B SECTION */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-emerald-800 uppercase tracking-wider">2. B2B Enterprise API Tiers</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {pricingData?.b2b_enterprise_api?.map((tier, i) => (
                  <div key={i} className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex justify-between items-center">
                      <h4 className="text-base font-bold text-slate-900">{tier.name}</h4>
                      <span className="text-sm font-bold text-emerald-800">{tier.price}</span>
                    </div>
                    <p className="text-xs text-slate-500">{tier.target_audience}</p>
                    <ul className="space-y-1.5 text-xs text-slate-700">
                      {tier.features.map((f, fi) => (
                        <li key={fi} className="flex items-center gap-2">
                          <Check className="w-3.5 h-3.5 text-emerald-800" />
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
