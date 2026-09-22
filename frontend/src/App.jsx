import React, { useState, useRef, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import SettingsModal from './components/SettingsModal';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { sendChatMessage, getCurrentUser, fetchUserSessions, fetchSessionHistory, deleteChatSession } from './services/api';
import logoImg from './logo/logo.png';
import { Sparkles, ShieldCheck, HeartPulse, Scale, Search, LogIn, UserPlus, LogOut, ArrowRight } from 'lucide-react';

function ChatDashboard({ user, onSignOut }) {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const userId = user ? (user.id || user.email) : null;

  // Load user chat sessions from MongoDB when user updates / logs in
  useEffect(() => {
    async function loadSessions() {
      if (userId) {
        const userDbSessions = await fetchUserSessions(userId);
        if (userDbSessions && userDbSessions.length > 0) {
          const formatted = userDbSessions.map(s => ({
            id: s.id,
            title: s.title || 'New Chat',
            messages: (s.messages || []).map((m, idx) => ({
              id: `msg-${idx}-${Date.now()}`,
              sender: m.role === 'assistant' ? 'ai' : m.role,
              text: m.content,
              products: m.products || [],
              timestamp: m.timestamp || new Date().toISOString(),
            })),
          }));
          setSessions(formatted);
          setCurrentSessionId(formatted[0].id);
          return;
        }
      }
      // Guest user or empty database: start fresh session
      const newId = `session-${Date.now()}`;
      setSessions([{ id: newId, title: 'New Chat', messages: [] }]);
      setCurrentSessionId(newId);
    }
    loadSessions();
  }, [userId]);

  const activeSession = sessions.find(s => s.id === currentSessionId) || sessions[0];
  const messages = activeSession ? activeSession.messages : [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleNewChat = () => {
    const newId = `session-${Date.now()}`;
    const newSession = {
      id: newId,
      title: 'New Chat',
      messages: [],
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newId);
  };

  const handleSelectSession = async (id) => {
    setCurrentSessionId(id);
    const sess = sessions.find(s => s.id === id);
    if (sess && sess.messages.length === 0 && userId) {
      try {
        const fullDoc = await fetchSessionHistory(id, userId);
        if (fullDoc && fullDoc.messages) {
          const formattedMsgs = fullDoc.messages.map((m, idx) => ({
            id: `msg-${idx}`,
            sender: m.role === 'assistant' ? 'ai' : m.role,
            text: m.content,
            products: m.products || [],
            timestamp: m.timestamp || new Date().toISOString(),
          }));
          setSessions(prev => prev.map(s => s.id === id ? { ...s, messages: formattedMsgs } : s));
        }
      } catch (err) {
        console.error('Error loading session detail:', err);
      }
    }
  };

  const handleDeleteSession = async (id) => {
    try {
      if (userId) {
        await deleteChatSession(id, userId);
      }
    } catch (e) {
      console.error('Failed deleting chat session:', e);
    }
    setSessions(prev => {
      const filtered = prev.filter(s => s.id !== id);
      if (filtered.length === 0) {
        const newId = `session-${Date.now()}`;
        setCurrentSessionId(newId);
        return [{ id: newId, title: 'New Chat', messages: [] }];
      }
      if (currentSessionId === id) {
        setCurrentSessionId(filtered[0].id);
      }
      return filtered;
    });
  };

  const handleSendMessage = async (userText) => {
    const userMsg = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: userText,
      timestamp: new Date().toISOString(),
    };

    setSessions(prev => prev.map(s => {
      if (s.id === currentSessionId) {
        const isFirstMsg = s.messages.length === 0;
        return {
          ...s,
          title: isFirstMsg ? (userText.length > 28 ? userText.substring(0, 28) + '...' : userText) : s.title,
          messages: [...s.messages, userMsg],
        };
      }
      return s;
    }));

    setIsLoading(true);

    try {
      const response = await sendChatMessage(userText, currentSessionId, userId);
      
      const aiMsg = {
        id: `msg-ai-${Date.now()}`,
        sender: 'ai',
        text: response.final_response,
        trace_id: response.trace_id,
        execution_steps: response.execution_steps,
        triage_output: response.triage_output,
        timestamp: response.timestamp || new Date().toISOString(),
      };

      setSessions(prev => prev.map(s => {
        if (s.id === currentSessionId) {
          return {
            ...s,
            messages: [...s.messages, aiMsg],
          };
        }
        return s;
      }));
    } catch (error) {
      const errorMsg = {
        id: `msg-err-${Date.now()}`,
        sender: 'ai',
        text: `⚠️ Could not reach EviBite AI backend: ${error.message}. Please make sure the backend API is running on http://localhost:8000.`,
        timestamp: new Date().toISOString(),
      };

      setSessions(prev => prev.map(s => {
        if (s.id === currentSessionId) {
          return {
            ...s,
            messages: [...s.messages, errorMsg],
          };
        }
        return s;
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const starterPrompts = [
    {
      title: 'Peanut Allergy Check',
      sub: 'Does Nutella contain peanuts or nut traces?',
      prompt: 'I have a peanut allergy. Can I safely eat Nutella?',
      icon: <ShieldCheck size={20} color="#46803A" />,
    },
    {
      title: 'Sugar & Nutrition Query',
      sub: 'Check sugar and calorie content of Coca-Cola',
      prompt: 'How much sugar is in Coca-Cola and what are its nutrition facts?',
      icon: <HeartPulse size={20} color="#46803A" />,
    },
    {
      title: 'Product Comparison',
      sub: 'Compare ingredients between Coke Zero and Pepsi Max',
      prompt: 'Compare Coca-Cola Zero vs Pepsi Max regarding artificial sweeteners.',
      icon: <Scale size={20} color="#46803A" />,
    },
    {
      title: 'Dietary Suitability',
      sub: 'Verify if Oreos are 100% vegan certified',
      prompt: 'Are Oreo biscuits suitable for a strict vegan diet?',
      icon: <Search size={20} color="#46803A" />,
    },
  ];

  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        user={user}
        onSignOut={onSignOut}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <main className="chat-stage">
        <header className="chat-header">
          <div className="chat-title">
            <img src={logoImg} alt="EviBite AI" className="header-logo-img" />
            <h1>{activeSession?.title || 'Chat'}</h1>
            <span className="tag-badge">Multi-Agent Intelligence</span>
          </div>

          {!user && (
            <div className="header-auth-group">
              <Link to="/login" className="auth-trigger-btn signin">
                <LogIn size={16} />
                <span>Sign In</span>
              </Link>
              <Link to="/register" className="auth-trigger-btn register">
                <UserPlus size={16} />
                <span>Register</span>
              </Link>
            </div>
          )}
        </header>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state-redesigned">
              <div className="welcome-hero-badge">
                <Sparkles size={14} color="#46803A" />
                <span>Supermarket Product Intelligence</span>
              </div>

              <div className="empty-logo-wrapper">
                <img src={logoImg} alt="EviBite AI Logo" className="empty-logo-img" />
              </div>

              <h2 className="empty-title">What would you like to verify today?</h2>
              <p className="empty-subtitle">
                Ask about packaged supermarket foods, allergen safety, ingredients, or nutritional comparisons.
              </p>

              <div className="starter-grid-redesigned">
                {starterPrompts.map((item, idx) => (
                  <button
                    key={idx}
                    className="starter-card-btn"
                    onClick={() => handleSendMessage(item.prompt)}
                  >
                    <div className="starter-card-top">
                      <div className="starter-icon-badge">
                        {item.icon}
                      </div>
                      <ArrowRight size={16} className="starter-card-arrow" />
                    </div>
                    <div className="starter-card-body">
                      <span className="starter-card-title">{item.title}</span>
                      <span className="starter-card-sub">{item.sub}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} />
            ))
          )}

          {isLoading && (
            <div className="message-row thinking-row">
              <div className="avatar ai-avatar">
                <img src={logoImg} alt="AI Avatar" className="avatar-logo-img" />
              </div>
              <div className="message-content">
                <div className="message-header">
                  <span>EviBite AI</span>
                </div>
                <div className="thinking-bubble">
                  <div className="thinking-header">
                    <Sparkles size={16} className="thinking-sparkle-spin" />
                    <span>Analyzing supermarket product evidence...</span>
                  </div>
                  <div className="typing-dots">
                    <span className="dot dot-1" />
                    <span className="dot dot-2" />
                    <span className="dot dot-3" />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        user={user}
      />
    </div>
  );
}

function ProtectedRoute({ children, user, isAuthChecking }) {
  if (isAuthChecking) {
    return (
      <div style={{ display: 'flex', height: '100vh', width: '100vw', alignItems: 'center', justifyContent: 'center', backgroundColor: '#F7F9F5', color: '#1B241D' }}>
        <div style={{ textAlign: 'center' }}>
          <img src={logoImg} alt="EviBite AI" style={{ width: '48px', height: '48px', marginBottom: '12px', objectFit: 'contain' }} />
          <p style={{ fontWeight: 600, fontSize: '0.95rem' }}>Loading EviBite AI...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('evibite_auth_token');
    const savedUser = localStorage.getItem('evibite_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        // ignore parse error
      }
    }
    if (token) {
      getCurrentUser(token)
        .then((userData) => {
          setUser(userData);
          localStorage.setItem('evibite_user', JSON.stringify(userData));
        })
        .catch(() => {
          localStorage.removeItem('evibite_auth_token');
          localStorage.removeItem('evibite_user');
          setUser(null);
        })
        .finally(() => {
          setIsAuthChecking(false);
        });
    } else {
      setIsAuthChecking(false);
    }
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem('evibite_auth_token');
    localStorage.removeItem('evibite_user');
    setUser(null);
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute user={user} isAuthChecking={isAuthChecking}>
              <ChatDashboard user={user} onSignOut={handleSignOut} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/login"
          element={<LoginPage onLoginSuccess={(userData) => setUser(userData)} />}
        />
        <Route
          path="/register"
          element={<RegisterPage onRegisterSuccess={(userData) => setUser(userData)} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
