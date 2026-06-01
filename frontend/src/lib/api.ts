import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  Agent,
  KnowledgeBase,
  Document,
  Chunk,
  RetrievalResult,
  Conversation,
  ChatMessage,
  ModelProvider,
  ModelConfig,
  PaginatedResponse,
  AuditLog,
  User,
} from '@/types';

// ---------------------------------------------------------------------------
// Inline types for responses without a dedicated interface in @/types
// ---------------------------------------------------------------------------

interface TokenResponse {
  access_token: string;
  token_type: string;
}

interface ChatCompletionResponse {
  content: string;
  model: string;
  usage: { input_tokens: number; output_tokens: number; total_tokens: number };
  conversation_id?: string;
}

interface StatusResponse {
  status: string;
}

interface ToolInfo {
  name: string;
  description: string;
  tool_type: string;
  source: 'registry' | 'database';
  id?: string;
  enabled?: boolean;
}

interface ToolExecutionResult {
  [key: string]: unknown;
}

interface FeedbackResponse {
  id: string;
  message_id: string;
  rating: string;
  comment?: string;
}

interface FeedbackStats {
  total_feedbacks: number;
  positive: number;
  negative: number;
  positive_rate: number;
}

interface Annotation {
  id: string;
  message_id: string;
  question?: string;
  corrected_answer: string;
  hit_count?: number;
  created_at?: string;
}

interface AnnotationResponse {
  id: string;
  message_id: string;
  corrected_answer: string;
}

interface CreateAgentData {
  name: string;
  description?: string;
  model_provider?: string;
  model_name?: string;
  system_prompt?: string;
  tools?: Record<string, unknown>[];
  knowledge_base_ids?: string[];
}

interface CreateKnowledgeBaseData {
  name: string;
  description?: string;
  embedding_model?: string;
  dimensions?: number;
  chunk_size?: number;
  chunk_overlap?: number;
}

interface CreateProviderData {
  name: string;
  provider_type: string;
  api_key?: string;
  api_base?: string;
  config?: Record<string, unknown>;
}

interface CreateModelConfigData {
  provider_id: string;
  model_name: string;
  model_type?: string;
  display_name?: string;
  config?: Record<string, unknown>;
  is_default?: boolean;
}

interface CreateToolData {
  name?: string;
  description?: string;
  tool_type?: string;
  api_schema?: Record<string, unknown>;
  config?: Record<string, unknown>;
  enabled?: boolean;
}

// ---------------------------------------------------------------------------
// API Client
// ---------------------------------------------------------------------------

