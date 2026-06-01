import { create } from 'zustand';
import api from '@/lib/api';
import { User } from '@/types';

/** Set a cookie visible to middleware (server-side) */
function setAuthCookie(token: string) {
  document.cookie = `token=${token}; Path=/; SameSite=Strict; Secure`;
}

/** Remove the auth cookie */
function removeAuthCookie() {
  document.cookie = 'token=; Path=/; SameSite=Strict; Secure; Max-Age=0';
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

// Initialize token from localStorage, restoring cookie for middleware
const initialToken = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
if (typeof window !== 'undefined' && initialToken) {
  // Ensure cookie is set on page load (may have been cleared by browser restart)
  const hasCookie = document.cookie.split(';').some(c => c.trim().startsWith('token='));
  if (!hasCookie) {
    document.cookie = `token=${initialToken}; Path=/; SameSite=Strict; Secure`;
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: initialToken,
  loading: false,

  login: async (username: string, password: string) => {
    set({ loading: true });
    try {
      const data = await api.login(username, password);
      localStorage.setItem('token', data.access_token);
      setAuthCookie(data.access_token);
      set({ token: data.access_token, loading: false });
      // Fetch user info
      const user = await api.getMe();
      set({ user });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    removeAuthCookie();
    set({ user: null, token: null });
    window.location.href = '/login';
  },

  checkAuth: async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const user = await api.getMe();
      set({ user, token });
    } catch {
      localStorage.removeItem('token');
      removeAuthCookie();
      set({ user: null, token: null });
    }
  },
}));
