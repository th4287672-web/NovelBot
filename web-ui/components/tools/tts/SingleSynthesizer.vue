<template>
  <section class="space-y-4">
    <div>
        <label for="tts-voice" class="archive-label">选择声音</label>
        <select id="tts-voice" v-model="ttsStore.selectedVoice" class="archive-input focus:border-green-500">
            <option v-if="ttsStore.isLoadingVoices" value="">正在加载声音列表...</option>
            <option v-for="voice in ttsStore.voices" :key="voice.ShortName" :value="voice.ShortName">
                {{ voice.DisplayName }} ({{ voice.Gender }})
            </option>
        </select>
    </div>
    <div>
        <label for="tts-text" class="archive-label">输入文本 (支持 SSML)</label>
        <textarea id="tts-text" v-model="ttsStore.textToSpeak" rows="6" class="archive-textarea focus:border-green-500 font-mono text-sm"></textarea>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-3 pt-2">
        <div>
            <label for="tts-rate" class="archive-label">语速 ({{ ttsStore.params.rate }})</label>
            <input id="tts-rate" type="range" min="0" max="100" v-model.number="ttsStore.params.rate" class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500">
        </div>
        <div>
            <label for="tts-volume" class="archive-label">音量 ({{ ttsStore.params.volume }})</label>
            <input id="tts-volume" type="range" min="0" max="100" v-model.number="ttsStore.params.volume" class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500">
        </div>
        <div>
            <label for="tts-pitch" class="archive-label">音调 ({{ ttsStore.params.pitch }})</label>
            <input id="tts-pitch" type="range" min="0" max="100" v-model.number="ttsStore.params.pitch" class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500">
        </div>
    </div>
    <div class="pt-2 space-y-3">
        <button @click="ttsStore.synthesize" :disabled="!ttsStore.canSynthesize" class="btn btn-primary bg-green-600 hover:bg-green-500 w-full text-base">
            <svg v-if="ttsStore.isSynthesizing" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ ttsStore.isSynthesizing ? '正在合成...' : '合成并播放' }}
        </button>
        <TTSPlayerControls />
    </div>
  </section>
</template>

<script setup lang="ts">
import { useTtsStore } from '~/stores/ttsStore';
import TTSPlayerControls from './PlayerControls.vue';

const ttsStore = useTtsStore();
</script>