const API_BASE = '/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private retryCount = 3;
  private retryDelay = 1000;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      timeout: 30000,
    });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      // Add request ID for tracing
      config.headers['X-Request-ID'] = crypto.randomUUID();
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const config = error.config;

        // Handle 401 - redirect to login
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/login';
          return Promise.reject(error);
        }

        // Retry on network errors or 5xx errors
        if (
          config &&
          (!error.response || (error.response.status >= 500 && error.response.status <= 599))
        ) {
          const retryConfig = config as any;
          retryConfig.__retryCount = retryConfig.__retryCount || 0;

          if (retryConfig.__retryCount < this.retryCount) {
            retryConfig.__retryCount += 1;
            const delay = this.retryDelay * Math.pow(2, retryConfig.__retryCount - 1);
            await new Promise(resolve => setTimeout(resolve, delay));
            return this.client(retryConfig);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Auth
  async login(username: string, password: string): Promise<TokenResponse> {
    const resp = await this.client.post('/auth/login', { username, password });
    return resp.data;
  }

  async getMe(): Promise<User> {
    const resp = await this.client.get('/auth/me');
    return resp.data;
  }

  // Agents
  async listAgents(page = 1, size = 20): Promise<PaginatedResponse<Agent>> {
    const resp = await this.client.get('/agents', { params: { page, size } });
    return resp.data;
  }

  async getAgent(id: string): Promise<Agent> {
    const resp = await this.client.get(`/agents/${id}`);
    return resp.data;
  }

  async createAgent(data: CreateAgentData): Promise<Agent> {
    const resp = await this.client.post('/agents', data);
    return resp.data;
  }

  async updateAgent(id: string, data: Partial<CreateAgentData>): Promise<Agent> {
    const resp = await this.client.put(`/agents/${id}`, data);
    return resp.data;
  }

  async publishAgent(id: string): Promise<Agent> {
    const resp = await this.client.post(`/agents/${id}/publish`);
    return resp.data;
  }

  async deleteAgent(id: string): Promise<StatusResponse> {
    const resp = await this.client.delete(`/agents/${id}`);
    return resp.data;
  }

  // Knowledge
  async listKnowledgeBases(page = 1, size = 20): Promise<PaginatedResponse<KnowledgeBase>> {
    const resp = await this.client.get('/knowledge/bases', { params: { page, size } });
    return resp.data;
  }

  async getKnowledgeBase(id: string): Promise<KnowledgeBase> {
    const resp = await this.client.get(`/knowledge/bases/${id}`);
    return resp.data;
  }

  async createKnowledgeBase(data: CreateKnowledgeBaseData): Promise<KnowledgeBase> {
    const resp = await this.client.post('/knowledge/bases', data);
    return resp.data;
  }

  async uploadDocument(kbId: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    const resp = await this.client.post(`/knowledge/bases/${kbId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return resp.data;
  }

  async deleteKnowledgeBase(id: string): Promise<StatusResponse> {
    const resp = await this.client.delete(`/knowledge/bases/${id}`);
    return resp.data;
  }

  // Models
  async listProviders(): Promise<ModelProvider[]> {
    const resp = await this.client.get('/models/providers');
    return resp.data;
  }

  async createProvider(data: CreateProviderData): Promise<ModelProvider> {
    const resp = await this.client.post('/models/providers', data);
    return resp.data;
  }

  async listModelConfigs(): Promise<ModelConfig[]> {
    const resp = await this.client.get('/models/configs');
    return resp.data;
  }

  async createModelConfig(data: CreateModelConfigData): Promise<ModelConfig> {
    const resp = await this.client.post('/models/configs', data);
    return resp.data;
  }

  async setDefaultModel(configId: string): Promise<ModelConfig> {
    const resp = await this.client.post(`/models/configs/${configId}/default`);
    return resp.data;
  }

  async discoverModels(providerId: string): Promise<any> {
    const resp = await this.client.get(`/models/discover/${providerId}`);
    return resp.data;
  }

  // Documents
  async listDocuments(kbId: string, page = 1, size = 50): Promise<PaginatedResponse<Document>> {
    const resp = await this.client.get(`/knowledge/bases/${kbId}/documents`, { params: { page, size } });
    return resp.data;
  }

  async deleteDocument(kbId: string, docId: string): Promise<StatusResponse> {
    const resp = await this.client.delete(`/knowledge/bases/${kbId}/documents/${docId}`);
    return resp.data;
  }

  // Document chunks
  async listChunks(kbId: string, docId?: string, page = 1, size = 50): Promise<PaginatedResponse<Chunk>> {
    const params: Record<string, unknown> = { page, size };
    if (docId) params.document_id = docId;
    const resp = await this.client.get(`/knowledge/bases/${kbId}/chunks`, { params });
    return resp.data;
  }

  // Retrieval test
  async retrievalTest(kbId: string, query: string, topK = 5): Promise<RetrievalResult[]> {
    const resp = await this.client.post(`/knowledge/bases/${kbId}/retrieve`, { query, top_k: topK });
    return resp.data;
  }

  // Conversations
  async listConversations(agentId?: string, page = 1, size = 20): Promise<PaginatedResponse<Conversation>> {
    const params: Record<string, unknown> = { page, size };
    if (agentId) params.agent_id = agentId;
    const resp = await this.client.get('/conversations', { params });
    return resp.data;
  }

  async getConversationMessages(convId: string): Promise<ChatMessage[]> {
    const resp = await this.client.get(`/conversations/${convId}/messages`);
    return resp.data;
  }

  async deleteConversation(convId: string): Promise<void> {
    await this.client.delete(`/conversations/${convId}`);
  }

  async searchConversations(query: string, page = 1, size = 20): Promise<PaginatedResponse<Conversation>> {
    const resp = await this.client.get('/conversations/search', { params: { query, page, size } });
    return resp.data;
  }

  // Provider / Config deletion
  async deleteProvider(id: string): Promise<StatusResponse> {
    const resp = await this.client.delete(`/models/providers/${id}`);
    return resp.data;
  }

  async deleteModelConfig(id: string): Promise<StatusResponse> {
    const resp = await this.client.delete(`/models/configs/${id}`);
    return resp.data;
  }

  // Chat
  async sendMessage(agentId: string, messages: { role: string; content: string }[]): Promise<ChatCompletionResponse> {
    const resp = await this.client.post('/chat/completions', { agent_id: agentId, messages });
    return resp.data;
  }

  // Tools
  async listBuiltinTools(): Promise<ToolInfo[]> {
    const resp = await this.client.get('/tools/builtin');
    return resp.data;
  }

  async listTools(toolType?: string): Promise<ToolInfo[]> {
    const params = toolType ? { tool_type: toolType } : {};
    const resp = await this.client.get('/tools', { params });
    return resp.data;
  }

  async createTool(data: CreateToolData): Promise<{ created?: string[]; count?: number; id?: string; name?: string; tool_type?: string }> {
    const resp = await this.client.post('/tools', data);
    return resp.data;
  }

  async deleteTool(id: string): Promise<StatusResponse> {
    const resp = await this.client.delete(`/tools/${id}`);
    return resp.data;
  }

  async executeTool(name: string, params: Record<string, unknown>, timeout = 30): Promise<ToolExecutionResult> {
    const resp = await this.client.post(`/tools/${name}/execute`, { params, timeout });
    return resp.data;
  }

  async getToolExecutions(toolName?: string, limit = 50): Promise<ToolExecutionResult[]> {
    const params: Record<string, unknown> = { limit };
    if (toolName) params.tool_name = toolName;
    const resp = await this.client.get('/tools/executions/history', { params });
    return resp.data;
  }

  // Feedbacks
  async createFeedback(data: { message_id: string; rating: string; comment?: string }): Promise<FeedbackResponse> {
    const resp = await this.client.post('/feedbacks', data);
    return resp.data;
  }

  async getFeedbackStats(agentId: string): Promise<FeedbackStats> {
    const resp = await this.client.get(`/feedbacks/stats/${agentId}`);
    return resp.data;
  }

  async createAnnotation(data: { message_id: string; corrected_answer: string; question?: string }): Promise<AnnotationResponse> {
    const resp = await this.client.post('/feedbacks/annotations', data);
    return resp.data;
  }

  async listAnnotations(page = 1, size = 20): Promise<Annotation[]> {
    const resp = await this.client.get('/feedbacks/annotations', { params: { page, size } });
    return resp.data;
  }

  // Audit
  async listAuditLogs(filters: Record<string, unknown> = {}, page = 1, size = 50): Promise<PaginatedResponse<AuditLog>> {
    const resp = await this.client.get('/audit', { params: { ...filters, page, size } });
    return resp.data;
  }

  // Workflows
  async listWorkflows(page = 1, size = 20): Promise<PaginatedResponse<any>> {
    const resp = await this.client.get('/workflows', { params: { page, size } });
    return resp.data;
  }

  async getWorkflow(id: string): Promise<any> {
    const resp = await this.client.get(`/workflows/${id}`);
    return resp.data;
  }

  async createWorkflow(data: { name: string; description?: string; nodes: any[]; edges: any[] }): Promise<any> {
    const resp = await this.client.post('/workflows', data);
    return resp.data;
  }

  async updateWorkflow(id: string, data: { name: string; description?: string; nodes: any[]; edges: any[] }): Promise<any> {
    const resp = await this.client.put(`/workflows/${id}`, data);
    return resp.data;
  }

  async deleteWorkflow(id: string): Promise<StatusResponse> {
    const resp = await this.client.delete(`/workflows/${id}`);
    return resp.data;
  }

  async runWorkflow(id: string, data: { nodes: any[]; edges: any[] }): Promise<any> {
    const resp = await this.client.post(`/workflows/${id}/run`, data);
    return resp.data;
  }

  // Marketplace
  async listMarketplaceItems(params?: {
    keyword?: string;
    category?: string;
    tags?: string;
    asset_type?: string;
    sort_by?: string;
    page?: number;
    size?: number;
  }): Promise<any> {
    const resp = await this.client.get('/marketplace/items', { params });
    return resp.data;
  }

  async getMarketplaceItem(id: string): Promise<any> {
    const resp = await this.client.get(`/marketplace/items/${id}`);
    return resp.data;
  }

  async getFeaturedItems(limit?: number): Promise<any> {
    const resp = await this.client.get('/marketplace/featured', { params: { limit } });
    return resp.data;
  }

  async getHotItems(limit?: number): Promise<any> {
    const resp = await this.client.get('/marketplace/hot', { params: { limit } });
    return resp.data;
  }

  async getMarketplaceCategories(): Promise<any> {
    const resp = await this.client.get('/marketplace/categories');
    return resp.data;
  }

  async createTrial(itemId: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/items/${itemId}/trial`);
    return resp.data;
  }

  async createRating(itemId: string, data: { score: number; comment?: string }): Promise<any> {
    const resp = await this.client.post(`/marketplace/items/${itemId}/rating`, data);
    return resp.data;
  }

  async getItemRatings(itemId: string, page?: number, size?: number): Promise<any> {
    const resp = await this.client.get(`/marketplace/items/${itemId}/ratings`, { params: { page, size } });
    return resp.data;
  }

  async getMyRating(itemId: string): Promise<any> {
    const resp = await this.client.get(`/marketplace/items/${itemId}/rating/me`);
    return resp.data;
  }

  async getWhiteboxView(itemId: string): Promise<any> {
    const resp = await this.client.get(`/marketplace/items/${itemId}/whitebox`);
    return resp.data;
  }

  async cloneItem(itemId: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/items/${itemId}/clone`);
    return resp.data;
  }

  async submitForReview(data: any): Promise<any> {
    const resp = await this.client.post('/marketplace/submissions', data);
    return resp.data;
  }

  async getMySubmissions(page?: number, size?: number): Promise<any> {
    const resp = await this.client.get('/marketplace/submissions', { params: { page, size } });
    return resp.data;
  }

  async cancelSubmission(itemId: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/submissions/${itemId}/cancel`);
    return resp.data;
  }

  // Marketplace Admin
  async listPendingReviews(page?: number, size?: number): Promise<any> {
    const resp = await this.client.get('/marketplace/admin/reviews', { params: { page, size } });
    return resp.data;
  }

  async listPendingPromotionReviews(page?: number, size?: number): Promise<any> {
    const resp = await this.client.get('/marketplace/admin/reviews/pending-promotion', { params: { page, size } });
    return resp.data;
  }

  async approveReview(itemId: string, comment?: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/admin/reviews/${itemId}/approve`, { comment });
    return resp.data;
  }

  async rejectReview(itemId: string, comment?: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/admin/reviews/${itemId}/reject`, { comment });
    return resp.data;
  }

  async freezeItem(itemId: string, reason?: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/admin/items/${itemId}/freeze`, { reason });
    return resp.data;
  }

  async unfreezeItem(itemId: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/admin/items/${itemId}/unfreeze`);
    return resp.data;
  }

  async takedownItem(itemId: string, reason?: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/admin/items/${itemId}/takedown`, { reason });
    return resp.data;
  }

  async promoteItem(itemId: string, targetLevel: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/admin/items/${itemId}/promote`, { target_level: targetLevel });
    return resp.data;
  }

  async setFeatured(itemId: string): Promise<any> {
    const resp = await this.client.post(`/marketplace/admin/items/${itemId}/feature`);
    return resp.data;
  }

  async unsetFeatured(itemId: string): Promise<any> {
    const resp = await this.client.delete(`/marketplace/admin/items/${itemId}/feature`);
    return resp.data;
  }

  async listAdminItems(params?: { status?: string; keyword?: string; page?: number; size?: number }): Promise<any> {
    const resp = await this.client.get('/marketplace/admin/items', { params });
    return resp.data;
  }

  async getMarketplaceStats(): Promise<any> {
    const resp = await this.client.get('/marketplace/admin/stats');
    return resp.data;
  }

  async getMarketplaceTrends(days?: number): Promise<any> {
    const resp = await this.client.get('/marketplace/admin/stats/trends', { params: { days } });
    return resp.data;
  }

  // API Tokens
  async listTokens(): Promise<any[]> {
    const resp = await this.client.get('/tokens');
    return resp.data;
  }

  async createToken(data: { name: string; permissions?: string[]; expiry_days?: number }): Promise<any> {
    const resp = await this.client.post('/tokens', data);
    return resp.data;
  }

  async revokeToken(tokenId: string): Promise<any> {
    const resp = await this.client.delete(`/tokens/${tokenId}`);
    return resp.data;
  }

  async updateToken(tokenId: string, data: { name?: string; permissions?: string[]; expiry_days?: number }): Promise<any> {
    const resp = await this.client.put(`/tokens/${tokenId}`, data);
    return resp.data;
  }

  // Publish Channels
  async listPublishChannels(agentId?: string): Promise<any[]> {
    const params = agentId ? { agent_id: agentId } : {};
    const resp = await this.client.get('/publish/channels', { params });
    return resp.data;
  }

  async createPublishChannel(data: { agent_id: string; type: string; name: string; config?: Record<string, any> }): Promise<any> {
    const resp = await this.client.post('/publish/channels', data);
    return resp.data;
  }

  async updatePublishChannel(channelId: string, data: { name?: string; status?: string; config?: Record<string, any> }): Promise<any> {
    const resp = await this.client.put(`/publish/channels/${channelId}`, data);
    return resp.data;
  }

  async deletePublishChannel(channelId: string): Promise<any> {
    const resp = await this.client.delete(`/publish/channels/${channelId}`);
    return resp.data;
  }

  async getPublishChannelStats(channelId: string): Promise<any> {
    const resp = await this.client.get(`/publish/channels/${channelId}/stats`);
    return resp.data;
  }

  // Knowledge URL Import
  async addUrlToKnowledgeBase(kbId: string, data: { url: string; chunk_size?: number; chunk_overlap?: number }): Promise<any> {
    const resp = await this.client.post(`/knowledge/bases/${kbId}/documents/url`, data);
    return resp.data;
  }

  async crawlUrlToKnowledgeBase(kbId: string, data: { url: string; max_pages?: number; allowed_domains?: string[]; chunk_size?: number; chunk_overlap?: number }): Promise<any> {
    const resp = await this.client.post(`/knowledge/bases/${kbId}/documents/crawl`, data);
    return resp.data;
  }

  // Agent Versions
  async listAgentVersions(agentId: string): Promise<any> {
    const resp = await this.client.get(`/agent-versions/${agentId}/versions`);
    return resp.data;
  }

  async createAgentVersion(agentId: string, data: { change_log?: string }): Promise<any> {
    const resp = await this.client.post(`/agent-versions/${agentId}/versions`, data);
    return resp.data;
  }

  async activateAgentVersion(agentId: string, versionId: string): Promise<any> {
    const resp = await this.client.put(`/agent-versions/${agentId}/versions/${versionId}/activate`);
    return resp.data;
  }

  async deleteAgentVersion(agentId: string, versionId: string): Promise<any> {
    const resp = await this.client.delete(`/agent-versions/${agentId}/versions/${versionId}`);
    return resp.data;
  }

  // A/B Tests
  async listABTests(agentId: string): Promise<any> {
    const resp = await this.client.get(`/agent-versions/${agentId}/ab-tests`);
    return resp.data;
  }

  async createABTest(agentId: string, data: { name: string; version_a: string; version_b: string; traffic_split: number }): Promise<any> {
    const resp = await this.client.post(`/agent-versions/${agentId}/ab-tests`, data);
    return resp.data;
  }

  async startABTest(agentId: string, testId: string): Promise<any> {
    const resp = await this.client.post(`/agent-versions/${agentId}/ab-tests/${testId}/start`);
    return resp.data;
  }

  async stopABTest(agentId: string, testId: string): Promise<any> {
    const resp = await this.client.post(`/agent-versions/${agentId}/ab-tests/${testId}/stop`);
    return resp.data;
  }

  async getABTestResults(agentId: string, testId: string): Promise<any> {
    const resp = await this.client.get(`/agent-versions/${agentId}/ab-tests/${testId}/results`);
    return resp.data;
  }

  // Workflow Versions & Executions
  async listWorkflowVersions(workflowId: string): Promise<any> {
    const resp = await this.client.get(`/workflows/${workflowId}/versions`);
    return resp.data;
  }

  async getWorkflowVersion(workflowId: string, versionId: string): Promise<any> {
    const resp = await this.client.get(`/workflows/${workflowId}/versions/${versionId}`);
    return resp.data;
  }

  async rollbackWorkflowVersion(workflowId: string, versionId: string): Promise<any> {
    const resp = await this.client.post(`/workflows/${workflowId}/versions/${versionId}/rollback`);
    return resp.data;
  }

  async listWorkflowExecutions(workflowId: string): Promise<any> {
    const resp = await this.client.get(`/workflows/${workflowId}/executions`);
    return resp.data;
  }

  async getWorkflowExecution(executionId: string): Promise<any> {
    const resp = await this.client.get(`/workflows/executions/${executionId}`);
    return resp.data;
  }

  async resumeWorkflowExecution(executionId: string): Promise<any> {
    const resp = await this.client.post(`/workflows/executions/${executionId}/resume`);
    return resp.data;
  }

  // Workflow Debug
  async startWorkflowDebug(workflowId: string, data: { mode: string; breakpoints?: string[] }): Promise<any> {
    const resp = await this.client.post(`/workflow-debug/${workflowId}/debug/start`, data);
    return resp.data;
  }

  async continueWorkflowDebug(workflowId: string, data: { action: string }): Promise<any> {
    const resp = await this.client.post(`/workflow-debug/${workflowId}/debug/continue`, data);
    return resp.data;
  }

  async stopWorkflowDebug(workflowId: string): Promise<any> {
    const resp = await this.client.post(`/workflow-debug/${workflowId}/debug/stop`);
    return resp.data;
  }

  async getWorkflowDebugState(workflowId: string): Promise<any> {
    const resp = await this.client.get(`/workflow-debug/${workflowId}/debug/state`);
    return resp.data;
  }

  // Generic methods — expose underlying Axios verbs for ad-hoc calls
  async get<T = any>(url: string, config?: Record<string, unknown>): Promise<T> {
    return this.client.get(url, config).then(r => r.data);
  }

  async post<T = any>(url: string, data?: unknown, config?: Record<string, unknown>): Promise<T> {
    return this.client.post(url, data, config).then(r => r.data);
  }

  async put<T = any>(url: string, data?: unknown, config?: Record<string, unknown>): Promise<T> {
    return this.client.put(url, data, config).then(r => r.data);
  }

  async patch<T = any>(url: string, data?: unknown, config?: Record<string, unknown>): Promise<T> {
    return this.client.patch(url, data, config).then(r => r.data);
  }

  async delete<T = any>(url: string, config?: Record<string, unknown>): Promise<T> {
    return this.client.delete(url, config).then(r => r.data);
  }

}

export const api = new ApiClient();
export default api;
