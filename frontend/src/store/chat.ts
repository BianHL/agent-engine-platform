import { create } from 'zustand';
import { ChatMessage } from '@/types';

interface ChatState {
  messages: ChatMessage[];
  streaming: boolean;
  error: string | null;
  abortController: AbortController | null;
  addMessage: (msg: ChatMessage) => void;
  updateLastMessage: (content: string) => void;
  setStreaming: (v: boolean) => void;
  setError: (e: string | null) => void;
  clearMessages: () => void;
  sendMessage: (agentId: string, content: string, signal?: AbortSignal) => Promise<void>;
  sendFileMessage: (agentId: string, file: File, message: string) => Promise<void>;
  stopGeneration: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  streaming: false,
  error: null,
  abortController: null,

  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),

  updateLastMessage: (content) =>
    set((state) => {
      const msgs = [...state.messages];
      if (msgs.length > 0) {
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content };
      }
      return { messages: msgs };
    }),

  setStreaming: (v) => set({ streaming: v }),
  setError: (e) => set({ error: e }),
  clearMessages: () => set({ messages: [], error: null }),

  stopGeneration: () => {
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
      set({ streaming: false, abortController: null });
    }
  },

  sendMessage: async (agentId: string, content: string, signal?: AbortSignal) => {
    const userMsg: ChatMessage = {
      id: typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      status: 'completed',
    };
    get().addMessage(userMsg);

    const assistantMsg: ChatMessage = {
      id: typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      status: 'running',
    };
    get().addMessage(assistantMsg);
    set({ streaming: true, error: null });

    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // 如果提供了 signal（来自外部 AbortController），使用它
      // 否则创建新的
      const controller = signal ? undefined : new AbortController();
      if (controller) {
        set({ abortController: controller });
      }

      const response = await fetch(`/api/v1/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agent_id: agentId,
          messages: get().messages.slice(0, -1).map((m) => ({ role: m.role, content: m.content })),
        }),
        signal: signal || controller?.signal,
      });

      if (!response.ok) throw new Error('Stream failed');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.done) {
                  set({
                    streaming: false,
                    abortController: null,
                  });
                  // 更新最后一条消息状态为完成
                  get().updateLastMessage(get().messages[get().messages.length - 1].content);
                  return;
                }
                if (data.content) {
                  const current = get().messages;
                  const last = current[current.length - 1];
                  get().updateLastMessage(last.content + data.content);
                }
              } catch {
                console.warn('SSE parse error:', line.slice(6));
              }
            }
          }
        }
      }
      set({
        streaming: false,
        abortController: null,
      });
    } catch (error: any) {
      // 如果是主动中止，不显示错误
      if (error.name === 'AbortError') {
        set({ streaming: false, abortController: null });
        return;
      }
      set({ streaming: false, error: error.message, abortController: null });
    }
  },

  sendFileMessage: async (agentId: string, file: File, message: string) => {
    const fileLabel = `[📎 ${file.name} (${(file.size / 1024).toFixed(1)}KB)]`;
    const displayContent = message ? `${message}\n${fileLabel}` : fileLabel;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: displayContent,
      created_at: new Date().toISOString(),
      status: 'completed',
      metadata: { fileName: file.name, fileSize: file.size, fileType: file.type },
    };
    get().addMessage(userMsg);

    const assistantMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      status: 'running',
    };
    get().addMessage(assistantMsg);
    set({ streaming: true, error: null });

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('agent_id', agentId);
      formData.append('message', message);
      formData.append('file', file);

      const response = await fetch('/api/v1/chat/upload', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      get().updateLastMessage(data.content);
      set({ streaming: false, abortController: null });
    } catch (error: any) {
      if (error.name === 'AbortError') {
        set({ streaming: false, abortController: null });
        return;
      }
      set({ streaming: false, error: error.message, abortController: null });
    }
  },
}));
