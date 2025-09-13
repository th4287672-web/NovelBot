import { defineStore } from 'pinia'
import { computed } from 'vue';
import type { Character, Filename, BackendCharacter, AllDataResponse, BootstrapResponse, PaginatedData, TaskSubmissionResponse } from '~/types/api';
import { useSettingsStore } from './settings';
import { useSessionStore } from './sessionStore';
import { BOOTSTRAP_QUERY_KEY, usePaginatedData } from '~/composables/useAllData';
import { useDataMutations } from '~/composables/useDataMutations';
import { apiService } from '~/services/api';
import { useUIStore } from './ui';
import { useInvalidateAllData } from '~/composables/useAllData';
import { useQueryClient } from '@tanstack/vue-query';
import { useTaskStore } from './taskStore'; 

export const useCharacterStore = defineStore('character', () => {
    const { createOrUpdate, rename, delete: deleteData } = useDataMutations();
    const invalidateAllData = useInvalidateAllData();
    const queryClient = useQueryClient();
    const settingsStore = useSettingsStore();
    const taskStore = useTaskStore(); 
    const uiStore = useUIStore();
    
    const characters = computed<Record<string, Character>>(() => {
      const bootstrapData = queryClient.getQueryData<BootstrapResponse>([BOOTSTRAP_QUERY_KEY, settingsStore.userId]);
      const paginatedQueries = queryClient.getQueryCache().findAll({ queryKey: ['paginatedData', 'character'] });
      const paginatedPersonasQueries = queryClient.getQueryCache().findAll({ queryKey: ['paginatedData', 'persona'] });
      const userConfig = settingsStore.userFullConfig;
      const deletedPublicIds = new Set(userConfig?.deleted_public_items || []);

      const allCharsMap = new Map<Filename, Character>();
      
      const processCharData = (char: Character, filename: Filename, isPrivate: boolean): Character => {
          return { 
              ...char, 
              filename, 
              is_private: isPrivate, 
              displayName: char.displayName || char.name,
              image: char.image
          };
      };
      
      const processQuery = (query: any) => {
        const pageData = query.state.data as PaginatedData<Character>;
        if (pageData && pageData.items) {
          pageData.items.forEach((char: Character) => {
            allCharsMap.set(char.filename, processCharData(char, char.filename, true));
          });
        }
      };

      paginatedQueries.forEach(processQuery);
      paginatedPersonasQueries.forEach(processQuery);

      if (bootstrapData?.public_characters) {
          Object.entries(bootstrapData.public_characters).forEach(([filename, charData]) => {
              if (!allCharsMap.has(filename) && !deletedPublicIds.has(`character:${filename}`)) {
                allCharsMap.set(filename, processCharData(charData as Character, filename, false));
              }
          });
      }

      return Object.fromEntries(allCharsMap);
    });
    
    const importableItems = computed(() => {
        const bootstrapData = queryClient.getQueryData<BootstrapResponse>([BOOTSTRAP_QUERY_KEY, settingsStore.userId]);
        const userConfig = settingsStore.userFullConfig;
        if (!bootstrapData?.public_characters || !userConfig?.deleted_public_items) {
            return [];
        }
        
        const deletedPublicIds = new Set(userConfig.deleted_public_items);

        return Object.entries(bootstrapData.public_characters)
            .filter(([filename]) => deletedPublicIds.has(`character:${filename}`))
            .map(([filename, charData]) => {
                const backendChar = charData as BackendCharacter;
                return {
                    ...backendChar,
                    filename,
                    is_private: true,
                    displayName: backendChar.displayName || backendChar.name,
                };
            });
    });

    const importableCharacters = computed(() => {
        return importableItems.value.filter(c => !c.is_user_persona);
    });

    const importablePersonas = computed(() => {
        return importableItems.value.filter(c => c.is_user_persona);
    });

    const activeCharacter = computed(() => {
        const activeKey = settingsStore.activeCharacterKey;
        return activeKey ? characters.value[activeKey] : null;
    });

    async function setActiveCharacter(filename: string) {
        const sessionStore = useSessionStore();
        if (settingsStore.activeCharacterKey === filename) return;
        await settingsStore.updateUserConfigValue('active_character', filename);
        await sessionStore.loadSessionsForCharacter(filename);
    }

    function createOrUpdateCharacter(nameForApi: string, charData: Omit<Character, 'filename'>, isEditing: boolean) {
        createOrUpdate({
            dataType: 'character',
            filename: nameForApi,
            data: charData,
            isEditing: isEditing,
        }, {
          onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['paginatedData', 'character'] });
            queryClient.invalidateQueries({ queryKey: ['paginatedData', 'persona'] });
          }
        });
    }

    async function generateCharacter(prompt: string, isPersona: boolean, selectedPresets?: Filename[], selectedWorlds?: Filename[]): Promise<Character | null> {
        if (!settingsStore.userId) {
            uiStore.setGlobalError("用户未登录，无法生成角色。");
            return null;
        }
        try {
            const apiCall = isPersona ? apiService.generateUserPersona : apiService.generateCharacter;
            const response = await apiCall(settingsStore.userId, prompt, selectedPresets, selectedWorlds);
            const generatedData = JSON.parse(response.data) as Omit<Character, 'filename'>;
            
            return {
                ...defaultCharacter,
                ...generatedData,
                filename: '',
                displayName: generatedData.name || '未命名',
            };
        } catch (error) {
            uiStore.setGlobalError(`AI生成失败: ${error}`);
            return null;
        }
    }
    
    function renameCharacter(oldFilename: Filename, newDisplayName: string) {
        rename({
            dataType: 'character',
            oldFilename: oldFilename,
            newDisplayName: newDisplayName,
        });
    }

    async function deleteCharacter(filename: string) {
        const charToDelete = characters.value[filename];
        if (!charToDelete) return;

        if (settingsStore.activeCharacterKey === filename) {
            await setActiveCharacter('Assistant');
        }
        if (settingsStore.activePersonaKey === filename) {
            await settingsStore.setActivePersona('User');
        }
        
        if (charToDelete.is_private) {
            deleteData({ dataType: 'character', filename: filename });
        } else {
            const userConfig = settingsStore.userFullConfig;
            if (userConfig) {
                const deletedItems = userConfig.deleted_public_items || [];
                const identifier = `character:${filename}`;
                if (!deletedItems.includes(identifier)) {
                    await settingsStore.updateUserConfigValue('deleted_public_items', [...deletedItems, identifier]);
                    invalidateAllData();
                }
            }
        }
    }
    
    async function importPublicCharacters(filenames: string[]) {
        if(!settingsStore.userFullConfig) return;
        
        const currentDeleted = settingsStore.userFullConfig.deleted_public_items || [];
        const newDeleted = currentDeleted.filter((id: string) => !filenames.some(fname => id === `character:${fname}`));

        await settingsStore.updateUserConfigValue('deleted_public_items', newDeleted);
        invalidateAllData();
    }
    
    async function uploadCharacterImage(charFilename: string, imageBlob: Blob): Promise<TaskSubmissionResponse> {
        if (!settingsStore.userId) throw new Error("用户未登录，无法上传图片。");
        
        const formData = new FormData();
        formData.append("file", imageBlob, "image.webp");
        
        try {
            const response = await apiService.uploadCharacterImage(settingsStore.userId, charFilename, formData);
            taskStore.addTask({ id: response.task_id, type: 'upload_character_image', status: 'processing' });
            return response;
        } catch (error) {
            uiStore.setGlobalError(`为 '${charFilename}' 提交图片上传任务失败: ${error}`);
            throw error;
        }
    }

    const defaultCharacter: Character = {
      filename: '',
      displayName: '',
      name: '',
      description: '',
      personality: '',
      first_mes: '',
      mes_example: '',
      is_private: true,
      is_user_persona: false,
    };

    return {
        characters,
        importableCharacters,
        importablePersonas,
        activeCharacter,
        setActiveCharacter,
        createOrUpdateCharacter,
        generateCharacter,
        renameCharacter,
        deleteCharacter,
        importPublicCharacters,
        uploadCharacterImage, 
    };
});