import { defineStore } from 'pinia';
import { computed, ref, watch } from 'vue';
import type { WorldInfo, Filename, BackendWorldInfo, Character, AllDataResponse, BootstrapResponse } from '~/types/api';
import { useSettingsStore } from './settings';
import { useCharacterStore } from './characterStore';
import { BOOTSTRAP_QUERY_KEY } from '~/composables/useAllData';
import { useDataMutations } from '~/composables/useDataMutations';
import { apiService } from '~/services/api';
import { useUIStore } from './ui';
import { useInvalidateAllData } from '~/composables/useAllData';
import { useQueryClient } from '@tanstack/vue-query';

export const useWorldStore = defineStore('world', () => {
    const { createOrUpdate, delete: deleteData } = useDataMutations();
    const invalidateAllData = useInvalidateAllData();
    const queryClient = useQueryClient();
    const settingsStore = useSettingsStore();

    const worldInfo = computed<Record<string, WorldInfo>>(() => {
        const bootstrapData = queryClient.getQueryData<BootstrapResponse>([BOOTSTRAP_QUERY_KEY, settingsStore.userId]);
        const paginatedQueries = queryClient.getQueryCache().findAll({ queryKey: ['paginatedData', 'world_info'] });
      
        const allWorldsMap = new Map<Filename, WorldInfo>();
  
        paginatedQueries.forEach(query => {
            const pageData = query.state.data as any;
            if (pageData && pageData.items) {
                pageData.items.forEach((world: WorldInfo) => {
                    allWorldsMap.set(world.filename, { ...world, name: world.name || world.filename });
                });
            }
        });

        if (bootstrapData?.public_world_info) {
            Object.entries(bootstrapData.public_world_info).forEach(([filename, worldData]) => {
                if (!allWorldsMap.has(filename)) {
                    const backendWorldInfo = worldData as BackendWorldInfo;
                    allWorldsMap.set(filename, { 
                        ...backendWorldInfo, 
                        filename, 
                        is_private: false, 
                        name: backendWorldInfo.name || filename,
                    });
                }
            });
        }
  
        return Object.fromEntries(allWorldsMap);
    });

    const importableWorlds = computed(() => {
        const bootstrapData = queryClient.getQueryData<BootstrapResponse>([BOOTSTRAP_QUERY_KEY, settingsStore.userId]);
        if (!bootstrapData?.public_world_info) return [];

        const paginatedQueries = queryClient.getQueryCache().findAll({ queryKey: ['paginatedData', 'world_info'] });
        const displayedFilenames = new Set<Filename>();

        paginatedQueries.forEach(query => {
            const pageData = query.state.data as any;
            if (pageData && pageData.items) {
                pageData.items.forEach((world: WorldInfo) => displayedFilenames.add(world.filename));
            }
        });

        return Object.entries(bootstrapData.public_world_info)
            .filter(([filename, _]) => !displayedFilenames.has(filename))
            .map(([filename, worldData]) => ({
                ...(worldData as BackendWorldInfo),
                filename: filename,
                is_private: true,
                entries: (worldData as BackendWorldInfo).entries || [],
            }));
    });

    function createOrUpdateWorldBook(filename: Filename, newBookData: Omit<WorldInfo, 'filename'>, isEditing: boolean) {
        createOrUpdate({
            dataType: 'world_info',
            filename: filename,
            data: newBookData,
            isEditing: isEditing,
        });
    }
    
    async function deleteWorldBook(filename: Filename) {
        const bootstrapData = queryClient.getQueryData<BootstrapResponse>([BOOTSTRAP_QUERY_KEY, settingsStore.userId]);
        const isPublicTemplate = !!bootstrapData?.public_world_info?.[filename];

        await handleWorldBookDeletion(filename);
        deleteData({ dataType: 'world_info', filename: filename });

        if (isPublicTemplate) {
            const settingsStore = useSettingsStore();
            const userConfig = settingsStore.userFullConfig;
            if (userConfig) {
                const deletedItems = userConfig.deleted_public_items || [];
                const identifier = `world_info:${filename}`;
                if (!deletedItems.includes(identifier)) {
                    await settingsStore.updateUserConfigValue('deleted_public_items', [...deletedItems, identifier]);
                    invalidateAllData();
                }
            }
        }
    }

    async function generateWorldBook(prompt: string, selectedPresets?: Filename[], selectedWorlds?: Filename[]): Promise<Omit<BackendWorldInfo, 'is_private'> | null> {
        const uiStore = useUIStore();
        const settingsStore = useSettingsStore();
        if (!settingsStore.userId) {
            uiStore.setGlobalError("用户未登录，无法生成世界书。");
            return null;
        }
        try {
            const response = await apiService.generateWorldInfo(settingsStore.userId, prompt, selectedPresets, selectedWorlds);
            return JSON.parse(response.data) as Omit<BackendWorldInfo, 'is_private'>;
        } catch (error) {
            uiStore.setGlobalError(`AI生成世界书失败: ${error}`);
            return null;
        }
    }

    async function handleWorldBookDeletion(filename: Filename) {
        const settingsStore = useSettingsStore();
        const characterStore = useCharacterStore();
        
        for (const char of Object.values(characterStore.characters)) {
            if (char.is_private && char.linked_worlds?.includes(filename)) {
                const updatedWorlds = char.linked_worlds.filter(w => w !== filename);
                const { filename: charFilename, ...apiData } = char;
                const backendData: Omit<Character, 'filename'> = { 
                    ...apiData, 
                    linked_worlds: updatedWorlds 
                };
                characterStore.createOrUpdateCharacter(charFilename, backendData, true);
            }
        }
        
        if (settingsStore.userConfig?.world_info.includes(filename)) {
            const updatedSessionWorlds = settingsStore.userConfig.world_info.filter((w: Filename) => w !== filename);
            await settingsStore.updateUserConfigValue('world_info', updatedSessionWorlds);
        }
    }

    async function importPublicWorlds(filenames: string[]) {
        const settingsStore = useSettingsStore();
        if(!settingsStore.userFullConfig) return;
        
        const currentDeleted = settingsStore.userFullConfig.deleted_public_items || [];
        const newDeleted = currentDeleted.filter((id: string) => !filenames.some(fname => id === `world_info:${fname}`));

        await settingsStore.updateUserConfigValue('deleted_public_items', newDeleted);
        invalidateAllData();
    }

    async function toggleSessionWorld(filename: Filename) {
        const settingsStore = useSettingsStore();
        if (!settingsStore.userConfig) return;
        const currentSessionWorlds = [...settingsStore.userConfig.world_info];
        const index = currentSessionWorlds.indexOf(filename);
        if (index > -1) {
            currentSessionWorlds.splice(index, 1);
        } else {
            currentSessionWorlds.push(filename);
        }
        await settingsStore.updateUserConfigValue('world_info', currentSessionWorlds);
    }
    
    async function syncWorldBooksToGoogle(worldsToSync: WorldInfo[]) {
        const settingsStore = useSettingsStore();
        const uiStore = useUIStore();
        if (!settingsStore.userId) {
            uiStore.setGlobalError('用户ID未找到，无法同步。');
            return;
        }
        try {
            const payload = worldsToSync.map(({ filename, is_private, ...data }) => data);
            const response = await apiService.syncWorldBooks(settingsStore.userId, payload);
            uiStore.setGlobalError(response.message || '世界书同步成功！');
        } catch (error) {
            uiStore.setGlobalError(`同步世界书失败: ${error}`);
        }
    }

    return {
        worldInfo,
        importableWorlds,
        createOrUpdateWorldBook,
        deleteWorldBook,
        generateWorldBook,
        handleWorldBookDeletion,
        importPublicWorlds,
        toggleSessionWorld,
        syncWorldBooksToGoogle,
    };
});