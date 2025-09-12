export type UserID = string;
export type Filename = string;
export type SessionID = string;
export type PresetName = string;
export type MessageRole = 'user' | 'model';

export type TargetLength = 'very_short' | 'short' | 'medium' | 'long' | 'very_long';

export interface GenerationProfile {
  target_length: TargetLength;
  custom_max_tokens?: number;
  prompt?: string;
}

export interface OptionsProfile extends GenerationProfile {
  count: number;
}

export type GenerationProfiles = {
  [key: string]: GenerationProfile | OptionsProfile;
};

export interface GenerationConfig {
    model: Filename;
    temperature: number;
    top_p: number;
    top_k: number;
    max_output_tokens: number;
}

export interface ModelDetails {
    name: Filename;
    display_name: string;
    description: string;
    input_token_limit: number;
    output_token_limit: number;
    supported_generation_methods: string[];
}

export interface Character {
  filename: Filename;
  name: string;
  displayName: string;
  description: string;
  personality?: string;
  first_mes: string;
  mes_example?: string;
  linked_worlds?: Filename[];
  is_private: boolean;
  is_user_persona: boolean;
  voice?: string;
  image?: string | null;
  owner_id?: string | null;
}

export interface Group {
  filename: Filename;
  name: string;
  description: string;
  character_filenames: Filename[];
  first_mes: string;
  is_private: boolean;
}

export interface PresetModule {
  identifier: string;
  name: string;
  system_prompt: boolean;
  enabled?: boolean;
  marker?: boolean;
  role: 'system' | 'user' | 'assistant';
  content: string;
  injection_position: number;
  injection_depth: number;
  forbid_overrides: boolean;
  injection_order?: number;
  is_thought_module?: boolean;
  thinking_budget?: number;
}

export interface Preset {
  filename: Filename;
  name: PresetName;
  displayName: string;
  prompts?: PresetModule[];
  is_private: boolean;
  [key: string]: any;
}

export interface WorldInfoEntry {
  uid: string;
  name?: string;
  keywords: string[];
  content: string;
}

export interface WorldInfo {
  filename: Filename;
  name: string;
  entries: WorldInfoEntry[];
  is_private: boolean;
}

export interface MemoryData {
  entries: string[];
}

export interface Session {
  id: SessionID;
  title: string;
  created: number;
  last_updated: number;
}

export interface TokenUsage {
  prompt_token_count: number;
  candidates_token_count: number;
  total_token_count: number;
}

export interface AIGCTask {
  taskId: string;
  status: 'processing' | 'success' | 'failed';
  imageUrl?: string;
}

export interface ChatMessage {
  id: number;
  role: MessageRole;
  content: string;
  isStreaming?: boolean;
  isComplete: boolean;
  isError?: boolean;
  errorContent?: string;
  alternatives?: string[];
  activeAlternative?: number;
  tokenUsage?: TokenUsage;
  aigcTask?: AIGCTask;
}

export interface RegexRule {
  id: string;
  name: string;
  pattern: string;
  template: string;
  enabled: boolean;
}

export interface DisplayOrder {
  characters?: Filename[];
  personas?: Filename[];
  presets?: Filename[];
  worlds?: Filename[];
  groups?: Filename[];
}

export interface TtsVoiceAssignments {
    user: string;
    char: string;
    narrator: string;
}

export interface TtsParams {
    rate: number;
    volume: number;
    pitch: number;
}

export type TtsServiceProvider = 'microsoft' | 'edge' | 'chat_tts' | 'huggingface' | 'coqui' | 'aihorde';

export interface TtsServiceConfig {
    service: TtsServiceProvider;
    apiKey: string;
    region: string;
    chatTtsApiUrl?: string;
    huggingfaceApiKey?: string;
    qwenTtsModelId?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key: string;
  provider: 'google';
}

export interface LLMServiceConfig {
    provider: 'google_gemini' | 'koboldai_horde';
    api_key?: string;
    horde_models?: string[];
    proxy?: string;
}

export interface UserConfig {
  active_character: Filename;
  active_session_id: SessionID | null;
  user_persona: Filename;
  preset: PresetName;
  active_modules: {
    [presetName in PresetName]: string[];
  };
  max_tokens: number;
  world_info: Filename[];
  display_order: DisplayOrder;
  regex_rules: RegexRule[];
  generation_profiles: GenerationProfiles;
  generation_config?: GenerationConfig;
  deleted_public_items: string[];
  tts_voice_assignments: TtsVoiceAssignments;
  tts_service_config: TtsServiceConfig;
  api_keys: ApiKey[]; 
  llm_service_config: LLMServiceConfig; 
  has_completed_onboarding?: boolean;
}

export interface SystemStatus {
  model_is_ready: boolean;
  api_key_count: number;
  verified_models: ModelDetails[];
}

export interface ImportReport {
  characters: { imported: number; skipped: number };
  presets: { imported: number; skipped: number };
  world_info: { imported: number; skipped: number };
  groups: { imported: number; skipped: number };
}

