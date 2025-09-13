import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import type { 
  UserConfig, SystemStatus, Filename, RegexRule, 
  TtsVoiceAssignments, ApiKey, LLMServiceConfig, 
  TtsServiceConfig, UserInfo, BootstrapResponse, 
  TokenUsageStatsResponse, GenerationConfig, GenerationProfiles, ModelDetails, TaskSubmissionResponse
} from '~/types/api'
import { apiService } from '~/services/api'
import { useUIStore } from './ui'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { BOOTSTRAP_QUERY_KEY, useBootstrapQuery } from '~/composables/useAllData'
import { useStorage } from '@vueuse/core'
import { v4 as uuidv4 } from 'uuid'
import { deepClone } from '~/utils/helpers'
import { useTaskStore } from './taskStore'

export const defaultRules: RegexRule[] = [
  { id: uuidv4(), name: '折叠思维链', pattern: '<think_internal>([\\s\\S]*?)<\\/think_internal>', template: '<Foldable title="思维链">$1</Foldable>', enabled: true },
  { id: uuidv4(), name: '渲染剧情选项', pattern: '\\[选项(\\d+)\\]([^\\[]+)\\[\\/选项\\1\\]', template: '<StoryOption>$2</StoryOption>', enabled: true },
  { id: uuidv4(), name: '加粗 **文本**', pattern: '\\*\\*([\\s\\S]+?)\\*\\*', template: '<strong>$1</strong>', enabled: true },
  { id: uuidv4(), name: '斜体 *文本*', pattern: '\\*([\\s\\S]+?)\\*', template: '<em>$1</em>', enabled: true },
  { id: uuidv4(), name: '高亮 ==文本==', pattern: '==([\\s\\S]+?)==', template: '<Highlight color="#fef08a" textColor="#5a522c">$1</Highlight>', enabled: true },
  { id: uuidv4(), name: '剧透 ||文本||', pattern: '\\|\\|([\\s\\S]+?)\\|\\|', template: '<Spoiler>$1</Spoiler>', enabled: true },
  { id: uuidv4(), name: '渲染表格 (JSON)', pattern: '<Table>([\\s\\S]*?)<\\/Table>', template: '<Table>$1</Table>', enabled: true },
  { id: uuidv4(), name: '渲染表格 (快捷JSON)', pattern: '\\|\\|\\|table([\\s\\S]*?)\\|\\|\\|', template: '<Table><!-- $1 --></Table>', enabled: true },
  { id: uuidv4(), name: '渲染ECharts图表 (JSON)', pattern: '<ECharts>([\\s\\S]*?)<\\/ECharts>', template: '<ECharts>$1</ECharts>', enabled: true },
  { id: uuidv4(), name: '渲染平面图 (JSON)', pattern: '<FloorPlan>([\\s\\S]*?)<\\/FloorPlan>', template: '<FloorPlan>$1</FloorPlan>', enabled: true },
  { id: uuidv4(), name: '渲染进度条', pattern: '<progress value="(\\d+)" max="(\\d+)"(?: label="([^"]+)")?><\\/progress>', template: '<ProgressBar value="$1" max="$2" label="$3"></ProgressBar>', enabled: true },
  { id: uuidv4(), name: '渲染地图 (Base64)', pattern: "<map lat=\"([\\d.-]+)\" lng=\"([\\d.-]+)\"(?: markers-base64=['\"]([^'\"]+)['\"])?>[\\s\\S]*?<\\/map>", template: '<Map lat="$1" lng="$2" markers="$3"></Map>', enabled: true },
  { id: uuidv4(), name: '信息卡片', pattern: '<card title="([^"]+)">([\\s\\S]*?)<\\/card>', template: '<Card title="$1">$2</Card>', enabled: true },
  { id: uuidv4(), name: '骰子结果', pattern: '\\[骰子: (\\S+) = (\\d+)\\]', template: '<DiceRoll expression="$1" result="$2"></DiceRoll>', enabled: true }
]

