// auth-service.js - Authentication API calls
const API_BASE_URL = import.meta.env.PROD 
  ? 'https://j1qbha86t1.execute-api.us-east-1.amazonaws.com/dev'  // Hardcoded for production
  : '/api';

console.log('AUTH API_BASE_URL:', API_BASE_URL); // Debug log

// Register new user
export const registerUser = async (email, password, username) => {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      password,
      username
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Registration failed');
  }

  const data = await response.json();
  
  // Store token in localStorage
  if (data.token) {
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
  }
  
  return data;
};

// Login user
export const loginUser = async (email, password) => {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      password
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Login failed');
  }

  const data = await response.json();
  
  // Store token in localStorage
  if (data.token) {
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
  }
  
  return data;
};

// Get user profile
export const getUserProfile = async () => {
  const token = localStorage.getItem('authToken');
  
  if (!token) {
    throw new Error('No authentication token');
  }

  const response = await fetch(`${API_BASE_URL}/auth/profile`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Token expired, clear storage
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      throw new Error('Session expired');
    }
    throw new Error('Failed to fetch profile');
  }

  const data = await response.json();
  return data;
};

// Logout user
export const logoutUser = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('user');
};

// Get stored token
export const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

// Get stored user
export const getStoredUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

// Check if user is authenticated
export const isAuthenticated = () => {
  const token = localStorage.getItem('authToken');
  if (!token) return false;
  
  try {
    // Basic JWT validation - check if token is expired
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    
    if (payload.exp < currentTime) {
      // Token expired, clear storage
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      return false;
    }
    
    return true;
  } catch (error) {
    // Invalid token format
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    return false;
  }
};