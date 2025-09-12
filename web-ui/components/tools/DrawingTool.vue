<template>
  <div class="h-full w-full flex flex-col">
    <header class="p-3 border-b border-gray-700 bg-gray-800/50 shrink-0">
      <div v-if="aigcStore.config" class="text-sm text-gray-400 text-center">
        当前使用 <a :href="aigcStore.config.docs_url" target="_blank" class="text-cyan-400 hover:underline">{{ aigcStore.config.service_name }}</a> 服务。
      </div>
    </header>
    
    <CommonTabbedContent :tabs="tabs" initial-tab="txt2img" theme-color="cyan" class="flex-grow min-h-0">
      <template #txt2img>
        <div class="h-full w-full p-6 grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-hidden">
          <AIGCParamsPanel 
            v-model:params="aigcStore.txt2imgParams"
            :available-models="aigcStore.config?.available_models || []"
            @generate="aigcStore.generateTxt2Img"
            @analyze-prompt="isAnalyzeModalOpen = true"
            :is-generating="aigcStore.isGenerating"
          />
          <AIGCPreviewPanel 
            :image-url="aigcStore.generatedImageUrl"
            :is-generating="aigcStore.isGenerating"
          />
        </div>
      </template>

      <template #img2img>
         <div class="h-full w-full p-6 grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-hidden">
            <AIGCParamsPanel 
              v-model:params="aigcStore.img2imgParams"
              :available-models="aigcStore.config?.available_models || []"
              @generate="aigcStore.generateImg2Img"
              @analyze-prompt="isAnalyzeModalOpen = true"
              :is-generating="aigcStore.isGenerating"
              :is-img2img="true"
            >
              <AIGCImageUploader 
                v-model:base64="aigcStore.sourceImageBase64"
                class="mb-4"
              />
            </AIGCParamsPanel>

            <AIGCPreviewPanel 
              :image-url="aigcStore.generatedImageUrl"
              :is-generating="aigcStore.isGenerating"
            />
        </div>
      </template>
    </CommonTabbedContent>

    <ClientOnly>
      <AIGCAnalyzePromptModal
        v-if="isAnalyzeModalOpen"
        @close="isAnalyzeModalOpen = false"
        @analyze="handleAnalyze"
      />
    </ClientOnly>

  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useAigcStore } from '~/stores/aigcStore';
import CommonTabbedContent from '~/components/common/TabbedContent.vue';
import AIGCParamsPanel from '~/components/tools/aigc/ParamsPanel.vue';
import AIGCPreviewPanel from '~/components/tools/aigc/PreviewPanel.vue';
import AIGCImageUploader from '~/components/tools/aigc/ImageUploader.vue';
import AIGCAnalyzePromptModal from '~/components/tools/aigc/AnalyzePromptModal.vue';

const aigcStore = useAigcStore();
const isAnalyzeModalOpen = ref(false);

const tabs = [
    { id: 'txt2img', label: '文生图 (Txt2Img)' },
    { id: 'img2img', label: '图生图 (Img2Img)' },
];

onMounted(() => {
    aigcStore.fetchConfig();
});

function handleAnalyze(payload: { image_base64: string, strategy: 'gemini' | 'deepdanbooru' }) {
    isAnalyzeModalOpen.value = false;
    aigcStore.analyzePromptFromImage(payload.image_base64, payload.strategy);
}
</script>