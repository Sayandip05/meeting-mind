import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  signup: (email: string, password: string, fullName: string) =>
    api.post('/auth/signup', { email, password, full_name: fullName }),
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  getMe: () => api.get('/auth/me'),
};

export const meetingsApi = {
  upload: (file: File, name: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    return api.post('/meetings/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  getAll: () => api.get('/meetings/'),
  getById: (id: number) => api.get(`/meetings/${id}`),
  process: (id: number) => api.post(`/meetings/${id}/process`),
  delete: (id: number) => api.delete(`/meetings/${id}`),
};

export const chatApi = {
  ask: (meetingId: number, question: string) =>
    api.post('/chat/ask', { meeting_id: meetingId, question }),
  getHistory: (meetingId: number) => api.get(`/chat/history/${meetingId}`),
  clearHistory: (meetingId: number) => api.delete(`/chat/history/${meetingId}`),
};

export const highlightsApi = {
  generate: (meetingId: number) => api.post(`/highlights/generate/${meetingId}`),
  get: (meetingId: number) => api.get(`/highlights/${meetingId}`),
  download: (meetingId: number, format: 'pdf' | 'txt' | 'docx' = 'pdf') =>
    `${API_URL}/api/v1/highlights/download/${meetingId}?format=${format}`,
};

export const adminApi = {
  getDashboard: () => api.get('/admin/dashboard'),
  getUsers: () => api.get('/admin/users'),
  getMeetings: () => api.get('/admin/meetings'),
  deactivateUser: (userId: number) => api.post(`/admin/users/${userId}/deactivate`),
};

export default api;
