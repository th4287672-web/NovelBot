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
  
  // [核心优化] userId 和 userInfo 的管理逻辑简化
  const storedUserId = useStorage<string | null>('mynovelbot_user_id', null)
  const storedUserInfo = useStorage<UserInfo | null>('mynovelbot_user_info', null)
  
  const generationConfig = useStorage<GenerationConfig>('mynovelbot_generation_config', {
    model: 'models/gemini-1.5-pro-latest',
    temperature: 0.8,
    top_p: 0.9,
    top_k: 40,
    max_output_tokens: 4096,
  });

  const ANONYMOUS_USER_ID = 'anonymous-user'
  const userId = computed(() => storedUserId.value || ANONYMOUS_USER_ID)
  const isAnonymous = computed(() => userId.value === ANONYMOUS_USER_ID)

  // [核心优化] 将 useBootstrapQuery 作为 store 内部的单一数据源
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
  
  // [核心优化] isReady 和 isInitializing 直接派生自 query 的状态
  const isReady = computed(() => bootstrapQuery.isSuccess.value)
  const isInitializing = computed(() => bootstrapQuery.isLoading.value)

  // [核心优化] 所有配置项都从 bootstrapQuery 的 data 中派生
  const userConfig = computed(() => bootstrapQuery.data.value?.user_config || null)
  const userFullConfig = computed(() => bootstrapQuery.data.value?.user_config as UserConfig | null)
  
  const hasCompletedOnboarding = ref(false);
  
  type ModelStatus = 'unchecked' | 'checking' | 'connected' | 'failed'
  const modelStatus = ref<ModelStatus>('unchecked')
  const verifiedModels = ref<ModelDetails[]>([])

  // [核心优化] 监听 query 数据变化来更新内部状态
  watch(bootstrapQuery.data, (newData) => {
    if (newData) {
      // 保持 userInfo 的本地存储同步
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
      // [代码注释] userId 变化会触发 useBootstrapQuery 的 queryKey 变化，自动重新获取数据。
    }
  }

  function setUserInfo(info: UserInfo) {
    storedUserInfo.value = info;
  }
  
  function updateUserInfo(info: UserInfo) {
    setUserInfo(info);
    // [代码注释] 手动更新缓存中的 user_info，避免不必要的 bootstrap 重载
    queryClient.setQueryData<BootstrapResponse | undefined>(
      [BOOTSTRAP_QUERY_KEY, userId.value], 
      (old) => old ? { ...old, user_info: info } : undefined
    );
  }

  // [核心优化] 所有更新操作都通过一个统一的函数，返回一个 Promise
  async function updateUserConfigValue<K extends keyof UserConfig>(key: K, value: UserConfig[K]): Promise<void> {
    const currentConfig = userFullConfig.value;
    if (!userId.value || isAnonymous.value || !currentConfig) {
      throw new Error("用户配置数据尚未加载，无法更新。");
    }
    const newConfig: UserConfig = { ...currentConfig, [key]: value };
    await apiService.updateUserConfig(userId.value, newConfig);
    // [代码注释] 更新成功后，让 bootstrap query 失效，自动在后台重新获取最新配置。
    await queryClient.invalidateQueries({ queryKey: [BOOTSTRAP_QUERY_KEY, userId.value] });
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

  async function checkModels() {
    if (!userId.value || isAnonymous.value) return
    modelStatus.value = 'checking'
    try {
      const response = await apiService.checkModels(userId.value)
      verifiedModels.value = response.models
      modelStatus.value = 'connected'
      // [代码注释] 将检查结果更新到 bootstrap 缓存中，保持数据一致
      queryClient.setQueryData<BootstrapResponse | undefined>(
        [BOOTSTRAP_QUERY_KEY, userId.value],
        (old) => old ? { ...old, system_status: { ...old.system_status, model_is_ready: true, verified_models: response.models } } : undefined
      )
    } catch (error) {
      modelStatus.value = 'failed'
      verifiedModels.value = []
      queryClient.setQueryData<BootstrapResponse | undefined>(
        [BOOTSTRAP_QUERY_KEY, userId.value],
        (old) => old ? { ...old, system_status: { ...old.system_status, model_is_ready: false, verified_models: [] } } : undefined
      )
      throw error
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

  // [代码注释] 所有导出的 computed 属性都直接从 Vue Query 的缓存数据中派生，确保了单一数据源。
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