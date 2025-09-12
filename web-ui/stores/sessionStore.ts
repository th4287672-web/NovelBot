// web-ui/stores/sessionStore.ts

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Session, ChatMessage, Filename, SessionID } from '~/types/api';
import { apiService } from '~/services/api';
import { useSettingsStore } from './settings';
import { useUIStore } from './ui';
import { deepClone } from '~/utils/helpers';

export const useSessionStore = defineStore('session', () => {
    const sessionsByChar = ref<Record<Filename, Session[]>>({});
    const activeSessionId = ref<SessionID | null>(null);
    const messageHistoryCache = ref<Record<SessionID, ChatMessage[]>>({});
    const titleGenerating = ref<Set<SessionID>>(new Set());

    const activeSessionMessages = computed<ChatMessage[]>(() => {
        return activeSessionId.value ? messageHistoryCache.value[activeSessionId.value] || [] : [];
    });

    const isTitleGenerating = (sessionId: SessionID) => computed(() => titleGenerating.value.has(sessionId));

    async function loadSessionsForCharacter(charFilename: Filename) {
        const settingsStore = useSettingsStore();
        const uiStore = useUIStore();
        if (!settingsStore.userId) return;
        if (settingsStore.isAnonymous) {
            sessionsByChar.value[charFilename] = [];
            activeSessionId.value = null;
            messageHistoryCache.value = {};
            return;
        }
        try {
            const sessions = await apiService.getSessionsForCharacter(settingsStore.userId, charFilename);
            sessionsByChar.value[charFilename] = sessions;
            
            const activeIdFromConfig = settingsStore.userConfig?.active_session_id;
            const isValidActiveId = sessions.some(s => s.id === activeIdFromConfig);

            let targetSessionId: SessionID | null = null;
            if (isValidActiveId && activeIdFromConfig) {
                targetSessionId = activeIdFromConfig;
            } else if (sessions.length > 0 && sessions[0]) {
                targetSessionId = sessions[0].id;
            }

            if (targetSessionId) {
                await setActiveSession(targetSessionId);
            } else if (!settingsStore.isAnonymous) {
                await createNewSession(charFilename);
            }

        } catch (error) {
            uiStore.setGlobalError(`加载角色 '${charFilename}' 的会话列表失败: ${error}`);
        }
    }

    async function setActiveSession(sessionId: SessionID) {
        if (activeSessionId.value === sessionId) return;

        activeSessionId.value = sessionId;
        const settingsStore = useSettingsStore();
        await settingsStore.updateUserConfigValue('active_session_id', sessionId);
        
        if (messageHistoryCache.value[sessionId] === undefined) {
            await loadHistoryForSession(sessionId);
        }
    }

    async function loadHistoryForSession(sessionId: SessionID) {
        const settingsStore = useSettingsStore();
        const uiStore = useUIStore();
        if (!settingsStore.userId) return;
        try {
            const history = await apiService.getSessionHistory(settingsStore.userId, sessionId);
            const formattedHistory = history.map((msg, index) => ({ id: Date.now() + index + Math.random(), ...msg }));
            
            messageHistoryCache.value = {
                ...messageHistoryCache.value,
                [sessionId]: formattedHistory,
            };
            
        } catch (error) {
            uiStore.setGlobalError(`加载会话历史 #${sessionId} 失败: ${error}`);
            messageHistoryCache.value = {
                ...messageHistoryCache.value,
                [sessionId]: [],
            };
        }
    }
    
    function updateMessageHistoryCache(sessionId: SessionID, messages: ChatMessage[]) {
        if (sessionId) {
            messageHistoryCache.value = {
                ...messageHistoryCache.value,
                [sessionId]: messages,
            };
        }
    }

    function findMessageById(messageId: number): ChatMessage | undefined {
        if (!activeSessionId.value) return undefined;
        const history = messageHistoryCache.value[activeSessionId.value];
        return history ? history.find(m => m.id === messageId) : undefined;
    }

    function getHistoryUpToMessage(messageId: number): ChatMessage[] {
        if (!activeSessionId.value) return [];
        const history = messageHistoryCache.value[activeSessionId.value] || [];
        const index = history.findIndex(m => m.id === messageId);
        return index > -1 ? history.slice(0, index + 1) : history;
    }
    
    function addMessageToActiveSession(message: Omit<ChatMessage, 'id'>): ChatMessage {
        const newMessage: ChatMessage = { id: Date.now() + Math.random(), ...message };
        const currentSessionId = activeSessionId.value;
        
        if (currentSessionId) {
            if (!Array.isArray(messageHistoryCache.value[currentSessionId])) {
                messageHistoryCache.value[currentSessionId] = [];
            }
            messageHistoryCache.value[currentSessionId].push(newMessage);
        }
        return newMessage;
    }

    function deleteMessageInActiveSession(messageId: number) {
        const currentSessionId = activeSessionId.value;
        if (currentSessionId) {
            const currentHistory = messageHistoryCache.value[currentSessionId] || [];
            const newHistory = currentHistory.filter(m => m.id !== messageId);
            messageHistoryCache.value = {
                ...messageHistoryCache.value,
                [currentSessionId]: newHistory,
            };
        }
    }
    
    function editMessageInActiveSession(payload: { messageId: number, newContent: string }) {
        const { messageId, newContent } = payload;
        const message = findMessageById(messageId);
        if (message && newContent.trim()) {
            if (message.activeAlternative !== undefined && message.alternatives && message.activeAlternative > -1) {
                message.alternatives[message.activeAlternative] = newContent;
            } else {
                message.content = newContent;
            }
        }
    }

    function setActiveAlternativeInMessage(payload: { messageId: number, index: number }) {
        const { messageId, index } = payload;
        const message = findMessageById(messageId);
        if (message) {
            const total = 1 + (message.alternatives?.length ?? 0);
            if (index >= -1 && index < total) {
                message.activeAlternative = index;
            }
        }
    }

    async function createNewSession(charFilename: Filename): Promise<Session | null> {
        const settingsStore = useSettingsStore();
        const uiStore = useUIStore();
        if (!settingsStore.userId || settingsStore.isAnonymous) return null;
        try {
            const newSession = await apiService.createNewSession(settingsStore.userId, charFilename);
            if (!sessionsByChar.value[charFilename]) {
                sessionsByChar.value[charFilename] = [];
            }
            sessionsByChar.value[charFilename].unshift(newSession);
            await setActiveSession(newSession.id);
            return newSession;
        } catch (error) {
            uiStore.setGlobalError(`为角色 '${charFilename}' 创建新会话失败: ${error}`);
            return null;
        }
    }
    
    async function renameSession(sessionId: SessionID, newTitle: string) {
        const settingsStore = useSettingsStore();
        const charFilename = settingsStore.activeCharacterKey;
        if (!charFilename || !settingsStore.userId) return;
        
        const sessions = sessionsByChar.value[charFilename];
        if (!sessions) return;

        const session = sessions.find(s => s.id === sessionId);
        if (!session || session.title === newTitle) return;

        const oldTitle = session.title;
        session.title = newTitle;

        try {
            await apiService.renameSession(settingsStore.userId, sessionId, newTitle);
        } catch (error) {
            session.title = oldTitle;
            useUIStore().setGlobalError(`重命名会话失败: ${error}`);
        }
    }

    async function generateSessionTitle(charFilename: Filename, sessionId: SessionID) {
        const uiStore = useUIStore();
        const settingsStore = useSettingsStore();
        if (!settingsStore.userId) return;
        titleGenerating.value.add(sessionId);
        try {
            const response = await apiService.generateSessionTitle(settingsStore.userId, sessionId);
            await renameSession(sessionId, response.title);
        } catch (error) {
            uiStore.setGlobalError(`AI命名会话失败: ${error}`);
        } finally {
            titleGenerating.value.delete(sessionId);
        }
    }
    
    async function deleteSession(charFilename: Filename, sessionId: SessionID) {
        const uiStore = useUIStore();
        const settingsStore = useSettingsStore();
        if (!settingsStore.userId) return;

        const oldSessions = deepClone(sessionsByChar.value[charFilename] || []);
        const sessionIndex = oldSessions.findIndex(s => s.id === sessionId);
        if (sessionIndex === -1) return;

        sessionsByChar.value[charFilename] = oldSessions.filter(s => s.id !== sessionId);
        
        try {
            await apiService.deleteSession(settingsStore.userId, sessionId);

            if (activeSessionId.value === sessionId) {
                const remainingSessions = sessionsByChar.value[charFilename] || [];
                if (remainingSessions.length > 0 && remainingSessions[0]) {
                    await setActiveSession(remainingSessions[0].id);
                } else {
                    await createNewSession(charFilename);
                }
            }
        } catch (error) {
            sessionsByChar.value[charFilename] = oldSessions;
            uiStore.setGlobalError(`删除会话 #${sessionId} 失败: ${error}`);
        }
    }

    return {
        sessionsByChar,
        activeSessionId,
        messageHistoryCache,
        activeSessionMessages,
        isTitleGenerating,
        loadSessionsForCharacter,
        setActiveSession,
        loadHistoryForSession,
        updateMessageHistoryCache,
        createNewSession,
        renameSession,
        generateSessionTitle,
        deleteSession,
        findMessageById,
        getHistoryUpToMessage,
        addMessageToActiveSession,
        deleteMessageInActiveSession,
        editMessageInActiveSession,
        setActiveAlternativeInMessage,
    };
});