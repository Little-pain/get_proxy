// src/api.ts
import api from './axios';

export const authApi = {
  register: (data: { email: string; password: string; password_confirm: string }) =>
  api.post('register/', data),

  login: (email: string, password: string) =>
    api.post('login/', { email, password }),

  getProfile: () => api.get('profile/'),

  refreshKey: () => api.post('refresh-key/'),

  logout: (refreshToken: string) =>
    api.post('logout/', { refresh: refreshToken }),

  changePassword: (data: { old_password: string; new_password: string }) =>
    api.put('change-password/', data),

  activateKey: (key: string) => api.post('activate-key/', { key }),
};

const allApi = {
  authApi,
};

export default allApi;