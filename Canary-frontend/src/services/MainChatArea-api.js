const API_BASE_URL = import.meta.env.PROD 
  ? (import.meta.env.VITE_API_URL || 'https://j1qbha86t1.execute-api.us-east-1.amazonaws.com/dev')
  : '/api';

const getAuthHeaders = () => {
  const token = localStorage.getItem('authToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

// Get AI memory about the user
export const getAIMemory = async () => {
  const response = await fetch(`${API_BASE_URL}/ai/memory`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Failed to fetch AI memory');
  }

  const data = await response.json();
  return data;
};

// Create a new chat
export const createNewChat = async (title = 'New Chat') => {
  const response = await fetch(`${API_BASE_URL}/chats`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error('Failed to create new chat');
  }

  const data = await response.json();
  return data;
};

// Get all chats
export const getAllChats = async () => {
  const response = await fetch(`${API_BASE_URL}/chats`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Failed to fetch chats');
  }

  const data = await response.json();
  return data;
};

// Get a specific chat by ID
export const getChatById = async (chatId) => {
  const response = await fetch(`${API_BASE_URL}/chats/${chatId}`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Failed to fetch chat');
  }

  const data = await response.json();
  return data;
};

// Save a text message to a chat and receive AI response
export const saveMessage = async (chatId, content) => {
  const response = await fetch(`${API_BASE_URL}/chats/${chatId}/messages`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    throw new Error('Failed to save message or get AI response');
  }

  const data = await response.json();
  return data;
};