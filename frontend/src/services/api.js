const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Send user query to EviBite AI multi-agent orchestrator
 * @param {string} message 
 * @param {string|null} sessionId 
 * @returns {Promise<Object>}
 */
export async function sendChatMessage(message, sessionId = null, userId = null) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        user_id: userId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error (${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}

/**
 * Fetch all chat sessions for a specific user from MongoDB
 * @param {string} userId 
 */
export async function fetchUserSessions(userId) {
  if (!userId) return [];
  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions?user_id=${encodeURIComponent(userId)}`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.sessions || [];
  } catch (err) {
    console.error('Error fetching user sessions:', err);
    return [];
  }
}

/**
 * Fetch messages for a single session
 * @param {string} sessionId 
 * @param {string|null} userId 
 */
export async function fetchSessionHistory(sessionId, userId = null) {
  try {
    const url = `${API_BASE_URL}/chat/sessions/${sessionId}?user_id=${encodeURIComponent(userId || '')}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Could not load session history');
    return await response.json();
  } catch (err) {
    console.error('Error fetching session history:', err);
    throw err;
  }
}

/**
 * Delete a session from MongoDB
 * @param {string} sessionId 
 * @param {string|null} userId 
 */
export async function deleteChatSession(sessionId, userId = null) {
  try {
    const url = `${API_BASE_URL}/chat/sessions/${sessionId}?user_id=${encodeURIComponent(userId || '')}`;
    const response = await fetch(url, { method: 'DELETE' });
    if (!response.ok) throw new Error('Could not delete chat session');
    return await response.json();
  } catch (err) {
    console.error('Error deleting session:', err);
    throw err;
  }
}

/**
 * Register a new user
 * @param {string} name
 * @param {string} email
 * @param {string} password
 */
export async function registerUser(name, email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Registration failed.');
  }
  return await response.json();
}

/**
 * Sign in an existing user
 * @param {string} email
 * @param {string} password
 */
export async function loginUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Login failed.');
  }
  return await response.json();
}

/**
 * Get current user profile with token
 * @param {string} token
 */
export async function getCurrentUser(token) {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Session expired');
  }
  return await response.json();
}
