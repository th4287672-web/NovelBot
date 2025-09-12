<template>
  <div class="h-full w-full p-6 flex justify-center bg-gray-900 text-white">
    <div class="w-full max-w-2xl h-full flex flex-col">
      <header class="flex justify-between items-center shrink-0 mb-6 border-b border-gray-700 pb-4">
        <h1 class="text-2xl font-bold text-gray-200">运行设置</h1>
        <div class="flex items-center gap-2">
          <button @click="resetToDefaults" class="btn btn-secondary text-sm">重置为默认</button>
          <button @click="saveSettings" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500 text-sm">保存设置</button>
        </div>
      </header>

      <div class="flex-grow min-h-0 overflow-y-auto pr-4 space-y-8">
        <!-- 模型选择 -->
        <section>
          <h2 class="font-semibold text-lg text-gray-300 mb-2">模型</h2>
          <button @click="isModelPanelOpen = true" class="w-full text-left p-4 bg-gray-800 rounded-md border border-gray-700 hover:border-cyan-500 transition-colors">
            <h3 class="text-base font-semibold text-white">{{ selectedModel?.display_name || '选择模型' }}</h3>
            <p class="text-sm text-gray-400 font-mono">{{ selectedModel?.name || '点击以选择' }}</p>
            <p class="mt-1 text-sm text-gray-500">{{ selectedModel?.description || '请从可用模型列表中选择一个。' }}</p>
          </button>
        </section>

        <!-- 参数调整 -->
        <section>
          <h2 class="font-semibold text-lg text-gray-300 mb-2">参数</h2>
          <div class="p-4 bg-gray-800 rounded-md border border-gray-700 space-y-6">
            <!-- Temperature, Top-P, Top-K, Max Tokens 的滑块和输入框 (保持不变) -->
          </div>
        </section>
      </div>
    </div>
    
    <ClientOnly>
      <ChatModelSelectionPanel
        v-if="isModelPanelOpen"
        :selected-model-name="localSettings.model"
        @close="isModelPanelOpen = false"
        @select="handleModelSelect"
      />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import type { GenerationConfig, ModelDetails } from '~/types/api';
import { deepClone } from '~/utils/helpers';
import ChatModelSelectionPanel from '~/components/chat/ModelSelectionPanel.vue';

const settingsStore = useSettingsStore();
const uiStore = useUIStore();

const defaultSettings: GenerationConfig = {
    model: 'models/gemini-1.5-pro-latest',
    temperature: 0.8,
    top_p: 0.9,
    top_k: 40,
    max_output_tokens: 4096,
};

const localSettings = ref<GenerationConfig>(deepClone(settingsStore.generationConfig || defaultSettings));
const isModelPanelOpen = ref(false);

const selectedModel = computed(() => {
    return settingsStore.verifiedModels.find(m => m.name === localSettings.value.model);
});

watch(() => settingsStore.generationConfig, (newConfig) => {
    if (newConfig) {
        localSettings.value = deepClone(newConfig);
    }
}, { immediate: true });

onMounted(() => {
    if (settingsStore.verifiedModels.length === 0 && settingsStore.modelStatus !== 'checking') {
        settingsStore.checkModels().catch(err => {
            uiStore.setGlobalError(`自动检查模型失败: ${err.message}`);
        });
    }
});

function resetToDefaults() {
    localSettings.value = deepClone(defaultSettings);
    if (settingsStore.verifiedModels.length > 0 && settingsStore.verifiedModels[0]) {
        localSettings.value.model = settingsStore.verifiedModels[0].name;
    }
}

async function saveSettings() {
    try {
        await settingsStore.updateGenerationConfig(localSettings.value);
        uiStore.setGlobalError("运行设置已成功保存！");
    } catch (error) {
        uiStore.setGlobalError(`保存设置失败: ${error}`);
    }
}

function handleModelSelect(model: ModelDetails) {
    localSettings.value.model = model.name;
}
</script>