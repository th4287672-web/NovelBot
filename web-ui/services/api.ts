import type { AxiosInstance } from 'axios';
import type {
  AllDataResponse, UserConfig, Character, Preset, WorldInfo, Group, ChatMessage, Session, Filename,
  DisplayOrder, MemoryData, BackendPreset, ImportReport, DrawingConfig, GenerationRequest, Img2ImgRequest,
  ImageToPromptRequest, ImageToPromptResponse, TtsVoice, TtsSegment, TtsParams, StoryPackage, 
  BrowseResponse, SharePayload, ImportCommunityItemResponse, RegisterPayload, RegisterResponse, LoginPayload,
  LoginResponse, ForgotPasswordRequestPayload, ForgotPasswordQuestionsResponse, ResetPasswordPayload,
  AvatarUploadResponse, DeleteAccountPayload, GenerationProfile, OptionsProfile, UsernameUpdatePayload, UsernameUpdateResponse,
  MessageActionType, PaginatedData,
  BootstrapResponse, CheckModelsResponse, TokenUsageStatsResponse, TaskSubmissionResponse, TaskStatusResponse,
  GenerationProfiles, StoryPackageResponse, ApiKey
} from '~/types/api';

function getApiClient(): AxiosInstance {
    const nuxtApp = useNuxtApp();
    if (!nuxtApp.$api) {
        throw new Error("Axios 客户端 ($api) 尚未在 Nuxt 插件中正确注入。");
    }
    return nuxtApp.$api as AxiosInstance;
}

