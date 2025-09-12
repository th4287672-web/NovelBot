// web-ui/stores/memoryStore.ts

import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Filename, MemoryData, ChatMessage } from '~/types/api';
import { apiService } from '~/services/api';
import { useSettingsStore } from './settings';
import { useUIStore } from './ui';
import { deepClone } from '~/utils/helpers';

export const useMemoryStore = defineStore('memory', () => {
    const memories = ref<Record<Filename, MemoryData>>({});
    const isLoading = ref(false);

    async function fetchMemories(charFilename: Filename) {
        if (memories.value[charFilename]) return;

        const settingsStore = useSettingsStore();
        const uiStore = useUIStore();
        if (!settingsStore.userId) return; 
        isLoading.value = true;
        try {
            const data = await apiService.getMemories(settingsStore.userId, charFilename);
            memories.value[charFilename] = data;
        } catch (error) {
            uiStore.setGlobalError(`获取角色'${charFilename}'的记忆失败: ${error}`);
            memories.value[charFilename] = { entries: [] };
        } finally {
            isLoading.value = false;
        }
    }

    async function updateMemories(charFilename: Filename, data: MemoryData) {
        const settingsStore = useSettingsStore();
        const uiStore = useUIStore();
        if (!settingsStore.userId) return; 
        
        const oldData = deepClone(memories.value[charFilename] || { entries: [] });
        memories.value[charFilename] = data;
        isLoading.value = true;

        try {
            await apiService.updateMemories(settingsStore.userId, charFilename, data);
            uiStore.setGlobalError("记忆已保存！");
        } catch (error) {
            memories.value[charFilename] = oldData; 
            uiStore.setGlobalError(`保存角色'${charFilename}'的记忆失败: ${error}`);
        } finally {
            isLoading.value = false;
        }
    }
    
    async function extractMemoryFromHistory(charFilename: Filename, history: ChatMessage[]): Promise<string[]> {
        const settingsStore = useSettingsStore();
        const uiStore = useUIStore();
        if (!settingsStore.userId) return [];
        isLoading.value = true;
        try {
            const response = await apiService.extractMemoryFromHistory(settingsStore.userId, history);
            return response.data;
        } catch (error) {
            uiStore.setGlobalError(`AI提取记忆失败: ${error}`);
            return [];
        } finally {
            isLoading.value = false;
        }
    }

    return {
        memories,
        isLoading,
        fetchMemories,
        updateMemories,
        extractMemoryFromHistory
    };
});