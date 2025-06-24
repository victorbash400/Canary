// news-api.js - Fixed with proper timeouts
const API_BASE_URL = import.meta.env.PROD 
  ? (import.meta.env.VITE_API_URL || 'https://j1qbha86t1.execute-api.us-east-1.amazonaws.com/dev')
  : '/api'; // Use proxy in development

const getAuthHeaders = () => {
  const token = localStorage.getItem('authToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

// Helper function to create fetch with timeout
const fetchWithTimeout = async (url, options = {}, timeoutMs = 30000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.');
    }
    throw error;
  }
};

// Get personalized news feed (with longer timeout since it makes multiple API calls)
export const getNewsFeed = async () => {
  const response = await fetchWithTimeout(`${API_BASE_URL}/news/feed`, {
    headers: getAuthHeaders()
  }, 35000); // 35 second timeout for news feed

  if (!response.ok) {
    throw new Error('Failed to fetch news feed');
  }

  const data = await response.json();
  return data;
};

// Get user preferences
export const getUserPreferences = async () => {
  const response = await fetchWithTimeout(`${API_BASE_URL}/news/preferences`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user preferences');
  }

  const data = await response.json();
  return data;
};

// Update user preferences
export const updateUserPreferences = async (preferences) => {
  const response = await fetchWithTimeout(`${API_BASE_URL}/news/preferences`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(preferences),
  });

  if (!response.ok) {
    throw new Error('Failed to update user preferences');
  }

  const data = await response.json();
  return data;
};

// Add monitoring topic
export const addMonitoringTopic = async (topic) => {
  const response = await fetchWithTimeout(`${API_BASE_URL}/news/monitor`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ topic }),
  });

  if (!response.ok) {
    throw new Error('Failed to add monitoring topic');
  }

  const data = await response.json();
  return data;
};

// Remove monitoring topic
export const removeMonitoringTopic = async (topic) => {
  const response = await fetchWithTimeout(`${API_BASE_URL}/news/monitor/${encodeURIComponent(topic)}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Failed to remove monitoring topic');
  }

  const data = await response.json();
  return data;
};

// Get urgent news only (also needs longer timeout)
export const getUrgentNews = async () => {
  const response = await fetchWithTimeout(`${API_BASE_URL}/news/urgent`, {
    headers: getAuthHeaders()
  }, 35000); // 35 second timeout for urgent news

  if (!response.ok) {
    throw new Error('Failed to fetch urgent news');
  }

  const data = await response.json();
  return data;
};