export const apiService = {
  // Authentication
  register(payload: RegisterPayload): Promise<RegisterResponse> { return getApiClient().post('/auth/register', payload); },
  login(payload: LoginPayload): Promise<LoginResponse> { return getApiClient().post('/auth/login', payload); },
  getSecurityQuestions(payload: ForgotPasswordRequestPayload): Promise<ForgotPasswordQuestionsResponse> { return getApiClient().post('/auth/forgot-password/questions', payload); },
  resetPassword(payload: ResetPasswordPayload): Promise<{ status: string; message: string }> { return getApiClient().post('/auth/forgot-password/reset', payload); },
  deleteAccount(payload: DeleteAccountPayload): Promise<{ status: string; message: string }> { return getApiClient().post('/auth/delete-account', payload); },
  
  // User Profile
  uploadAvatar(userId: string, formData: FormData): Promise<TaskSubmissionResponse> { return getApiClient().post(`/user/${userId}/avatar`, formData); },
  updateUsername(userId: string, payload: UsernameUpdatePayload): Promise<UsernameUpdateResponse> { return getApiClient().put(`/user/${userId}/username`, payload); },

  // Character Image
  uploadCharacterImage(userId: string, charFilename: string, formData: FormData): Promise<TaskSubmissionResponse> {
    return getApiClient().post(`/character/${userId}/${charFilename}/image`, formData);
  },

  // Bootstrap & Data
  bootstrap(userId: string): Promise<BootstrapResponse> {
    if (!userId) { return Promise.reject(new Error("User ID cannot be empty for bootstrap")); }
    return getApiClient().get(`/bootstrap/${userId}`);
  },
  
  getPaginatedData<T>(userId: string, dataType: string, page: number, limit: number, sortBy: string, search?: string): Promise<PaginatedData<T>> {
    const params = { page, limit, sort_by: sortBy, search };
    return getApiClient().get(`/data/${userId}/${dataType}`, { params });
  },

  // Config Management
  updateUserConfig(userId: string, configData: UserConfig): Promise<{ status: string; message: string }> { 
    console.log('[DIAG] apiService.updateUserConfig is sending:', configData);
    return getApiClient().post(`/user_config/${userId}`, configData);
  },
  updateDisplayOrder(userId: string, dataType: keyof DisplayOrder, order: Filename[]): Promise<{ status: string; message: string }> { return getApiClient().post(`/user_config/${userId}/display_order`, { dataType, order }); },
  updateGenerationProfiles(userId: string, profiles: Partial<GenerationProfiles>): Promise<{ status: string; message: string }> { return getApiClient().post(`/user_config/${userId}/generation_profiles`, profiles); },

  // CRUD
  createOrUpdateData(userId: string, dataType: 'character' | 'preset' | 'world_info' | 'group', filenameSuggestion: string, data: any, isEditing: boolean = false): Promise<{ success: boolean, filename: string, data: any, error?: string }> {
    const payload = { ...data, _is_editing: isEditing };
    return getApiClient().post(`/data/${userId}/${dataType}/${filenameSuggestion}`, payload);
  },
  renameData(userId: string, dataType: 'character' | 'preset' | 'world_info' | 'group', oldName: string, newName: string): Promise<{ status: string; message: string }> {
      return getApiClient().patch(`/data/${userId}/${dataType}/${oldName}`, { new_name: newName });
  },
  deleteData(userId: string, dataType: 'character' | 'preset' | 'world_info' | 'group', filename: string): Promise<{ status: string; message: string }> {
    return getApiClient().delete(`/data/${userId}/${dataType}/${filename}`);
  },

  // Session
  getSessionsForCharacter(userId: string, charFilename: string): Promise<Session[]> { return getApiClient().get(`/sessions/${userId}/${charFilename}`); },
  createNewSession(userId: string, charFilename: string): Promise<Session> { return getApiClient().post(`/session/${userId}/${charFilename}`); },
  getSessionHistory(userId: string, sessionId: string): Promise<Omit<ChatMessage, 'id'>[]> { return getApiClient().get(`/history/${userId}/${sessionId}`); },
  updateSessionHistory(userId: string, sessionId: string, history: Omit<ChatMessage, 'id'>[]): Promise<{ status: string; message: string }> { return getApiClient().put(`/history/${userId}/${sessionId}`, history); },
  deleteSession(userId: string, sessionId: string): Promise<{ status: string; message: string }> { return getApiClient().delete(`/session/${userId}/${sessionId}`); },
  renameSession(userId: string, sessionId: string, newTitle: string): Promise<{ status: string; message: string }> { return getApiClient().patch(`/session/${userId}/${sessionId}`, { title: newTitle }); },
  generateSessionTitle(userId: string, sessionId: string): Promise<{ status: string; title: string }> { return getApiClient().post(`/session/${userId}/${sessionId}/generate_title`); },

  // Memory & Semantic
  getMemories(userId: string, charFilename: string): Promise<MemoryData> { return getApiClient().get(`/memory/${userId}/${charFilename}`); },
  updateMemories(userId: string, charFilename: string, data: MemoryData): Promise<{ status: string; message: string }> { return getApiClient().put(`/memory/${userId}/${charFilename}`, data); },
  extractMemoryFromHistory(userId: string, history: ChatMessage[]): Promise<{ status: string; data: string[] }> { return getApiClient().post('/generation/extract_memory', { user_id: userId, history: history.map(m => ({ role: m.role, content: m.content })) }); },
  syncWorldBooks(userId: string, worlds: Omit<WorldInfo, 'filename' | 'is_private'>[]): Promise<{ status: string; message: string }> { return getApiClient().post(`/semantic-retrieval/sync-worlds`, { user_id: userId, worlds: worlds }); },

  // Generation
  generateCharacter(userId: string, prompt: string, selectedPresets?: Filename[], selectedWorlds?: Filename[]): Promise<{ status: string; data: string }> { return getApiClient().post('/generation/character', { user_id: userId, prompt, selected_presets: selectedPresets, selected_worlds: selectedWorlds }); },
  generateUserPersona(userId: string, prompt: string, selectedPresets?: Filename[], selectedWorlds?: Filename[]): Promise<{ status: string; data: string }> { return getApiClient().post('/generation/user_persona', { user_id: userId, prompt, selected_presets: selectedPresets, selected_worlds: selectedWorlds }); },
  generateWorldInfo(userId: string, prompt: string, selectedPresets?: Filename[], selectedWorlds?: Filename[]): Promise<{ status: string; data: string }> { return getApiClient().post('/generation/world_info', { user_id: userId, prompt, selected_presets: selectedPresets, selected_worlds: selectedWorlds }); },
  weaveStory(userId: string, prompt: string): Promise<StoryPackageResponse> { return getApiClient().post('/generation/weave_story', { user_id: userId, prompt }); },
  debugPresetPrompt(userConfig: UserConfig & { user_id: string }, userMessage: string): Promise<{ status: string; prompt: string }> { return getApiClient().post('/generation/debug-prompt', { userConfig, userMessage }); },

  // Data Import/Export
  exportData(userId: string): Promise<TaskSubmissionResponse> { return getApiClient().post(`/data/export/${userId}`); },
  importData(userId: string, formData: FormData): Promise<TaskSubmissionResponse> { return getApiClient().post(`/data/import/${userId}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }); },
  
  // AIGC
  getDrawingConfig(): Promise<DrawingConfig> { return getApiClient().get('/aigc/config'); },
  generateTxt2Img(params: GenerationRequest, userId: string): Promise<TaskSubmissionResponse> { return getApiClient().post('/aigc/txt2img', { ...params, user_id: userId }); },
  generateImg2Img(params: Img2ImgRequest, userId: string): Promise<TaskSubmissionResponse> { return getApiClient().post('/aigc/img2img', { ...params, user_id: userId }, { timeout: 300000 }); },
  getImagePrompt(params: ImageToPromptRequest): Promise<ImageToPromptResponse> { return getApiClient().post('/aigc/image-to-prompt', params); },
  
  // TTS
  getTtsVoices(): Promise<{ status: string; voices: TtsVoice[] }> { return getApiClient().get('/tts/voices'); },
  synthesizeTtsBatch(userId: string, segments: TtsSegment[], params: TtsParams): Promise<TaskSubmissionResponse> { return getApiClient().post('/tts/synthesize-batch', { user_id: userId, segments, params }); },
  
  // Tasks
  getTaskStatus(taskId: string): Promise<TaskStatusResponse> { return getApiClient().get(`/tasks/${taskId}`); },
  getAllTasksForUser(userId: string, limit: number = 50, offset: number = 0): Promise<TaskStatusResponse[]> { return getApiClient().get(`/tasks/user/${userId}`, { params: { limit, offset } }); },
  
  // System
  checkModels(userId: string, apiKeys?: ApiKey[]): Promise<CheckModelsResponse> { return getApiClient().post('/system/check_models', { user_id: userId, api_keys: apiKeys }); },
  getTokenUsageStats(userId: string): Promise<TokenUsageStatsResponse> { return getApiClient().get(`/system/token_usage_stats/${userId}`); },
  testApiKey(apiKey: string, proxyUrl?: string | null): Promise<{ status: string; message: string }> { return getApiClient().post('/system/test-api-key', { api_key: apiKey, proxy_url: proxyUrl }); },
  netCheck(proxyUrl?: string | null): Promise<{ status: string; message: string }> { return getApiClient().get('/system/net-check', { params: { proxy_url: proxyUrl } }); },
  
  // Community
  shareToCommunity(payload: SharePayload): Promise<{ status: string; message: string }> { return getApiClient().post('/community/share', payload); },
  browseCommunity(dataType: string, sortBy: string, page: number, limit: number): Promise<BrowseResponse> { return getApiClient().get('/community/browse', { params: { data_type: dataType, sort_by: sortBy, page, limit }}); },
  importFromCommunity(userId: string, itemId: number): Promise<ImportCommunityItemResponse> { return getApiClient().post(`/community/import/${itemId}`, { user_id: userId }); },
  
  // Streaming Fetch
  performMessageAction(userId: string, action: MessageActionType, history: Omit<ChatMessage, 'id'>[], target_message: Omit<ChatMessage, 'id' | 'isComplete'>): Promise<Response> {
      const config = useRuntimeConfig();
      return fetch(`${config.public.apiBase}/api/generation/message_action`, { 
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' }, 
          body: JSON.stringify({ 
              user_id: userId, 
              action, 
              history, 
              target_message
          }) 
      });
  }
};