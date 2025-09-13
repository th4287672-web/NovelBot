<template>
  <div>
    <button
      @click="logStore.toggleVisibility"
      class="fixed bottom-4 right-4 z-[100] p-3 bg-indigo-600 hover:bg-indigo-500 rounded-full shadow-lg text-white transition-transform transform hover:scale-110"
      title="切换开发日志"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
    </button>

    <transition name="slide-fade">
      <div 
        v-if="logStore.isVisible"
        class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[99]"
        @click.self="logStore.toggleVisibility"
      >
        <div class="w-11/12 h-5/6 max-w-4xl bg-gray-900 border border-indigo-500/50 rounded-lg shadow-2xl flex flex-col">
          <header class="p-3 border-b border-gray-700 flex justify-between items-center shrink-0">
            <h2 class="font-semibold text-indigo-300">前端实时日志</h2>
            <div class="flex items-center gap-3">
              <button 
                @click="layoutDiagnosis.toggle" 
                class="btn btn-secondary text-xs !px-3 !py-1"
                :class="{ 'bg-yellow-600/30 border-yellow-500 text-yellow-300': layoutDiagnosis.isEnabled.value }"
              >
                布局诊断
              </button>
              <button @click="logStore.clearLogs" class="btn btn-secondary text-xs !px-3 !py-1">清空</button>
              <button @click="downloadLogs" class="btn btn-primary bg-indigo-600 hover:bg-indigo-500 text-xs !px-3 !py-1">下载日志</button>
              <button @click="logStore.toggleVisibility" class="text-gray-500 hover:text-white">&times;</button>
            </div>
          </header>
          <main ref="logContainer" class="flex-grow p-2 overflow-y-auto">
            <div v-for="log in logStore.logs" :key="log.id" class="font-mono text-xs mb-1 flex">
              <span class="text-gray-600 shrink-0">{{ formatTimestamp(log.timestamp) }}</span>
              <span class="mx-2 shrink-0" :class="levelColor[log.level]">{{ log.level.toUpperCase() }}</span>
              <pre class="whitespace-pre-wrap break-all text-gray-300">{{ log.message }}</pre>
            </div>
          </main>
        </div>
      </div>
    </transition>
    
    <CommonLayoutDiagnosisPopup :rect="layoutDiagnosis.rect.value" :is-enabled="layoutDiagnosis.isEnabled.value" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useLogStore } from '~/stores/logStore';
import type { LogEntry } from '~/stores/logStore';
import { useLayoutDiagnosis } from '~/composables/useLayoutDiagnosis';
import CommonLayoutDiagnosisPopup from '~/components/common/LayoutDiagnosisPopup.vue';

const logStore = useLogStore();
const logContainer = ref<HTMLElement | null>(null);
const layoutDiagnosis = useLayoutDiagnosis();

const levelColor: Record<LogEntry['level'], string> = {
  log: 'text-gray-400',
  info: 'text-cyan-400',
  debug: 'text-purple-400',
  warn: 'text-yellow-400',
  error: 'text-red-400',
};

watch(() => logStore.logs.length, () => {
  if (logContainer.value) {
    nextTick(() => {
      logContainer.value!.scrollTop = logContainer.value!.scrollHeight;
    });
  }
});

function formatTimestamp(isoString: string): string {
  return new Date(isoString).toLocaleTimeString();
}

function downloadLogs() {
  const logText = logStore.logs
    .map(log => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`)
    .join('\n');
  
  const blob = new Blob([logText], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mynovelbot_frontend_trace_${new Date().toISOString()}.log`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>