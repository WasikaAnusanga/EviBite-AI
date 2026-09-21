const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Send user query to EviBite AI multi-agent orchestrator
 * @param {string} message 
 * @param {string|null} sessionId 
 * @returns {Promise<Object>}
 */
export async function sendChatMessage(message, sessionId = null) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
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
