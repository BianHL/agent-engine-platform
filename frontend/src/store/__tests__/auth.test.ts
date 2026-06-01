import { act } from '@testing-library/react';

// Mock the API module
jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    login: jest.fn(),
    getMe: jest.fn(),
  },
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: jest.fn((key: string) => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; }),
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

import api from '@/lib/api';
import { useAuthStore } from '../auth';

const mockedApi = api as jest.Mocked<typeof api>;

describe('AuthStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
    // Reset the store state
    useAuthStore.setState({ user: null, token: null, loading: false });
  });

  describe('login', () => {
    it('sets token and fetches user on successful login', async () => {
      const mockToken = { access_token: 'test-token-123' };
      const mockUser = { id: '1', username: 'admin', role: 'admin', tenant_id: 't1' };

      mockedApi.login.mockResolvedValue(mockToken);
      mockedApi.getMe.mockResolvedValue(mockUser);

      await act(async () => {
        await useAuthStore.getState().login('admin', 'password');
      });

      expect(mockedApi.login).toHaveBeenCalledWith('admin', 'password');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'test-token-123');
      expect(mockedApi.getMe).toHaveBeenCalled();

      const state = useAuthStore.getState();
      expect(state.token).toBe('test-token-123');
      expect(state.user).toEqual(mockUser);
      expect(state.loading).toBe(false);
    });

    it('sets loading to false and throws on login failure', async () => {
      const error = new Error('Invalid credentials');
      mockedApi.login.mockRejectedValue(error);

      await act(async () => {
        try {
          await useAuthStore.getState().login('admin', 'wrong');
        } catch (e) {
          // Expected to throw
        }
      });

      const state = useAuthStore.getState();
      expect(state.loading).toBe(false);
      expect(state.token).toBeNull();
    });
  });

  describe('logout', () => {
    it('clears token and user state', () => {
      // Set initial state
      useAuthStore.setState({ token: 'some-token', user: { id: '1', username: 'admin', role: 'admin', tenant_id: 't1' } });

      act(() => {
        useAuthStore.getState().logout();
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
      const state = useAuthStore.getState();
      expect(state.token).toBeNull();
      expect(state.user).toBeNull();
    });
  });

  describe('checkAuth', () => {
    it('fetches user and sets state when token exists', async () => {
      localStorageMock.getItem.mockReturnValue('valid-token');
      const mockUser = { id: '1', username: 'admin', role: 'admin', tenant_id: 't1' };
      mockedApi.getMe.mockResolvedValue(mockUser);

      await act(async () => {
        await useAuthStore.getState().checkAuth();
      });

      expect(mockedApi.getMe).toHaveBeenCalled();
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.token).toBe('valid-token');
    });

    it('clears state when getMe fails', async () => {
      localStorageMock.getItem.mockReturnValue('expired-token');
      mockedApi.getMe.mockRejectedValue(new Error('Unauthorized'));

      await act(async () => {
        await useAuthStore.getState().checkAuth();
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
    });

    it('does nothing when no token exists', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      await act(async () => {
        await useAuthStore.getState().checkAuth();
      });

      expect(mockedApi.getMe).not.toHaveBeenCalled();
    });
  });
});
