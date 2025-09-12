<template>
  <div class="flex flex-col space-y-4 pr-4 overflow-y-auto">
    <slot></slot> <!-- 用于插入图生图的上传组件 -->
    
    <div>
      <label class="archive-label">模型 (Model)</label>
      <select v-model="localParams.model" class="archive-input focus:border-cyan-500" :disabled="availableModels.length === 0">
        <option v-if="availableModels.length === 0" disabled>当前服务不支持选择模型</option>
        <option v-for="model in availableModels" :key="model" :value="model">{{ model }}</option>
      </select>
    </div>
    <div>
      <label for="prompt" class="archive-label">正面提示词 (Prompt)</label>
      <div class="relative">
        <textarea id="prompt" v-model="localParams.prompt" rows="5" class="archive-textarea focus:border-cyan-500"></textarea>
        <button @click="emit('analyze-prompt')" class="absolute bottom-2 right-2 text-xs text-cyan-400 hover:underline">图生文</button>
      </div>
    </div>
    <div>
      <label for="negative_prompt" class="archive-label">负面提示词 (Negative Prompt)</label>
      <textarea id="negative_prompt" v-model="localParams.negative_prompt" rows="3" class="archive-textarea focus:border-cyan-500"></textarea>
    </div>
    
    <div v-if="isImg2img">
      <label for="denoising_strength" class="archive-label">重绘幅度 (Denoising Strength): {{ (localParams as any).denoising_strength }}</label>
      <input id="denoising_strength" type="range" min="0" max="1" step="0.01" v-model.number="(localParams as any).denoising_strength" class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500">
    </div>

    <div class="grid grid-cols-2 gap-4">
        <div>
            <label for="width" class="archive-label">宽度</label>
            <input id="width" type="number" v-model.number="localParams.width" class="archive-input focus:border-cyan-500" step="64" />
        </div>
        <div>
            <label for="height" class="archive-label">高度</label>
            <input id="height" type="number" v-model.number="localParams.height" class="archive-input focus:border-cyan-500" step="64" />
        </div>
    </div>
    <div class="grid grid-cols-2 gap-4">
        <div>
            <label for="steps" class="archive-label">步数 (Steps)</label>
            <input id="steps" type="number" v-model.number="localParams.steps" class="archive-input focus:border-cyan-500" />
        </div>
        <div>
            <label for="cfg_scale" class="archive-label">引导系数 (CFG Scale)</label>
            <input id="cfg_scale" type="number" v-model.number="localParams.cfg_scale" class="archive-input focus:border-cyan-500" step="0.5" />
        </div>
    </div>
      <div>
        <label for="seed" class="archive-label">种子 (Seed, -1为随机)</label>
        <input id="seed" type="number" v-model.number="localParams.seed" class="archive-input focus:border-cyan-500" />
    </div>
    <div class="pt-4">
        <button @click="emit('generate')" :disabled="!localParams.prompt || isGenerating" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500 w-full text-base">
              <svg v-if="isGenerating" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isGenerating ? '正在生成中...' : '开始生成' }}
        </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue';
import type { GenerationRequest, Img2ImgRequest } from '~/types/api';

type Params = GenerationRequest | Omit<Img2ImgRequest, 'image_base64'>;

const props = defineProps({
    params: {
        type: Object as PropType<Params>,
        required: true
    },
    availableModels: {
        type: Array as PropType<string[]>,
        required: true
    },
    isGenerating: Boolean,
    isImg2img: Boolean,
});

const emit = defineEmits(['update:params', 'generate', 'analyze-prompt']);

const localParams = computed({
    get: () => props.params,
    set: (value) => emit('update:params', value)
});
</script>