<template>
  <CommonBaseModal :title="modalTitle" theme-color="purple" @close="emit('close')" max-width="80rem">
    <div v-if="viewMode === 'form'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="space-y-4">
        <div class="text-right">
          <button @click="viewMode = 'ai'" class="text-sm text-purple-400 hover:underline">切换到 AI 辅助生成</button>
        </div>
        <div>
          <label for="personaDisplayName" class="archive-label">人设名称 (必填)</label>
          <input id="personaDisplayName" v-model="localPersona.displayName" type="text" class="archive-input focus:border-purple-500" />
        </div>
        <div>
          <label for="personaDesc" class="archive-label">人设描述</label>
          <textarea id="personaDesc" v-model="localPersona.description" rows="6" class="archive-textarea focus:border-purple-500"></textarea>
        </div>
      </div>
      
      <div>
        <CommonImageUploaderWithCropper 
          v-model:image-url="localPersona.image"
          cropper-title="裁剪人设封面图"
          :aspect-ratio="1"
          :upload-function="handleImageUpload"
          :disabled="!localPersona.is_private || !localPersona.filename"
        />
      </div>
    </div>
    
    <div v-if="viewMode === 'ai'" class="space-y-4">
      <div class="text-right">
        <button @click="viewMode = 'form'" class="text-sm text-purple-400 hover:underline">切换到手动填写</button>
      </div>
      <div>
        <label for="ai-prompt-persona" class="archive-label">输入你的人设核心概念</label>
        <textarea id="ai-prompt-persona" v-model="aiPrompt" rows="5" class="archive-textarea focus:border-purple-500" placeholder="例如：一位知识渊博、言辞犀利的历史学教授，喜欢引用古籍。"></textarea>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="archive-label">选择预设作为规则 (可选)</label>
          <div class="max-h-32 overflow-y-auto space-y-1 p-2 border border-gray-600 rounded-md">
            <label v-for="preset in Object.values(presets) as Preset[]" :key="preset.filename" class="flex items-center text-sm p-1 rounded hover:bg-gray-700">
              <input type="checkbox" :value="preset.filename" v-model="selectedPresets" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-purple-500 focus:ring-purple-600">
              <span class="ml-2 text-gray-300 truncate">{{ preset.displayName }}</span>
            </label>
          </div>
        </div>
        <div>
          <label class="archive-label">选择世界书作为背景 (可选)</label>
          <div class="max-h-32 overflow-y-auto space-y-1 p-2 border border-gray-600 rounded-md">
            <label v-for="world in Object.values(worldInfo) as WorldInfo[]" :key="world.filename" class="flex items-center text-sm p-1 rounded hover:bg-gray-700">
              <input type="checkbox" :value="world.filename" v-model="selectedWorlds" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-purple-500 focus:ring-purple-600">
              <span class="ml-2 text-gray-300 truncate">{{ world.name }}</span>
            </label>
          </div>
        </div>
      </div>
    </div>

    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button v-if="viewMode === 'form'" @click="handleSave" class="btn btn-primary bg-purple-600 hover:bg-purple-500">保存</button>
      <button v-if="viewMode === 'ai'" @click="handleAiGenerate" :disabled="isGenerating" class="btn btn-primary bg-purple-600 hover:bg-purple-500 disabled:bg-gray-500">
        {{ isGenerating ? '生成中...' : '开始生成' }}
      </button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, watch, computed, type PropType } from 'vue';
import type { Character, Filename, Preset, WorldInfo } from '~/types/api';
import { deepClone } from '~/utils/helpers';
import { useCharacterStore } from '~/stores/characterStore';
import { usePresetStore } from '~/stores/presetStore';
import { useWorldStore } from '~/stores/worldStore';
import { useTaskStore } from '~/stores/taskStore';
import { storeToRefs } from 'pinia';
import CommonImageUploaderWithCropper from '~/components/common/ImageUploaderWithCropper.vue';

const props = defineProps({
  mode: { type: String as PropType<'create' | 'edit'>, required: true },
  persona: { type: Object as PropType<Character | null>, default: null }
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', payload: { mode: 'create' | 'edit', data: Character }): void;
}>();

const characterStore = useCharacterStore();
const presetStore = usePresetStore();
const worldStore = useWorldStore();
const taskStore = useTaskStore();

const { presets } = storeToRefs(presetStore);
const { worldInfo } = storeToRefs(worldStore);

const modalTitle = computed(() => props.mode === 'create' ? '创建新人设' : `编辑人设: ${props.persona?.displayName}`);
const viewMode = ref<'form' | 'ai'>(props.mode === 'create' ? 'ai' : 'form');
const aiPrompt = ref('');
const isGenerating = ref(false);
const selectedPresets = ref<Filename[]>([]);
const selectedWorlds = ref<Filename[]>([]);

const defaultPersona: Partial<Character> = {
  displayName: '', description: '', first_mes: '', is_private: true,
  is_user_persona: true, image: null, filename: ''
};

const localPersona = ref<Partial<Character>>({});

watch(() => [props.mode, props.persona], () => {
  if (props.mode === 'edit' && props.persona) {
    localPersona.value = deepClone(props.persona);
    viewMode.value = 'form';
  } else {
    localPersona.value = deepClone(defaultPersona);
    viewMode.value = 'ai';
  }
  selectedPresets.value = [];
  selectedWorlds.value = [];
}, { immediate: true });

function handleSave() {
  if (!localPersona.value.displayName?.trim()) { alert('人设名称不能为空！'); return; }
  if (!localPersona.value.name) { localPersona.value.name = localPersona.value.displayName; }
  emit('save', { mode: props.mode, data: localPersona.value as Character });
}

function isGeneratedPersonaValid(data: any): data is Character {
    return data && typeof data.name === 'string' && data.name.trim() !== '' &&
           typeof data.description === 'string' && data.description.trim() !== '';
}

async function handleAiGenerate() {
    if (!aiPrompt.value.trim()) { alert('请输入人设核心概念！'); return; }
    isGenerating.value = true;
    try {
        const generatedData = await characterStore.generateCharacter(aiPrompt.value, true, selectedPresets.value, selectedWorlds.value);
        if (isGeneratedPersonaValid(generatedData)) {
            localPersona.value.displayName = generatedData.displayName || generatedData.name;
            localPersona.value.name = generatedData.name;
            localPersona.value.description = generatedData.description;
            viewMode.value = 'form';
        } else {
            alert('AI生成的内容不完整或格式不正确，请调整提示词后重试，或切换到手动填写。');
        }
    } finally { isGenerating.value = false; }
}

async function handleImageUpload(blob: Blob): Promise<string> {
    if (localPersona.value.filename) {
        const taskSubmission = await characterStore.uploadCharacterImage(localPersona.value.filename, blob);
        const finalTask = await taskStore.pollTaskResult(taskSubmission.task_id);
        if (finalTask.status === 'success' && finalTask.result.image_url) {
            return finalTask.result.image_url;
        } else {
            throw new Error(finalTask.error?.error || "图片上传任务失败");
        }
    }
    throw new Error('人设尚未保存，无法上传图片');
}
</script>