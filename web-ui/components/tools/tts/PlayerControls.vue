<template>
    <div v-if="ttsStore.audioDataUrl" class="mt-4 p-3 bg-gray-800/50 rounded-lg space-y-2">
        <div class="flex items-center gap-3">
              <button @click="ttsStore.togglePlayPause" :disabled="!ttsStore.canPlay && !ttsStore.isPlaying" class="p-2 rounded-full bg-green-600 hover:bg-green-500 disabled:bg-gray-500 transition-colors" title="播放/暂停">
                <svg v-if="!ttsStore.isPlaying" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" /></svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd" /></svg>
            </button>
              <button @click="ttsStore.stop" :disabled="!ttsStore.audioDataUrl" class="p-2 rounded-full hover:bg-gray-700 disabled:opacity-50 transition-colors" title="停止">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 9a1 1 0 00-1 1v.01L7 10a1 1 0 001 1h4a1 1 0 001-1V9a1 1 0 00-1-1H8z" clip-rule="evenodd" /></svg>
            </button>
            <span class="text-xs font-mono text-gray-400">{{ ttsStore.formattedCurrentTime }}</span>
            <progress @click="handleSeek" class="w-full h-2 rounded-full overflow-hidden [&::-webkit-progress-bar]:bg-gray-700 [&::-webkit-progress-value]:bg-green-500 [&::-moz-progress-bar]:bg-green-500 cursor-pointer" :value="ttsStore.playbackProgress" max="100"></progress>
            <span class="text-xs font-mono text-gray-400">{{ ttsStore.formattedDuration }}</span>
            <button @click="handleDownload" :disabled="!ttsStore.audioDataUrl" class="p-2 rounded-full hover:bg-gray-700 disabled:opacity-50 transition-colors" title="下载音频">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clip-rule="evenodd" /></svg>
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { onUnmounted } from 'vue';
import { useTtsStore } from '~/stores/ttsStore';

const ttsStore = useTtsStore();

onUnmounted(() => {
    ttsStore.cleanup();
});

function handleSeek(event: MouseEvent) {
    const progressBar = event.currentTarget as HTMLProgressElement;
    const clickPosition = event.offsetX;
    const progressBarWidth = progressBar.offsetWidth;
    const percentage = (clickPosition / progressBarWidth) * 100;
    ttsStore.seek(percentage);
}

function handleDownload() {
    if (!ttsStore.audioDataUrl) return;

    const a = document.createElement('a');
    a.href = ttsStore.audioDataUrl;
    a.download = ttsStore.generateAudioFilename();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
</script>