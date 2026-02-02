import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Don't retry if it's a login, refresh, verify, or logout request
    const isAuthEndpoint = originalRequest.url?.includes('/auth/login') || 
                          originalRequest.url?.includes('/auth/refresh') || 
                          originalRequest.url?.includes('/auth/verify') ||
                          originalRequest.url?.includes('/auth/logout');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      try {
        await authService.refreshToken();
        return api(originalRequest);
      } catch (refreshError) {
        // Don't redirect, just reject - let the component handle it
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authService = {
  login: async (username, password, tornApiKey) => {
    const response = await api.post('/auth/login', {
      username,
      password,
      torn_api_key: tornApiKey,
    });
    if (response.data?.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    if (response.data?.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return response.data;
  },

  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    if (response.data?.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    return response.data;
  },

  verify: async () => {
    const response = await api.get('/auth/verify');
    return response.data;
  },

  listUsers: async () => {
    const response = await api.get('/auth/users');
    return response.data;
  },

  createUser: async (userData) => {
    const response = await api.post('/auth/create-user', userData);
    return response.data;
  },

  changePassword: async (currentPassword, newPassword) => {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

// War Session API
export const warService = {
  createSession: async (warName) => {
    const response = await api.post('/war/create', { war_name: warName });
    return response.data;
  },

  getActive: async () => {
    const response = await api.get('/war/active');
    return response.data;
  },

  listWars: async () => {
    const response = await api.get('/war/list');
    return response.data;
  },

  getWarDetails: async (sessionId) => {
    const response = await api.get(`/war/${sessionId}`);
    return response.data;
  },

  completeSession: async (sessionId) => {
    const response = await api.post(`/war/${sessionId}/complete`);
    return response.data;
  },

  calculatePayouts: async (sessionId, totalEarnings, pricePerHit) => {
    const response = await api.post(`/war/${sessionId}/calculate`, {
      total_earnings: totalEarnings,
      price_per_hit: pricePerHit,
    });
    return response.data;
  },

  getPayouts: async (sessionId) => {
    const response = await api.get(`/war/${sessionId}/payouts`);
    return response.data;
  },

  getHistory: async () => {
    const response = await api.get('/war/history');
    return response.data;
  },

  getMemberPayouts: async (sessionId) => {
    const response = await api.get(`/war/${sessionId}/member-payouts`);
    return response.data;
  },
};

// Member API
export const memberService = {
  refreshMembers: async (warSessionId) => {
    const response = await api.post('/members/refresh', { war_session_id: warSessionId });
    return response.data;
  },

  getSessionMembers: async (sessionId) => {
    const response = await api.get(`/members/session/${sessionId}`);
    return response.data;
  },

  addBonus: async (memberId, bonusAmount, bonusReason) => {
    const response = await api.post(`/members/${memberId}/bonus`, {
      bonus_amount: bonusAmount,
      bonus_reason: bonusReason,
    });
    return response.data;
  },

  updateBonus: async (memberId, bonusAmount, bonusReason) => {
    const response = await api.put(`/members/${memberId}/bonus`, {
      bonus_amount: bonusAmount,
      bonus_reason: bonusReason,
    });
    return response.data;
  },

  deleteBonus: async (memberId) => {
    const response = await api.delete(`/members/${memberId}/bonus`);
    return response.data;
  },
};

// Payment API
export const paymentService = {
  createPayment: async (sessionId, amount, description) => {
    const response = await api.post(`/payments/${sessionId}`, {
      amount,
      description,
    });
    return response.data;
  },

  getPayments: async (sessionId) => {
    const response = await api.get(`/payments/${sessionId}`);
    return response.data;
  },

  updatePayment: async (paymentId, amount, description) => {
    const response = await api.put(`/payments/${paymentId}`, {
      amount,
      description,
    });
    return response.data;
  },

  deletePayment: async (paymentId) => {
    const response = await api.delete(`/payments/${paymentId}`);
    return response.data;
  },
};

// Export API
export const exportService = {
  exportPDF: async (sessionId, userName) => {
    const response = await api.get(`/export/${sessionId}/pdf`, {
      params: { user_name: userName },
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `war_report_${sessionId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return response.data;
  },
};

// Archive API
export const archiveService = {
  getArchivedLogs: async (startDate, endDate, actionType, limit = 100) => {
    const response = await api.get('/archive/', {
      params: {
        start_date: startDate,
        end_date: endDate,
        action_type: actionType,
        limit,
      },
    });
    return response.data;
  },
};

export default api;
