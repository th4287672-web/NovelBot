<template>
  <CommonBaseModal :title="modalTitle" theme-color="cyan" @close="emit('close')" max-width="80rem">
    <div v-if="viewMode === 'form'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="space-y-4">
        <div class="text-right">
          <button @click="viewMode = 'ai'" class="text-sm text-cyan-400 hover:underline">切换到 AI 辅助生成</button>
        </div>
        <div>
          <label for="charDisplayName" class="archive-label">显示名称 (必填)</label>
          <input id="charDisplayName" v-model="localCharacter.displayName" type="text" class="archive-input focus:border-cyan-500" />
        </div>
        <div>
          <label for="charVoice" class="archive-label">角色声音</label>
          <select id="charVoice" v-model="localCharacter.voice" class="archive-input focus:border-cyan-500">
              <option :value="undefined">默认 (跟随全局设置)</option>
              <option v-if="ttsStore.isLoadingVoices" disabled>加载中...</option>
              <option v-for="voice in ttsStore.voices" :key="voice.ShortName" :value="voice.ShortName">
                  {{ voice.DisplayName }} ({{ voice.Gender }})
              </option>
          </select>
        </div>
        <div>
          <label for="charDesc" class="archive-label">角色描述</label>
          <textarea id="charDesc" v-model="localCharacter.description" rows="4" class="archive-textarea focus:border-cyan-500"></textarea>
        </div>
        <div>
          <label for="charPerson" class="archive-label">性格</label>
          <input id="charPerson" v-model="localCharacter.personality" type="text" class="archive-input focus:border-cyan-500" />
        </div>
        <div>
          <label for="charFirst" class="archive-label">开场白</label>
          <textarea id="charFirst" v-model="localCharacter.first_mes" rows="2" class="archive-textarea focus:border-cyan-500"></textarea>
        </div>
      </div>

      <div>
        <CommonImageUploaderWithCropper 
          v-model:image-url="localCharacter.image"
          :key="localCharacter.image || localCharacter.filename"
          cropper-title="裁剪角色封面图"
          :aspect-ratio="2/3"
          :upload-function="(blob: Blob) => uploadImageAndPoll(localCharacter.filename, blob)"
          :disabled="!localCharacter.is_private || !localCharacter.filename"
        />
      </div>
    </div>
    
    <div v-if="viewMode === 'ai'" class="space-y-4">
      <div class="text-right">
        <button @click="viewMode = 'form'" class="text-sm text-cyan-400 hover:underline">切换到手动填写</button>
      </div>
      <div>
        <label for="ai-prompt" class="archive-label">输入角色核心概念</label>
        <textarea id="ai-prompt" v-model="aiPrompt" rows="5" class="archive-textarea focus:border-cyan-500" placeholder="例如：一个来自赛博朋克都市、厌倦了纷争的退休侦探，只喜欢喂猫和喝威士忌。"></textarea>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="archive-label">选择预设作为规则 (可选)</label>
          <div class="max-h-32 overflow-y-auto space-y-1 p-2 border border-gray-600 rounded-md">
            <label v-for="preset in Object.values(presets) as Preset[]" :key="preset.filename" class="flex items-center text-sm p-1 rounded hover:bg-gray-700">
              <input type="checkbox" :value="preset.filename" v-model="selectedPresets" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-cyan-500 focus:ring-cyan-600">
              <span class="ml-2 text-gray-300 truncate">{{ preset.displayName }}</span>
            </label>
          </div>
        </div>
        <div>
          <label class="archive-label">选择世界书作为背景 (可选)</label>
          <div class="max-h-32 overflow-y-auto space-y-1 p-2 border border-gray-600 rounded-md">
            <label v-for="world in Object.values(worldInfo) as WorldInfo[]" :key="world.filename" class="flex items-center text-sm p-1 rounded hover:bg-gray-700">
              <input type="checkbox" :value="world.filename" v-model="selectedWorlds" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-cyan-500 focus:ring-cyan-600">
              <span class="ml-2 text-gray-300 truncate">{{ world.name }}</span>
            </label>
          </div>
        </div>
      </div>
    </div>

    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button v-if="viewMode === 'form'" @click="handleSave" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500">保存</button>
      <button v-if="viewMode === 'ai'" @click="handleAiGenerate" :disabled="isGenerating" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-500">
        {{ isGenerating ? '生成中...' : '开始生成' }}
      </button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, type PropType } from 'vue';