export interface DrawingConfig {
    service_name: string;
    description: string;
    api_key_url: string | null;
    docs_url: string;
    available_models: string[];
}

export interface GenerationRequest {
    prompt: string;
    negative_prompt?: string;
    width?: number;
    height?: number;
    steps?: number;
    cfg_scale?: number;
    seed?: number;
    model?: string | null;
}

export interface Img2ImgRequest extends GenerationRequest {
    imageBase64: string;
    denoising_strength: number;
}

export interface ImageToPromptRequest {
    imageBase64: string;
    strategy: 'gemini' | 'deepdanbooru';
}

export interface ImageToPromptResponse {
    status: string;
    prompt: string;
}

export interface StoryPackage {
    main_character: Character;
    npcs: Character[];
    world_info: WorldInfo;
    group: Group;
}

export interface StoryPackageResponse {
    status: string;
    data: StoryPackage;
}

export interface TtsVoice {
  Name?: string;
  DisplayName: string;
  LocalName?: string;
  ShortName: string;
  Gender: 'Male' | 'Female' | 'Unknown';
  Locale?: string;
  StyleList?: string[];
  VoiceType?: 'Neural';
  Provider: 'Microsoft' | 'Edge' | 'ChatTTS' | 'HuggingFace' | 'Coqui' | 'AIHorde';
}

export type TtsSegment = [string, string];

export interface CommunityItem {
  id: number;
  name: string;
  description: string;
  tags: string[];
  downloads: number;
  rating: number;
  user_id: string;
  created_at: string;
}

export interface SharePayload {
    user_id: string;
    data_type: CommunityItemType;
    filename: string;
    description: string;
    tags: string[];
}

export interface BrowseResponse {
    status: string;
    items: CommunityItem[];
    total: number;
    page: number;
    limit: number;
}

export interface ImportCommunityItemResponse {
    status: string;
    message: string;
    filename: string;
}
export type CommunityItemType = 'character' | 'preset' | 'world_info';

export interface UserInfo {
  user_id: string;
  username: string;
  account_number: string;
  avatar?: string | null;
  owner_id?: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  account_digits: number;
  security_questions: { question: string, answer: string }[];
  anonymous_user_id: string;
}

export interface RegisterResponse {
  status: string;
  message: string;
  user_info: UserInfo;
}

export interface LoginPayload {
    username_or_account: string;
    password: string;
}

export interface LoginResponse {
    status: string;
    message: string;
    user_info: UserInfo;
}

export interface ForgotPasswordRequestPayload {
    account_number: string;
}

export interface ForgotPasswordQuestionsResponse {
    status: string;
    questions: string[];
}

export interface ResetPasswordPayload {
    account_number: string;
    answers: string[];
    new_password: string;
}

export interface AvatarUploadResponse {
    status: string;
    avatar_url: string;
}

export interface UsernameUpdatePayload {
    new_username: string;
    password: string;
}

export interface UsernameUpdateResponse {
    status: string;
    message: string;
    new_username: string;
}

export interface DeleteAccountPayload {
    user_id: string;
    password: string;
}

export interface PaginatedData<T> {
  items: T[];
  total_items: number;
  total_pages: number;
  current_page: number;
}


export type BackendCharacter = Omit<Character, 'filename'>;
export type BackendWorldInfo = Omit<WorldInfo, 'filename'>;
export type BackendPreset = Omit<Preset, 'filename'>;
export type BackendGroup = Omit<Group, 'filename'>;

export interface AllDataResponse {
  user_config: UserConfig;
  characters: Record<Filename, BackendCharacter>;
  presets: Record<Filename, BackendPreset>;
  world_info: Record<Filename, BackendWorldInfo>;
  groups: Record<Filename, BackendGroup>;
  public_characters: Record<Filename, BackendCharacter>;
  public_presets: Record<Filename, BackendPreset>;
  public_world_info: Record<Filename, BackendWorldInfo>;
  public_groups: Record<Filename, BackendGroup>;
  status: SystemStatus;
}

export interface BootstrapResponse {
  user_config: UserConfig;
  system_status: SystemStatus;
  initial_sessions: Session[];
  public_characters: Record<Filename, BackendCharacter>;
  public_presets: Record<Filename, BackendPreset>;
  public_world_info: Record<Filename, BackendWorldInfo>;
  public_groups: Record<Filename, BackendGroup>;
  user_info?: UserInfo;
}

export interface CheckModelsResponse {
  status: 'success' | 'failed';
  models: ModelDetails[];
  error: string | null;
}

export interface TokenUsageStatsResponse {
  hourly: number;
  daily: number;
  monthly: number;
}

export interface TaskStatusResponse {
    id: string;
    user_id: string;
    task_type: string;
    status: 'pending' | 'processing' | 'success' | 'failed';
    progress: number;
    status_text: string | null;
    created_at: number;
    updated_at: number;
    start_time: number | null;
    end_time: number | null;
    result: any;
    error: any;
}

export type TaskSubmissionResponse = { status: 'processing', task_id: string };

export type MessageActionType = 'rewrite' | 'continue' | 'regenerate' | 'regenerate_options' | 'complete';