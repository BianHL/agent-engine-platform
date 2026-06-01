import axios from 'axios';

// Mock axios before importing the module
jest.mock('axios', () => {
  const mockAxiosInstance = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };
  return {
    __esModule: true,
    default: {
      create: jest.fn(() => mockAxiosInstance),
    },
  };
});

// Import after mock setup
import { api } from '../api';

const mockedAxios = axios as jest.Mocked<typeof axios>;
const mockClient = (mockedAxios.create as jest.Mock).mock.results[0]?.value;

describe('ApiClient', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('login', () => {
    it('sends POST to /auth/login with credentials', async () => {
      const mockData = { access_token: 'test-token' };
      mockClient.post.mockResolvedValue({ data: mockData });

      const result = await api.login('admin', 'password');

      expect(mockClient.post).toHaveBeenCalledWith('/auth/login', {
        username: 'admin',
        password: 'password',
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('getMe', () => {
    it('sends GET to /auth/me', async () => {
      const mockUser = { id: '1', username: 'admin', role: 'admin' };
      mockClient.get.mockResolvedValue({ data: mockUser });

      const result = await api.getMe();

      expect(mockClient.get).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(mockUser);
    });
  });

  describe('listAgents', () => {
    it('sends GET to /agents with pagination params', async () => {
      const mockAgents = { items: [], total: 0 };
      mockClient.get.mockResolvedValue({ data: mockAgents });

      const result = await api.listAgents(1, 20);

      expect(mockClient.get).toHaveBeenCalledWith('/agents', {
        params: { page: 1, size: 20 },
      });
      expect(result).toEqual(mockAgents);
    });
  });

  describe('listBuiltinTools', () => {
    it('sends GET to /tools/builtin', async () => {
      const mockTools = [{ name: 'web_search', description: 'Search the web' }];
      mockClient.get.mockResolvedValue({ data: mockTools });

      const result = await api.listBuiltinTools();

      expect(mockClient.get).toHaveBeenCalledWith('/tools/builtin');
      expect(result).toEqual(mockTools);
    });
  });

  describe('listAuditLogs', () => {
    it('sends GET to /audit with filters and pagination', async () => {
      const mockLogs = { items: [], total: 0 };
      mockClient.get.mockResolvedValue({ data: mockLogs });

      const result = await api.listAuditLogs({ action: 'create' }, 1, 50);

      expect(mockClient.get).toHaveBeenCalledWith('/audit', {
        params: { action: 'create', page: 1, size: 50 },
      });
      expect(result).toEqual(mockLogs);
    });
  });

  describe('createTool', () => {
    it('sends POST to /tools with tool data', async () => {
      const toolData = { name: 'my_tool', description: 'A test tool' };
      const mockResponse = { id: '1', ...toolData };
      mockClient.post.mockResolvedValue({ data: mockResponse });

      const result = await api.createTool(toolData);

      expect(mockClient.post).toHaveBeenCalledWith('/tools', toolData);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('deleteTool', () => {
    it('sends DELETE to /tools/:id', async () => {
      mockClient.delete.mockResolvedValue({ data: { success: true } });

      const result = await api.deleteTool('tool-123');

      expect(mockClient.delete).toHaveBeenCalledWith('/tools/tool-123');
      expect(result).toEqual({ success: true });
    });
  });

  describe('executeTool', () => {
    it('sends POST to /tools/:name/execute with params', async () => {
      const mockResult = { output: 'result' };
      mockClient.post.mockResolvedValue({ data: mockResult });

      const result = await api.executeTool('web_search', { query: 'test' }, 30);

      expect(mockClient.post).toHaveBeenCalledWith('/tools/web_search/execute', {
        params: { query: 'test' },
        timeout: 30,
      });
      expect(result).toEqual(mockResult);
    });
  });

  describe('generic methods', () => {
    it('get method calls client.get', async () => {
      mockClient.get.mockResolvedValue({ data: { foo: 'bar' } });

      const result = await api.get('/test');

      expect(mockClient.get).toHaveBeenCalledWith('/test', undefined);
      expect(result).toEqual({ foo: 'bar' });
    });

    it('post method calls client.post', async () => {
      mockClient.post.mockResolvedValue({ data: { id: '1' } });

      const result = await api.post('/test', { name: 'test' });

      expect(mockClient.post).toHaveBeenCalledWith('/test', { name: 'test' }, undefined);
      expect(result).toEqual({ id: '1' });
    });
  });
});
