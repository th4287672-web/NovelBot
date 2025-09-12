// web-ui/stores/chat.ts

import { defineStore } from 'pinia';
import { ref, type Ref } from 'vue';
import { useWebSocket } from '~/services/websocket';
import { apiService } from '~/services/api';
import { useSettingsStore } from './settings';
import { useUIStore } from './ui';
import { useSessionStore } from './sessionStore';
import { useAigcStore } from './aigcStore';
import type { ChatMessage, TokenUsage, MessageActionType } from '~/types/api';

export type RequestStatus = 'idle' | 'sending' | 'thinking' | 'streaming' | 'error';

export const useChatStore = defineStore('chat', () => {
  const { sendMessage, onMessage } = useWebSocket();
  const settingsStore = useSettingsStore();
  const uiStore = useUIStore();
  const sessionStore = useSessionStore();
  
  const requestState = ref<{ status: RequestStatus, startTime: number | null }>({ status: 'idle', startTime: null });
  const streamingState = ref<{ messageId: number | null; isRegenerate: boolean }>({ messageId: null, isRegenerate: false });
  const suggestionState = ref<{ isLoading: boolean; suggestions: string[] }>({ isLoading: false, suggestions: [] });
  const isImpersonating = ref(false);
  const isVoiceMode = ref(false);
  const memorySuggestions = ref<string[]>([]);
  const activeAigcPolls = ref<Set<number>>(new Set());

  let unsubscribeCallbacks: (() => void)[] = [];
  
  // [核心修复] 将 onError 提升到 store 的顶层作用域
  const onError = (errorPayload: { code: string, message: string }) => {
    const targetId = streamingState.value.messageId;
    requestState.value = { status: 'error', startTime: null };

    if (targetId) {
      const targetMessage = sessionStore.findMessageById(targetId);
      if (targetMessage) {
          targetMessage.isStreaming = false;
          targetMessage.isComplete = false;
          targetMessage.isError = true;
          targetMessage.errorContent = errorPayload.message;
          if (targetMessage.content === 'AI正在思考...' || !targetMessage.content) {
              targetMessage.content = '生成失败';
          }
      }
    } else {
        sessionStore.addMessageToActiveSession({ role: 'model', content: '生成失败', isComplete: false, isError: true, errorContent: `[${errorPayload.code}] ${errorPayload.message}`});
    }

    streamingState.value = { messageId: null, isRegenerate: false };
  };

  async function _pollAigcTaskStatus(messageId: number, taskId: string) {
    if (!activeAigcPolls.value.has(messageId)) return;
    
    try {
        const task = await apiService.getTaskStatus(taskId);
        const message = sessionStore.findMessageById(messageId);
        if (!message || !message.aigcTask) {
            activeAigcPolls.value.delete(messageId);
            return;
        }

        if (task.status === 'success') {
            message.aigcTask = { taskId, status: 'success', imageUrl: task.result.image_url };
            activeAigcPolls.value.delete(messageId);
        } else if (task.status === 'failed') {
            message.aigcTask = { taskId, status: 'failed' };
            activeAigcPolls.value.delete(messageId);
        } else {
            setTimeout(() => _pollAigcTaskStatus(messageId, taskId), 5000);
        
        }
    } catch (error) {
        console.error(`Polling AIGC task ${taskId} failed:`, error);
        const message = sessionStore.findMessageById(messageId);
        if (message && message.aigcTask) message.aigcTask.status = 'failed';
        activeAigcPolls.value.delete(messageId);
    }
  }

  function initialize() {
    unsubscribeCallbacks.forEach(cb => cb());
    unsubscribeCallbacks = [];

    const onThinking = () => {
        requestState.value.status = 'thinking';
        if (!streamingState.value.isRegenerate) {
            const newMessage = sessionStore.addMessageToActiveSession({ role: 'model', content: 'AI正在思考...', isStreaming: true, isComplete: false });
            streamingState.value = { messageId: newMessage.id, isRegenerate: false };
        }
    };

    const onChunk = async (chunkPayload: string) => {
      if (requestState.value.status !== 'streaming') requestState.value.status = 'streaming';
      
      const targetId = streamingState.value.messageId;
      if (!targetId) return;

      const targetMessage = sessionStore.findMessageById(targetId);
      if(!targetMessage) return;

      if(targetMessage.content === 'AI正在思考...') targetMessage.content = '';
      
      if (streamingState.value.isRegenerate) {
          if (!targetMessage.alternatives) targetMessage.alternatives = [];
          
          const activeIndex = targetMessage.activeAlternative ?? (targetMessage.alternatives.length - 1);
          if (targetMessage.alternatives[activeIndex] === undefined) {
            targetMessage.alternatives[activeIndex] = chunkPayload;
          } else {
            targetMessage.alternatives[activeIndex] += chunkPayload;
          }
      } else {
        targetMessage.content += chunkPayload;
      }

      if (!targetMessage.aigcTask && !activeAigcPolls.value.has(targetId)) {
          const match = targetMessage.content.match(/<request_image prompt="(.+?)">/);
          if (match && match[1]) {
              const prompt = match[1];
              const aigcStore = useAigcStore();
              
              activeAigcPolls.value.add(targetId);
              
              const taskId = await aigcStore.generateTxt2ImgFromChat(prompt);

              if (taskId) {
                  targetMessage.aigcTask = { taskId, status: 'processing' };
                  _pollAigcTaskStatus(targetId, taskId);
              } else {
                  targetMessage.aigcTask = { taskId: 'failed-to-start', status: 'failed' };
                  activeAigcPolls.value.delete(targetId);
              }
          }
      }
    };

    const onFull = async (fullPayload: { full_content: string, notification: string, token_usage: TokenUsage | null }) => {
      const targetId = streamingState.value.messageId;
      requestState.value = { status: 'idle', startTime: null };

      if (!targetId) return;
      
      const targetMessage = sessionStore.findMessageById(targetId);
      if (targetMessage) {
        if (streamingState.value.isRegenerate) {
            if (targetMessage.alternatives && targetMessage.activeAlternative !== undefined) {
                targetMessage.alternatives[targetMessage.activeAlternative] = fullPayload.full_content;
            }
        } else {
            targetMessage.content = fullPayload.full_content;
        }
        targetMessage.isStreaming = false;
        targetMessage.isComplete = true;
        targetMessage.isError = false;
        if (fullPayload.token_usage) {
          targetMessage.tokenUsage = fullPayload.token_usage;
        }
      }
      
      streamingState.value = { messageId: null, isRegenerate: false };
      await saveCurrentHistory();
      
      if (isVoiceMode.value && targetMessage) {
        const { useCharacterStore } = await import('~/stores/characterStore');
        const { useTtsStore } = await import('~/stores/ttsStore');
        const characterStore = useCharacterStore();
        const ttsStore = useTtsStore();
        const activeChar = characterStore.activeCharacter;
        const charVoice = activeChar?.voice || settingsStore.ttsVoiceAssignments.char || 'zh-CN-XiaoxiaoNeural';
        const audio = await ttsStore.synthesizeBatch([[targetMessage.content, charVoice]]);
        audio?.play();
      }
    };
    
    const onMemorySuggestion = (suggestions: string[]) => {
      memorySuggestions.value = suggestions;
    };
    
    unsubscribeCallbacks.push(onMessage('thinking', onThinking));
    unsubscribeCallbacks.push(onMessage('chunk', onChunk));
    unsubscribeCallbacks.push(onMessage('full', onFull));
    unsubscribeCallbacks.push(onMessage('error', onError));
    unsubscribeCallbacks.push(onMessage('memory_suggestion', onMemorySuggestion));
  }

  async function saveCurrentHistory() {
      if (!sessionStore.activeSessionId || !settingsStore.userId) return;
      if ((saveCurrentHistory as any)._timeoutId) clearTimeout((saveCurrentHistory as any)._timeoutId);
      (saveCurrentHistory as any)._timeoutId = setTimeout(async () => {
          try { 
            const historyToSave = sessionStore.activeSessionMessages.map(({ id, ...rest }: ChatMessage) => rest);
            await apiService.updateSessionHistory(settingsStore.userId!, sessionStore.activeSessionId!, historyToSave); 
          }
          catch (error) { uiStore.setGlobalError(`自动保存历史记录失败: ${error}`); }
      }, 1000);
  }
  
  async function performMessageAction(messageId: number, action: MessageActionType) {
    if (requestState.value.status !== 'idle' && requestState.value.status !== 'error') return;
    
    const message = sessionStore.findMessageById(messageId);
    if (!message) return;

    const historyUpToMessage = sessionStore.getHistoryUpToMessage(messageId);
    const historyForApi = historyUpToMessage.slice(0, -1).map(({ id, ...rest }) => rest);
    const targetForApi = { role: message.role, content: message.content, isComplete: message.isComplete };

    requestState.value = { status: 'sending', startTime: Date.now() };
    streamingState.value = { messageId, isRegenerate: action === 'regenerate' || action === 'rewrite' };
    
    if (action === 'regenerate' || action === 'rewrite') {
        if (!message.alternatives) message.alternatives = [];
        message.alternatives.push('');
        message.activeAlternative = message.alternatives.length - 1;
        message.content = 'AI正在重写...';
    } else if (action === 'continue') {
        message.content += ' ';
    }
    
    message.isStreaming = true;
    message.isComplete = false;
    message.isError = false;

    try {
        const response = await apiService.performMessageAction(settingsStore.userId!, action, historyForApi, targetForApi);
        // ... 在这里处理来自新后端的流式响应 ...
    } catch (error) {
        onError({ code: 'ACTION_FAILED', message: `操作 '${action}' 失败: ${error}` });
    }
  }
  
  function send(content: string) {
    if (requestState.value.status !== 'idle' && requestState.value.status !== 'error') return;
    
    if (content.trim()) {
      sessionStore.addMessageToActiveSession({ role: 'user', content: content, isComplete: true });
      saveCurrentHistory(); 
    }
    
    requestState.value = { status: 'sending', startTime: Date.now() };

    sendMessage({
      message: content,
      action: 'new',
      session_id: sessionStore.activeSessionId,
    });
  }
  
  function continueMessage(messageId: number) {
      performMessageAction(messageId, 'continue');
  }

  function stopGeneration() {
      if (requestState.value.status === 'thinking' || requestState.value.status === 'streaming') {
          sendMessage({ action: 'stop', session_id: sessionStore.activeSessionId });
      }
  }
  
  function retryGeneration(failedMessageId: number) {
    sessionStore.deleteMessageInActiveSession(failedMessageId);
    const lastMessage = sessionStore.activeSessionMessages[sessionStore.activeSessionMessages.length - 1];
    if (lastMessage && lastMessage.role === 'user') {
      send(lastMessage.content);
    } else {
      uiStore.setGlobalError("无法重试：未找到有效的用户提问。");
    }
  }
  
  async function fetchSuggestions(guidance: string) {}

  function clearSuggestions() {
      suggestionState.value = { isLoading: false, suggestions: [] };
  }
  
  function regenerateMessage(messageId: number) {
    performMessageAction(messageId, 'regenerate');
  }

  function rewriteMessage(messageId: number) {
      performMessageAction(messageId, 'rewrite');
  }

  function regenerateOptions(messageId: number) {
      performMessageAction(messageId, 'regenerate_options');
  }

  function completeMessage(messageId: number) {
      performMessageAction(messageId, 'complete');
  }

  function clearMemorySuggestions() {
    memorySuggestions.value = [];
  }

  return { 
    requestState, suggestionState, isImpersonating,
    isVoiceMode, memorySuggestions,
    initialize,
    send,
    continueMessage,
    stopGeneration,
    retryGeneration,
    fetchSuggestions,
    clearSuggestions,
    clearMemorySuggestions,
    deleteMessage: sessionStore.deleteMessageInActiveSession,
    editMessage: sessionStore.editMessageInActiveSession,
    setActiveAlternative: sessionStore.setActiveAlternativeInMessage,
    regenerateMessage,
    rewriteMessage,
    regenerateOptions,
    completeMessage,
  };
});