import type { Character, Filename, Preset, WorldInfo } from '~/types/api';
import { deepClone } from '~/utils/helpers';
import { useCharacterStore } from '~/stores/characterStore';
import { usePresetStore } from '~/stores/presetStore';
import { useWorldStore } from '~/stores/worldStore';
import { useTtsStore } from '~/stores/ttsStore';
import { useTaskStore } from '~/stores/taskStore';
import { storeToRefs } from 'pinia';
import CommonImageUploaderWithCropper from '~/components/common/ImageUploaderWithCropper.vue';

const props = defineProps({
  mode: { type: String as PropType<'create' | 'edit'>, required: true },
  character: { type: Object as PropType<Character | null>, default: null }
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', payload: { mode: 'create' | 'edit', data: Character }): void;
}>();

const characterStore = useCharacterStore();
const presetStore = usePresetStore();
const worldStore = useWorldStore();
const ttsStore = useTtsStore();
const taskStore = useTaskStore();

const { presets } = storeToRefs(presetStore);
const { worldInfo } = storeToRefs(worldStore);

const modalTitle = computed(() => props.mode === 'create' ? '创建新角色' : `编辑角色: ${props.character?.displayName}`);
const viewMode = ref<'form' | 'ai'>(props.mode === 'create' ? 'ai' : 'form');
const aiPrompt = ref('');
const isGenerating = ref(false);
const selectedPresets = ref<Filename[]>([]);
const selectedWorlds = ref<Filename[]>([]);

const defaultCharacter: Character = {
  filename: '', displayName: '', name: '', description: '', personality: '',
  first_mes: '', mes_example: '', is_private: true, is_user_persona: false,
  voice: undefined, image: null,
};

const localCharacter = ref<Character>(defaultCharacter);

onMounted(() => { ttsStore.fetchVoices(); });

watch(() => [props.mode, props.character], () => {
  if (props.mode === 'edit' && props.character) {
    localCharacter.value = deepClone(props.character);
  } else {
    localCharacter.value = deepClone(defaultCharacter);
    viewMode.value = 'ai';
  }
  selectedPresets.value = [];
  selectedWorlds.value = [];
}, { immediate: true });

function handleSave() {
  if (!localCharacter.value.displayName.trim()) { alert('角色显示名称不能为空！'); return; }
  if (!localCharacter.value.name.trim()) { localCharacter.value.name = localCharacter.value.displayName; }
  emit('save', { mode: props.mode, data: localCharacter.value });
}

function isGeneratedCharacterValid(data: any): data is Character {
    return data && typeof data.name === 'string' && data.name.trim() !== '' &&
           typeof data.description === 'string' && data.description.trim() !== '' &&
           typeof data.first_mes === 'string' && data.first_mes.trim() !== '';
}

async function uploadImageAndPoll(charFilename: string, imageBlob: Blob): Promise<string> {
    const taskSubmission = await characterStore.uploadCharacterImage(charFilename, imageBlob);
    const finalTask = await taskStore.pollTaskResult(taskSubmission.task_id);
    if (finalTask.status === 'success' && finalTask.result.image_url) {
        return finalTask.result.image_url;
    } else {
        throw new Error(finalTask.error?.error || "图片上传任务失败");
    }
}

async function handleAiGenerate() {
    if (!aiPrompt.value.trim()) { alert('请输入角色核心概念！'); return; }
    isGenerating.value = true;
    try {
        const generatedData = await characterStore.generateCharacter(aiPrompt.value, false, selectedPresets.value, selectedWorlds.value);
        if (isGeneratedCharacterValid(generatedData)) {
            localCharacter.value.displayName = generatedData.displayName || generatedData.name;
            localCharacter.value.name = generatedData.name;
            localCharacter.value.description = generatedData.description;
            localCharacter.value.personality = generatedData.personality;
            localCharacter.value.first_mes = generatedData.first_mes;
            localCharacter.value.mes_example = generatedData.mes_example;
            viewMode.value = 'form';
        } else {
            alert('AI生成的内容不完整或格式不正确，请调整提示词后重试，或切换到手动填写。');
        }
    } finally { isGenerating.value = false; }
}
</script>