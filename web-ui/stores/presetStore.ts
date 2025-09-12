import { defineStore } from 'pinia';
import { computed, ref, watch } from 'vue';
import type { Preset, Filename, BackendPreset, AllDataResponse, BootstrapResponse } from '~/types/api';
import { useSettingsStore } from './settings';
import { BOOTSTRAP_QUERY_KEY, usePaginatedData } from '~/composables/useAllData';
import { useDataMutations } from '~/composables/useDataMutations';
import { apiService } from '~/services/api';
import { useUIStore } from './ui';
import { v4 as uuidv4 } from 'uuid';
import { useInvalidateAllData } from '~/composables/useAllData';
import { useQueryClient } from '@tanstack/vue-query';

export const usePresetStore = defineStore('preset', () => {
    const { createOrUpdate, createOrUpdateAsync, rename, delete: deleteData } = useDataMutations();
    const invalidateAllData = useInvalidateAllData();
    const queryClient = useQueryClient();
    const settingsStore = useSettingsStore();
    
    const presets = computed<Record<string, Preset>>(() => {
        const bootstrapData = queryClient.getQueryData<BootstrapResponse>([BOOTSTRAP_QUERY_KEY, settingsStore.userId]);
        const paginatedQueries = queryClient.getQueryCache().findAll({ queryKey: ['paginatedData', 'preset'] });
      
        const allPresetsMap = new Map<Filename, Preset>();
  
        if (bootstrapData?.public_presets) {
            Object.entries(bootstrapData.public_presets).forEach(([filename, presetData]) => {
                const backendPreset = presetData as BackendPreset;
                allPresetsMap.set(filename, { 
                    ...backendPreset, 
                    filename, 
                    is_private: false, 
                    name: backendPreset.name || filename,
                    displayName: backendPreset.displayName || backendPreset.name || filename 
                });
            });
        }
        
        paginatedQueries.forEach(query => {
            const pageData = query.state.data as any;
            if (pageData && pageData.items) {
                pageData.items.forEach((preset: Preset) => {
                    allPresetsMap.set(preset.filename, { ...preset, displayName: preset.displayName || preset.name });
                });
            }
        });
  
        return Object.fromEntries(allPresetsMap);
    });
    
    const debugState = ref({
        isLoading: false,
        promptText: '',
    });

    const importablePresets = computed(() => {
        const bootstrapData = queryClient.getQueryData<BootstrapResponse>([BOOTSTRAP_QUERY_KEY, settingsStore.userId]);
        if (!bootstrapData?.public_presets) return [];

        const paginatedQueries = queryClient.getQueryCache().findAll({ queryKey: ['paginatedData', 'preset'] });
        const displayedFilenames = new Set<Filename>();

        paginatedQueries.forEach(query => {
            const pageData = query.state.data as any;
            if (pageData && pageData.items) {
                pageData.items.forEach((preset: Preset) => displayedFilenames.add(preset.filename));
            }
        });
        
        return Object.entries(bootstrapData.public_presets)
            .filter(([filename, _]) => !displayedFilenames.has(filename))
            .map(([filename, p]) => {
                const presetData = p as BackendPreset;
                return {
                    name: presetData.name || filename,
                    displayName: presetData.displayName || presetData.name || filename,
                    prompts: presetData.prompts || [],
                    filename: filename,
                    is_private: true,
                } as Preset;
            });
    });
    
    async function setActivePreset(presetFilename: Filename) {
        const settingsStore = useSettingsStore();
        await settingsStore.setActivePreset(presetFilename);
    }
    
    async function createPreset(presetData: Omit<Preset, 'filename'>): Promise<Filename | null> {
        try {
            const response = await createOrUpdateAsync({
                dataType: 'preset',
                filename: presetData.displayName,
                data: presetData,
                isEditing: false
            });
            return response.filename; 
        } catch (e) {
            console.error("Failed to create preset in store action:", e);
            return null;
        }
    }

    function renamePreset(oldFilename: Filename, newDisplayName: string) {
        rename({
            dataType: 'preset',
            oldFilename: oldFilename,
            newDisplayName: newDisplayName,
        });
    }
    
    async function deletePreset(filename: Filename) {
        const settingsStore = useSettingsStore();
        const bootstrapData = queryClient.getQueryData<BootstrapResponse>([BOOTSTRAP_QUERY_KEY, settingsStore.userId]);
        const isPublicTemplate = !!bootstrapData?.public_presets?.[filename];

        if (settingsStore.activePresetName === filename) {
            await setActivePreset('百变助手');
        }
        deleteData({ dataType: 'preset', filename: filename });

        if (isPublicTemplate) {
            const userConfig = settingsStore.userFullConfig;
            if (userConfig) {
                const deletedItems = userConfig.deleted_public_items || [];
                const identifier = `preset:${filename}`;
                if (!deletedItems.includes(identifier)) {
                    await settingsStore.updateUserConfigValue('deleted_public_items', [...deletedItems, identifier]);
                    invalidateAllData();
                }
            }
        }
    }

    async function clonePreset(originalPreset: Preset) {
        const { filename, ...apiData } = originalPreset;
        const newDisplayName = `${originalPreset.displayName} (副本)`;
        const newData: Omit<Preset, 'filename'> = {
            ...apiData,
            name: newDisplayName,
            displayName: newDisplayName,
            is_private: true,
            prompts: apiData.prompts ? JSON.parse(JSON.stringify(apiData.prompts)) : [],
        };
        await createPreset(newData);
    }
    
    function updatePreset(preset: Preset) {
        const { filename, ...apiData } = preset;
        createOrUpdate({
            dataType: 'preset',
            filename: filename,
            data: apiData,
            isEditing: true
        });
    }

    async function importPublicPresets(filenames: string[]) {
        const settingsStore = useSettingsStore();
        if(!settingsStore.userFullConfig) return;
        
        const currentDeleted = settingsStore.userFullConfig.deleted_public_items || [];
        const newDeleted = currentDeleted.filter((id: string) => !filenames.some(fname => id === `preset:${fname}`));

        await settingsStore.updateUserConfigValue('deleted_public_items', newDeleted);
        invalidateAllData();
    }
    
    function importPresetFromObject(parsedJson: any, filename: string): Preset | null {
        const uiStore = useUIStore();
        
        if (typeof parsedJson !== 'object' || parsedJson === null || !Array.isArray(parsedJson.prompts)) {
            uiStore.setGlobalError("导入失败：文件不是有效的预设格式 (缺少 'prompts' 数组)。");
            return null;
        }

        const presetName = filename.replace(/\.json$/i, '');
        
        const newPreset: Preset = {
            name: parsedJson.name || presetName,
            displayName: parsedJson.displayName || presetName,
            filename: `imported_${Date.now()}`,
            is_private: true,
            prompts: [],
            prompt_order: parsedJson.prompt_order || [],
        };

        newPreset.prompts = parsedJson.prompts.map((p: any) => ({
            identifier: p.identifier || uuidv4(),
            name: p.name || '未命名模块',
            system_prompt: p.system_prompt ?? true,
            enabled: p.enabled ?? true,
            marker: p.marker ?? false,
            role: p.role || 'system',
            content: p.content || '',
            injection_position: p.injection_position ?? 0,
            injection_depth: p.injection_depth ?? 4,
            injection_order: p.injection_order ?? 100,
            forbid_overrides: p.forbid_overrides ?? false,
        }));

        return newPreset;
    }

    async function debugPreset(preset: Preset, userMessage: string) {
        const settingsStore = useSettingsStore();
        const uiStore = useUIStore();
        if (!settingsStore.userFullConfig || !settingsStore.userId) return;

        debugState.value.isLoading = true;
        debugState.value.promptText = '';
        try {
            const debugConfig = {
                ...settingsStore.userFullConfig,
                user_id: settingsStore.userId,
                preset: preset.name,
                active_modules: {
                    [preset.name]: preset.prompts?.filter(p => p.enabled).map(p => p.identifier) || []
                }
            };
            
            const response = await apiService.debugPresetPrompt(debugConfig, userMessage);
            debugState.value.promptText = response.prompt;
        } catch (error) {
            uiStore.setGlobalError(`预设调试失败: ${error}`);
            debugState.value.promptText = `错误: ${error}`;
        } finally {
            debugState.value.isLoading = false;
        }
    }


    return {
        presets,
        importablePresets,
        debugState,
        setActivePreset,
        createPreset,
        renamePreset,
        deletePreset,
        clonePreset,
        updatePreset,
        importPublicPresets,
        importPresetFromObject,
        debugPreset,
    };
});