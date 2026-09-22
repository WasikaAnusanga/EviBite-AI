import React, { useState, useRef, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import AuthModal from './components/AuthModal';
import { sendChatMessage, getCurrentUser } from './services/api';
import { Sparkles, ShieldCheck, HeartPulse, Scale, Search, LogIn, LogOut, User as UserIcon } from 'lucide-react';

export default function App() {
  const [sessions, setSessions] = useState([
    { id: 'session-1', title: 'Product Safety Check', messages: [] }
  ]);
  const [currentSessionId, setCurrentSessionId] = useState('session-1');
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const messagesEndRef = useRef(null);

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
        });
    }
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem('evibite_auth_token');
    localStorage.removeItem('evibite_user');
    setUser(null);
  };

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

  const handleSelectSession = (id) => {
    setCurrentSessionId(id);
  };

  const handleSendMessage = async (userText) => {
    const userMsg = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: userText,
      timestamp: new Date().toISOString(),
    };

    // Update state immediately with user message
    setSessions(prev => prev.map(s => {
      if (s.id === currentSessionId) {
        const firstMsg = s.messages.length === 0;
        return {
          ...s,
          title: firstMsg ? (userText.length > 28 ? userText.substring(0, 28) + '...' : userText) : s.title,
          messages: [...s.messages, userMsg],
        };
      }
      return s;
    }));

    setIsLoading(true);

    try {
      const response = await sendChatMessage(userText, currentSessionId);
      
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
      icon: <ShieldCheck size={18} color="#f43f5e" />,
    },
    {
      title: 'Sugar & Nutrition Query',
      sub: 'Check sugar and calorie content of Coca-Cola',
      prompt: 'How much sugar is in Coca-Cola and what are its nutrition facts?',
      icon: <HeartPulse size={18} color="#f59e0b" />,
    },
    {
      title: 'Product Comparison',
      sub: 'Compare ingredients between Coke Zero and Pepsi Max',
      prompt: 'Compare Coca-Cola Zero vs Pepsi Max regarding artificial sweeteners.',
      icon: <Scale size={18} color="#06b6d4" />,
    },
    {
      title: 'Dietary Suitability',
      sub: 'Verify if Oreos are 100% vegan certified',
      prompt: 'Are Oreo biscuits suitable for a strict vegan diet?',
      icon: <Search size={18} color="#10b981" />,
    },
  ];

  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
      />

      <main className="chat-stage">
        <header className="chat-header">
          <div className="chat-title">
            <h1>{activeSession?.title || 'Chat'}</h1>
            <span className="tag-badge">Multi-Agent Intelligence</span>
          </div>

          <div className="user-profile-menu">
            {user ? (
              <div className="user-badge-pill">
                <div className="user-avatar-sm">
                  {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="user-name-text">{user.name}</span>
                <button className="signout-btn" onClick={handleSignOut} title="Sign Out">
                  <LogOut size={16} />
                </button>
              </div>
            ) : (
              <button className="auth-trigger-btn" onClick={() => setIsAuthModalOpen(true)}>
                <LogIn size={16} />
                <span>Sign In / Register</span>
              </button>
            )}
          </div>
        </header>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">
                <Sparkles size={28} />
              </div>
              <h2 className="empty-title">What would you like to verify today?</h2>
              <p className="empty-subtitle">
                Ask about packaged supermarket foods, allergen safety, ingredients, or nutritional comparisons.
              </p>

              <div className="starter-chips">
                {starterPrompts.map((item, idx) => (
                  <button
                    key={idx}
                    className="chip-btn"
                    onClick={() => handleSendMessage(item.prompt)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {item.icon}
                      <span className="chip-title">{item.title}</span>
                    </div>
                    <span className="chip-sub">{item.sub}</span>
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
            <div className="message-row">
              <div className="avatar ai-avatar">
                <Sparkles size={18} />
              </div>
              <div className="message-content">
                <div className="message-header">
                  <span>EviBite AI</span>
                </div>
                <div className="typing-indicator">
                  <div className="dot" />
                  <div className="dot" />
                  <div className="dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </main>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={(userData) => setUser(userData)}
      />
    </div>
  );
}
