<template>
  <div class="fixed inset-y-0 right-0 h-full w-full max-w-sm bg-gray-800 border-l border-gray-700 shadow-2xl z-40 transform transition-transform duration-300 ease-in-out"
       :class="uiStore.isRunSettingsPanelOpen ? 'translate-x-0' : 'translate-x-full'">
    <div class="h-full flex flex-col">
      <header class="flex justify-between items-center shrink-0 p-4 border-b border-gray-700">
        <h2 class="text-lg font-semibold text-gray-200">运行设置</h2>
        <div class="flex items-center gap-2">
            <button class="btn btn-secondary !p-2 text-sm flex items-center gap-1"><span class="material-symbols-outlined notranslate text-base">code</span> 获取代码</button>
            <button @click="resetToDefaults" title="重置为默认" class="btn btn-secondary !p-2"><span class="material-symbols-outlined notranslate text-base">reset_settings</span></button>
            <button @click="uiStore.toggleRunSettingsPanel" title="关闭" class="btn btn-secondary !p-2"><span class="material-symbols-outlined notranslate text-base">close</span></button>
        </div>
      </header>

      <div class="flex-grow min-h-0 overflow-y-auto p-4">
        <section>
          <button @click="isModelPanelOpen = true" class="w-full text-left p-4 bg-gray-900/50 rounded-md border border-gray-700 hover:border-cyan-500 transition-colors">
            <h4 class="text-base font-semibold text-white">{{ selectedModel?.display_name || '选择模型' }}</h4>
            <p class="text-sm text-gray-400 font-mono">{{ selectedModel?.name.replace('models/', '') || '点击以选择' }}</p>
            <p class="mt-1 text-sm text-gray-500 truncate">{{ selectedModel?.description || '请从可用模型列表中选择一个。' }}</p>
          </button>
        </section>
      </div>
      
      <footer class="p-4 border-t border-gray-700 shrink-0">
        <button @click="saveSettings" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500 w-full">应用并保存</button>
      </footer>
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
import { officialModelData } from '~/utils/modelData';

const settingsStore = useSettingsStore();
const uiStore = useUIStore();

const defaultSettings: GenerationConfig = {
    model: 'models/gemini-2.5-pro',
    temperature: 0.8,
    top_p: 0.9,
    top_k: 40,
    max_output_tokens: 4096,
};

const localSettings = ref<GenerationConfig>(deepClone(settingsStore.generationConfig || defaultSettings));
const isModelPanelOpen = ref(false);

const selectedModel = computed(() => {
    if (!localSettings.value.model) return null;
    const officialInfo = officialModelData.find(m => m.name === localSettings.value.model);
    const verifiedInfo = settingsStore.verifiedModels.find(m => m.name === localSettings.value.model);

    if (officialInfo) {
      return {
        ...verifiedInfo,
        ...officialInfo, 
      };
    }
    return verifiedInfo || null;
});

watch(() => settingsStore.generationConfig, (newConfig) => {
    if (newConfig) {
        localSettings.value = deepClone(newConfig);
    }
}, { immediate: true, deep: true });

onMounted(() => {
    if (settingsStore.verifiedModels.length === 0 && settingsStore.modelStatus !== 'checking') {
        settingsStore.checkModels().catch(err => {
            uiStore.setGlobalError(`自动检查模型失败: ${err.message}`);
        });
    }
});

function resetToDefaults() {
    localSettings.value = deepClone(defaultSettings);
    const featuredModels = officialModelData.filter(m => m.categories.includes('Featured'));
    const firstAvailableFeatured = featuredModels.find(fm => settingsStore.verifiedModels.some(vm => vm.name === fm.name));
    if (firstAvailableFeatured) {
        localSettings.value.model = firstAvailableFeatured.name;
    } else if (settingsStore.verifiedModels.length > 0) {
        const firstModel = settingsStore.verifiedModels[0];
        if (firstModel) {
            localSettings.value.model = firstModel.name;
        }
    }
}

async function saveSettings() {
    try {
        await settingsStore.updateGenerationConfig(localSettings.value);
        uiStore.setGlobalError("运行设置已成功保存！");
        uiStore.toggleRunSettingsPanel();
    } catch (error) {
        uiStore.setGlobalError(`保存设置失败: ${error}`);
    }
}

function handleModelSelect(model: ModelDetails) {
    localSettings.value.model = model.name;
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
</style>