<template>
  <div class="h-full w-full flex flex-col">
    <CommonTabbedContent :tabs="tabs" initial-tab="single" theme-color="green" class="flex-grow min-h-0">
      
      <template #settings>
        <div class="h-full w-full p-6 flex-grow min-h-0 pr-4">
          <div class="space-y-6 max-w-2xl mx-auto">
             <TTSServiceSettings />
          </div>
        </div>
      </template>

      <template #single>
        <div class="h-full w-full p-6 flex-grow min-h-0 pr-4">
          <div class="space-y-6 max-w-2xl mx-auto">
            <TTSSingleSynthesizer />
          </div>
        </div>
      </template>

      <template #dialogue>
        <div class="h-full w-full p-6 flex-grow min-h-0 pr-4">
           <div class="space-y-6 max-w-3xl mx-auto">
              <TTSDialogueSynthesizer />
           </div>
        </div>
      </template>

    </CommonTabbedContent>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useTtsStore } from '~/stores/ttsStore';
import CommonTabbedContent from '~/components/common/TabbedContent.vue';
import TTSSingleSynthesizer from '~/components/tools/tts/SingleSynthesizer.vue';
import TTSDialogueSynthesizer from '~/components/tools/tts/DialogueSynthesizer.vue';
import TTSServiceSettings from '~/components/tools/tts/ServiceSettings.vue';

const ttsStore = useTtsStore();

const tabs = [
    { id: 'settings', label: '服务设置' },
    { id: 'single', label: '单句合成' },
    { id: 'dialogue', label: '对话合成' },
];

onMounted(() => {
    ttsStore.fetchVoices();
});
</script>