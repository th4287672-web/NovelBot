<template>
  <CommonBaseModal title="模型选择" theme-color="cyan" max-width="80rem" @close="emit('close')">
    <div class="flex flex-col h-[80vh]">
      <div class="shrink-0 p-2 border-b border-gray-700">
        <div class="flex items-center space-x-2">
          <button 
            v-for="category in categories" 
            :key="category"
            @click="activeCategory = category"
            class="px-3 py-1 text-sm rounded-full transition-colors"
            :class="activeCategory === category ? 'bg-cyan-600 text-white' : 'bg-gray-700 hover:bg-gray-600'"
          >
            {{ category }}
          </button>
        </div>
      </div>

      <div class="flex-grow min-h-0 overflow-y-auto">
        <div v-if="settingsStore.modelStatus === 'checking'" class="flex items-center justify-center h-full text-gray-400">
          <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-cyan-400"></div>
          <span class="ml-3">正在加载模型...</span>
        </div>
        <div v-else-if="filteredModels.length === 0" class="flex items-center justify-center h-full text-gray-500">
          <p>没有找到可用的模型。</p>
        </div>
        <div v-else>
          <div
            v-for="model in filteredModels"
            :key="model.name"
            @click="selectModel(model)"
            class="w-full text-left p-4 hover:bg-gray-700/50 transition-colors border-b border-gray-700 cursor-pointer"
            :class="{ 'bg-cyan-900/50 ring-2 ring-cyan-500': model.name === selectedModelName }"
          >
            <div class="flex justify-between items-start">
              <div class="flex-grow">
                <div class="flex items-center mb-2">
                  <svg v-if="model.icon.type === 'svg'" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 mr-3 text-cyan-400">
                    <path
                      v-for="(pathD, index) in model.icon.paths"
                      :key="index"
                      :d="pathD"
                      :fill="model.icon.fill || 'none'"
                      :stroke="model.icon.fill ? 'none' : 'currentColor'"
                      :stroke-width="model.icon.strokeWidth || 2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    ></path>
                  </svg>
                  <div class="flex items-center">
                    <h3 class="font-semibold text-white text-base">{{ model.display_name }}</h3>
                    <span v-if="model.isNew" class="ml-2 px-2 py-0.5 text-xs bg-blue-500 text-white rounded-full">New</span>
                  </div>
                </div>
                <p class="text-sm text-gray-400 font-mono mb-3">{{ model.name.replace('models/','') }}</p>
                <ul class="space-y-1.5 text-sm text-gray-300">
                  <li class="flex items-center">
                    <span class="material-symbols-outlined notranslate text-gray-500 mr-2 text-base">info</span>
                    {{ model.description }}
                  </li>
                  <li v-for="(price, pIndex) in model.pricingDetails" :key="pIndex" class="flex items-center">
                    <span class="material-symbols-outlined notranslate text-gray-500 mr-2 text-base">attach_money</span>
                    {{ price }}
                  </li>
                  <li class="flex items-center" v-if="model.knowledgeCutoff">
                    <span class="material-symbols-outlined notranslate text-gray-500 mr-2 text-base">network_intelligence_history</span>
                    知识截止: {{ model.knowledgeCutoff }}
                  </li>
                </ul>
              </div>
              <div class="flex items-center space-x-2 shrink-0">
                <button @click.stop.prevent="copyToClipboard(model.name.replace('models/',''))" class="btn btn-secondary !p-2" title="复制模型ID">
                  <span class="material-symbols-outlined notranslate text-base">content_copy</span>
                </button>
                <a :href="model.docsUrl" target="_blank" rel="noopener noreferrer" @click.stop class="btn btn-secondary !p-2" title="查看开发者文档">
                  <span class="material-symbols-outlined notranslate text-base">developer_guide</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import type { ModelDetails, Filename } from '~/types/api';
import { officialModelData } from '~/utils/modelData';
import type { OfficialModelEntry } from '~/utils/modelData';

defineProps<{
  selectedModelName: Filename;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'select', model: ModelDetails): void;
}>();

const settingsStore = useSettingsStore();
const uiStore = useUIStore();

type ModelCategory = 'All' | 'Featured' | 'Gemini' | 'Images' | 'Gemma';
const categories: readonly ModelCategory[] = ['All', 'Featured', 'Gemini', 'Images', 'Gemma'];
const activeCategory = ref<ModelCategory>('Featured');

type EnrichedModelDetails = ModelDetails & OfficialModelEntry & { docsUrl: string };

const enrichedModels = computed((): EnrichedModelDetails[] => {
  const verifiedModelNames = new Set(settingsStore.verifiedModels.map(m => m.name));
  return officialModelData
    .filter(model => verifiedModelNames.has(model.name))
    .map(model => {
      const verifiedModel = settingsStore.verifiedModels.find(v => v.name === model.name)!;
      const modelId = model.name.replace('models/','');
      const docsUrl = model.categories.includes('Gemma')
        ? 'https://ai.google.dev/gemma/docs/core?hl=zh-cn'
        : `https://ai.google.dev/gemini-api/docs/models/gemini?hl=zh-cn#${modelId}`;

      return {
        ...verifiedModel,
        ...model,
        docsUrl,
      };
    });
});

const filteredModels = computed(() => {
  if (activeCategory.value === 'All') {
    return enrichedModels.value;
  }
  return enrichedModels.value.filter(model => model.categories.includes(activeCategory.value));
});

function selectModel(model: ModelDetails) {
  emit('select', model);
  emit('close');
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    uiStore.setGlobalError('模型ID已复制!');
  } catch (err) {
    uiStore.setGlobalError('复制失败!');
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
</style>