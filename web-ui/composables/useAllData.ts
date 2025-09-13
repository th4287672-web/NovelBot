import { useQuery, useQueryClient, type UseQueryReturnType, type UseQueryDefinedReturnType } from '@tanstack/vue-query';
import { computed, ref, type Ref, watch } from 'vue';
import { apiService } from '~/services/api';
import { useSettingsStore } from '~/stores/settings';
import type { AllDataResponse, Filename, Character, Preset, WorldInfo, Group, PaginatedData, BootstrapResponse } from '~/types/api';
import { useSessionStore } from '~/stores/sessionStore';

export const BOOTSTRAP_QUERY_KEY = 'bootstrapData';

export function useBootstrapQuery(): UseQueryReturnType<BootstrapResponse, Error> {
  const settingsStore = useSettingsStore();
  const sessionStore = useSessionStore();
  
  const query = useQuery({
    queryKey: [BOOTSTRAP_QUERY_KEY, settingsStore.userId],
    queryFn: (): Promise<BootstrapResponse> => {
      console.log(`[DIAG][useBootstrapQuery] 正在为用户 ${settingsStore.userId} 执行实际的 API 数据获取...`);
      if (!settingsStore.userId || settingsStore.isAnonymous) {
        console.warn('[DIAG][useBootstrapQuery] 已拒绝：用户 ID 无效或为匿名用户。');
        const anonymousResponse: BootstrapResponse = {
          user_config: {
            active_character: 'Assistant',
            active_session_id: null,
            user_persona: 'User',
            preset: '百变助手',
            active_modules: {},
            max_tokens: 4096,
            world_info: [],
            display_order: {},
            regex_rules: [],
            generation_profiles: {},
            deleted_public_items: [],
            tts_voice_assignments: { user: 'zh-CN-YunxiNeural', char: 'zh-CN-XiaoxiaoNeural', narrator: 'zh-CN-YunyangNeural' },
            tts_service_config: { service: 'microsoft', apiKey: '', region: '' },
            api_keys: [],
            llm_service_config: { provider: 'google_gemini' },
            has_completed_onboarding: true,
          },
          system_status: { model_is_ready: false, api_key_count: 0, verified_models: [] },
          initial_sessions: [],
          public_characters: {},
          public_presets: {},
          public_world_info: {},
          public_groups: {},
          user_info: undefined,
        };
        return Promise.resolve(anonymousResponse);
      }
      return apiService.bootstrap(settingsStore.userId);
    },
    enabled: computed(() => {
      const isEnabled = !!settingsStore.userId && process.client;
      console.log(`[DIAG][useBootstrapQuery] 'enabled' 计算属性当前为: ${isEnabled}`);
      return isEnabled;
    }),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
    refetchOnWindowFocus: false,
  });

  watch(
    () => query.isSuccess.value,
    (isSuccess, wasSuccess) => {
      if (isSuccess && !wasSuccess) {
        const data = query.data.value;
        console.log('[DIAG][useBootstrapQuery] watch(isSuccess) 回调触发。');
        if (data && data.user_config && data.user_config.active_character) {
          console.log(`[DIAG][useBootstrapQuery] 正在为角色 '${data.user_config.active_character}' 加载会话...`);
          sessionStore.loadSessionsForCharacter(data.user_config.active_character);
        }
      }
    },
    { immediate: true }
  );

  return query;
}

type DataType = 'character' | 'preset' | 'world_info' | 'group' | 'persona';

export function usePaginatedData<T extends { filename: Filename }>(
  dataType: DataType, 
  page: Ref<number>, 
  limit: Ref<number>,
  searchQuery: Ref<string>
) {
  const settingsStore = useSettingsStore();
  
  const queryKey = computed(() => ['paginatedData', dataType, settingsStore.userId, page.value, limit.value, searchQuery.value]);

  const query = useQuery({
    queryKey: queryKey,
    queryFn: async (): Promise<PaginatedData<T>> => {
      if (!settingsStore.userId || settingsStore.isAnonymous) {
        return { items: [], total_items: 0, total_pages: 1, current_page: page.value };
      }
      const data = await apiService.getPaginatedData(
        settingsStore.userId, 
        dataType, 
        page.value, 
        limit.value, 
        'name', 
        searchQuery.value
      );

      if (data === undefined) {
        return { items: [], total_items: 0, total_pages: 1, current_page: page.value };
      }

      data.items = data.items.map((item: any) => ({
        ...item,
        filename: item.filename || item.name,
        displayName: item.displayName || item.name,
      }));
      return data as PaginatedData<T>;
    },
    enabled: computed(() => !!settingsStore.userId && process.client),
    staleTime: 1000 * 60 * 1,
    placeholderData: (previousData) => previousData,
  });

  return query;
}

export function useInvalidateAllData() {
    const queryClient = useQueryClient();
    return () => {
        queryClient.invalidateQueries({ queryKey: [BOOTSTRAP_QUERY_KEY] });
        queryClient.invalidateQueries({ queryKey: ['paginatedData'] });
    };
}