export const useSettingsStore = defineStore('settings', () => {
  const queryClient = useQueryClient()
  const uiStore = useUIStore()
  
  const storedUserId = useStorage<string | null>('mynovelbot_user_id', null)
  const storedUserInfo = useStorage<UserInfo | null>('mynovelbot_user_info', null)
  
  const generationConfig = useStorage<GenerationConfig>('mynovelbot_generation_config', {
    model: 'models/gemini-1.5-pro-latest',
    temperature: 0.8,
    top_p: 0.9,
    top_k: 40,
    max_output_tokens: 4096,
  });
  
  let resolveHydration: () => void;
  const hydrationPromise = new Promise<void>(resolve => {
    resolveHydration = resolve;
  });

  const ANONYMOUS_USER_ID = 'anonymous-user'
  const userId = computed(() => storedUserId.value || ANONYMOUS_USER_ID)
  const isAnonymous = computed(() => userId.value === ANONYMOUS_USER_ID)

  const bootstrapQuery = useBootstrapQuery();

  const tokenUsageQuery = useQuery({
    queryKey: ['tokenUsage', userId],
    queryFn: () => {
        if (!userId.value || isAnonymous.value) return { hourly: 0, daily: 0, monthly: 0 };
        return apiService.getTokenUsageStats(userId.value);
    },
    enabled: computed(() => process.client && !!userId.value && !isAnonymous.value),
    staleTime: 1000 * 60 * 5,
  })
  
  const isReady = computed(() => bootstrapQuery.isSuccess.value)
  const isInitializing = computed(() => bootstrapQuery.isLoading.value)

  const userConfig = computed(() => bootstrapQuery.data.value?.user_config || null)
  const userFullConfig = computed(() => bootstrapQuery.data.value?.user_config as UserConfig | null)
  
  const hasCompletedOnboarding = ref(false);
  
  type ModelStatus = 'unchecked' | 'checking' | 'connected' | 'failed'
  const modelStatus = ref<ModelStatus>('unchecked')
  const verifiedModels = ref<ModelDetails[]>([])

  watch(bootstrapQuery.data, (newData) => {
    if (newData) {
      if (newData.user_info) {
        storedUserInfo.value = newData.user_info
      } else if (isAnonymous.value) {
        storedUserInfo.value = null;
      }
      
      hasCompletedOnboarding.value = newData.user_config?.has_completed_onboarding || false;

      if (newData.system_status) {
        verifiedModels.value = newData.system_status.verified_models || []
        modelStatus.value = newData.system_status.model_is_ready ? 'connected' : 'unchecked'
      }
      
      resolveHydration();
    }
  }, { deep: true, immediate: true })

  async function updateGenerationConfig(config: GenerationConfig) {
    generationConfig.value = config;
  }

  function setUserId(newUserId: string) {
    if (storedUserId.value !== newUserId) {
      storedUserId.value = newUserId
      if (newUserId === ANONYMOUS_USER_ID) {
        storedUserInfo.value = null
        hasCompletedOnboarding.value = false;
      }
    }
  }

  function setUserInfo(info: UserInfo) {
    storedUserInfo.value = info;
  }
  
  function updateUserInfo(info: UserInfo) {
    setUserInfo(info);
    queryClient.setQueryData<BootstrapResponse | undefined>(
      [BOOTSTRAP_QUERY_KEY, userId.value], 
      (old) => old ? { ...old, user_info: info } : undefined
    );
  }

  async function updateMultipleUserConfigValues(updates: Partial<UserConfig>): Promise<void> {
    const currentConfig = userFullConfig.value;
    if (!userId.value || isAnonymous.value || !currentConfig) {
      throw new Error("用户配置数据尚未加载，无法更新。");
    }
    const newConfig: UserConfig = { ...currentConfig, ...updates };
    await apiService.updateUserConfig(userId.value, newConfig);
    await queryClient.invalidateQueries({ queryKey: [BOOTSTRAP_QUERY_KEY, userId.value] });
  }

  async function updateUserConfigValue<K extends keyof UserConfig>(key: K, value: UserConfig[K]): Promise<void> {
    await updateMultipleUserConfigValues({ [key]: value });
  }
  
  async function updateLLMServiceConfig(config: LLMServiceConfig) {
      await updateUserConfigValue('llm_service_config', config);
  }

  async function updateUserApiKeys(keys: ApiKey[]) {
      await updateUserConfigValue('api_keys', keys);
  }
  
  async function uploadAvatar(avatarBlob: Blob): Promise<TaskSubmissionResponse> {
    const taskStore = useTaskStore()
    if (!userId.value || isAnonymous.value) throw new Error("匿名用户无法上传头像")
    const formData = new FormData()
    formData.append("file", avatarBlob, "avatar.webp")
    try {
      const response = await apiService.uploadAvatar(userId.value, formData)
      taskStore.addTask({ id: response.task_id, type: 'upload_avatar', status: 'processing' })
      return response;
    } catch (error) {
      console.error('头像上传失败:', error)
      throw error
    }
  }
  
  async function updateUsername(newUsername: string, password: string): Promise<UserInfo | null> {
    if (!userId.value || isAnonymous.value) throw new Error("匿名用户无法修改用户名")
    await apiService.updateUsername(userId.value, { new_username: newUsername, password })
    await queryClient.invalidateQueries({ queryKey: [BOOTSTRAP_QUERY_KEY, userId.value] })
    return storedUserInfo.value
  }

  async function deleteAccount(password: string) {
    if (!userId.value || isAnonymous.value) throw new Error("匿名用户无法注销账号")
    await apiService.deleteAccount({ user_id: userId.value, password })
    setUserId(ANONYMOUS_USER_ID)
  }

  async function checkModels(keys?: ApiKey[]) {
    if (!userId.value || isAnonymous.value) return;
    modelStatus.value = 'checking';
    try {
      const payload = { user_id: userId.value, api_keys: keys };
      const response = await apiService.checkModels(payload.user_id, payload.api_keys);
      verifiedModels.value = response.models;
      modelStatus.value = 'connected';
      queryClient.setQueryData<BootstrapResponse | undefined>(
        [BOOTSTRAP_QUERY_KEY, userId.value],
        (old) => old ? { ...old, system_status: { ...old.system_status, model_is_ready: true, verified_models: response.models } } : undefined
      );
    } catch (error) {
      modelStatus.value = 'failed';
      verifiedModels.value = [];
      queryClient.setQueryData<BootstrapResponse | undefined>(
        [BOOTSTRAP_QUERY_KEY, userId.value],
        (old) => old ? { ...old, system_status: { ...old.system_status, model_is_ready: false, verified_models: [] } } : undefined
      );
      throw error;
    }
  }

  async function importDefaultRulesByIds(ids: string[]) {
    const currentRules = deepClone(userFullConfig.value?.regex_rules || []);
    const rulesToImport = defaultRules.filter(rule => ids.includes(rule.id))
    const combinedRules = [...currentRules, ...rulesToImport]
      .filter((rule, index, self) => 
        index === self.findIndex(r => r.name === rule.name)
      )
    await updateUserConfigValue('regex_rules', combinedRules)
  }

  function logout() {
    setUserId(ANONYMOUS_USER_ID);
    uiStore.setGlobalError("您已退出登录。");
  }

  async function setActivePersona(filename: Filename) {
      await updateUserConfigValue('user_persona', filename);
  }

  async function setActivePreset(filename: Filename) {
      await updateUserConfigValue('preset', filename);
  }
  
  async function updateRegexRules(rules: RegexRule[]) {
      await updateUserConfigValue('regex_rules', rules);
  }

  async function completeOnboarding() {
      if (hasCompletedOnboarding.value) return;
      try {
          await updateUserConfigValue('has_completed_onboarding', true);
          hasCompletedOnboarding.value = true;
      } catch(e) {
          console.error("Failed to persist onboarding status:", e);
          uiStore.setGlobalError("无法保存设置，请稍后重试。");
      }
  }

  return {
    userId,
    userInfo: computed(() => storedUserInfo.value),
    isAnonymous,
    isReady,
    isInitializing,
    userConfig,
    userFullConfig,
    hasCompletedOnboarding,
    modelStatus,
    verifiedModels,
    generationConfig,
    hydrationPromise,
    setUserId,
    setUserInfo,
    updateUserInfo,
    updateUserConfigValue,
    updateMultipleUserConfigValues,
    updateLLMServiceConfig,
    updateUserApiKeys,
    updateGenerationConfig,
    uploadAvatar,
    updateUsername,
    deleteAccount,
    checkModels,
    importDefaultRulesByIds,
    logout,
    setActivePersona,
    setActivePreset,
    updateRegexRules,
    completeOnboarding,
    activeCharacterKey: computed(() => userConfig.value?.active_character || null),
    activePersonaKey: computed(() => userConfig.value?.user_persona || null),
    activePresetName: computed(() => userConfig.value?.preset || null),
    sessionActiveWorlds: computed(() => userConfig.value?.world_info || []),
    regexRules: computed(() => userFullConfig.value?.regex_rules || defaultRules),
    ttsVoiceAssignments: computed<TtsVoiceAssignments>(() => userConfig.value?.tts_voice_assignments || { user: 'zh-CN-YunxiNeural', char: 'zh-CN-XiaoxiaoNeural', narrator: 'zh-CN-YunyangNeural' }),
    llmServiceConfig: computed<LLMServiceConfig>(() => userConfig.value?.llm_service_config || { provider: 'google_gemini' }),
    userApiKeys: computed<ApiKey[]>(() => userConfig.value?.api_keys || []),
    ttsServiceConfig: computed<TtsServiceConfig>(() => userConfig.value?.tts_service_config || { service: 'microsoft', apiKey: '', region: '' }),
    tokenUsageStats: computed(() => tokenUsageQuery.data.value),
    importableRegexRules: computed(() => {
        const currentRuleNames = new Set((userFullConfig.value?.regex_rules || []).map(r => r.name));
        return defaultRules.filter(r => !currentRuleNames.has(r.name));
    }),
  }
})