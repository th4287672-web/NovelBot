import { useQuery, useQueryClient, type UseQueryReturnType } from '@tanstack/vue-query';
import { computed, ref, type Ref } from 'vue';
import { apiService } from '~/services/api';
import { useSettingsStore } from '~/stores/settings';
import type { AllDataResponse, Filename, Character, Preset, WorldInfo, Group, PaginatedData, BootstrapResponse } from '~/types/api';

export const BOOTSTRAP_QUERY_KEY = 'bootstrapData';

export function useBootstrapQuery(): UseQueryReturnType<BootstrapResponse, Error> {
  const settingsStore = useSettingsStore();
  
  return useQuery({
    queryKey: [BOOTSTRAP_QUERY_KEY, settingsStore.userId],
    queryFn: () => {
      // [代码注释] queryFn 是 Vue Query 获取数据的核心。
      // 它只在需要时（例如缓存失效或首次加载）被调用。
      console.log(`[DIAG][useBootstrapQuery] 正在为用户 ${settingsStore.userId} 执行实际的 API 数据获取...`);
      if (!settingsStore.userId || settingsStore.isAnonymous) {
        console.warn('[DIAG][useBootstrapQuery] 已拒绝：用户 ID 无效或为匿名用户。');
        // [代码注释] 对于匿名用户或未登录状态，我们返回一个符合类型的空结构，避免后续代码出错。
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
    // [核心优化] `enabled` 属性控制查询是否自动执行。只有当用户ID有效且在客户端时才执行。
    enabled: computed(() => {
      const isEnabled = !!settingsStore.userId && process.client;
      console.log(`[DIAG][useBootstrapQuery] 'enabled' 计算属性当前为: ${isEnabled}`);
      return isEnabled;
    }),
    // [核心优化] 设置合理的缓存时间，这是本次优化的关键。
    // staleTime: 5分钟。在这段时间内，数据被认为是“新鲜的”，不会触发新的网络请求。
    staleTime: 1000 * 60 * 5,
    // gcTime: 10分钟。如果一个查询在10分钟内没有任何活跃的观察者，它将被从缓存中移除。
    gcTime: 1000 * 60 * 10,
    // [核心优化] 禁用窗口聚焦时自动重新获取，以避免不必要的 API 调用。
    refetchOnWindowFocus: false,
  });
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
        // [代码注释] 对匿名用户返回空数据结构
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
    // [核心优化] 分页数据同样设置缓存时间
    staleTime: 1000 * 60 * 1, // 1分钟
    placeholderData: (previousData) => previousData,
  });

  return query;
}

export function useInvalidateAllData() {
    const queryClient = useQueryClient();
    return () => {
        // [代码注释] 这个函数用于在重大变更后，强制让所有缓存失效，并重新获取最新数据。
        queryClient.invalidateQueries({ queryKey: [BOOTSTRAP_QUERY_KEY] });
        queryClient.invalidateQueries({ queryKey: ['paginatedData'] });
    };
}