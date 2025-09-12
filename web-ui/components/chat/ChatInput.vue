<template>
  <div class="p-4 flex flex-col relative">
    <MemorySuggestionPanel
      v-if="memorySuggestions.length > 0"
      :suggestions="memorySuggestions"
      @accept="acceptMemorySuggestions"
      @dismiss="dismissMemorySuggestions"
    />
    
    <SuggestReplyPanel 
      v-if="showSuggestions" 
      :suggestion-state="suggestionState"
      @select-suggestion="selectSuggestion" 
      @close="toggleSuggestions"
      @generate="(guidance: string) => emit('fetch-suggestions', guidance)"
    />

    <div class="flex items-center justify-between p-2 text-xs text-gray-400">
      <div class="flex items-center space-x-4">
        <label class="flex items-center cursor-pointer"><input type="checkbox" v-model="uiStore.isStreamingEnabled" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-cyan-500 focus:ring-cyan-600"><span class="ml-2">流式</span></label>
        <label class="flex items-center cursor-pointer"><input type="checkbox" v-model="isAutoScrollEnabled" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-cyan-500 focus:ring-cyan-600"><span class="ml-2">滚动</span></label>
        <label class="flex items-center cursor-pointer"><input type="checkbox" v-model="chatStore.isVoiceMode" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-cyan-500 focus:ring-cyan-600"><span class="ml-2">语音模式</span></label>
      </div>
      <div v-if="statusText" class="text-yellow-400 font-mono animate-pulse">
        {{ statusText }}
      </div>
    </div>
    <textarea 
      v-model="userInput"
      @keydown="handleKeydown"
      :disabled="isBusy || !activeSessionId"
      class="w-full flex-grow bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-shadow resize-none disabled:opacity-50"
      :placeholder="isImpersonating ? 'AI正在代笔...' : (!activeSessionId ? '正在加载会话...' : '在这里输入消息 (Enter 发送, Shift + Enter 換行)...')"
    ></textarea>
    <div class="flex justify-between items-center mt-2">

      <div class="flex items-center space-x-2">
        <button @click="handleSuggestion" :disabled="isBusy || !activeSessionId" title="获取回复建议 / AI代笔" class="p-2 rounded-full hover:bg-gray-700 transition-colors disabled:opacity-50">
          <svg v-if="suggestionState.isLoading" class="animate-spin h-5 w-5 text-yellow-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-yellow-300" viewBox="0 0 20 20" fill="currentColor"><path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 5.05a1 1 0 011.414 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zM4 11a1 1 0 100-2H3a1 1 0 100 2h1z" /></svg>
        </button>
        <button @click="toggleRecording" :disabled="isBusy || !activeSessionId" title="语音输入" class="p-2 rounded-full hover:bg-gray-700 transition-colors disabled:opacity-50" :class="{'bg-red-500/50': isRecording}">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" :class="isRecording ? 'text-red-300' : 'text-gray-300'" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8h-1a6 6 0 11-12 0H3a7.001 7.001 0 006 6.93V17H7a1 1 0 100 2h6a1 1 0 100-2h-2v-2.07z" clip-rule="evenodd" /></svg>
        </button>
      </div>

      <button 
        @click="handleSend"
        :disabled="isBusy || !userInput.trim() || !activeSessionId"
        class="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-2 px-4 rounded transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed"
      >
        {{ isBusy ? '...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, onMounted, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useUIStore } from '~/stores/ui';
import { useChatStore } from '~/stores/chat';
import { useSessionStore } from '~/stores/sessionStore';
import { useMemoryStore } from '~/stores/memoryStore';
import { useCharacterStore } from '~/stores/characterStore';
import SuggestReplyPanel from '~/components/chat/SuggestReplyPanel.vue';
import MemorySuggestionPanel from '~/components/chat/MemorySuggestionPanel.vue';
import { useSpeechRecognition } from '~/composables/useSpeechRecognition';

const uiStore = useUIStore();
const chatStore = useChatStore();
const sessionStore = useSessionStore();
const memoryStore = useMemoryStore();
const characterStore = useCharacterStore();

const { requestState, isImpersonating, suggestionState, memorySuggestions } = storeToRefs(chatStore);
const { activeSessionId } = storeToRefs(sessionStore);
const { isAutoScrollEnabled } = storeToRefs(uiStore);

const { isListening: isRecording, transcript, start, stop } = useSpeechRecognition({
  onResult: (result) => { userInput.value = result; },
  onError: (error) => { uiStore.setGlobalError(`语音识别错误: ${error}`); }
});
function toggleRecording() { isRecording.value ? stop() : start(); }

const emit = defineEmits<{
  (e: 'send', content: string): void;
  (e: 'fetch-suggestions', guidance: string): void;
  (e: 'clear-suggestions'): void;
}>();

const userInput = ref('');
const showSuggestions = ref(false);
const timer = ref<number | null>(null);
const elapsedTime = ref('0.0s');

onMounted(() => {
  timer.value = window.setInterval(() => {
    if (requestState.value.status !== 'idle' && requestState.value.startTime) {
      const seconds = (Date.now() - requestState.value.startTime) / 1000;
      elapsedTime.value = `${seconds.toFixed(1)}s`;
    }
  }, 100);
});

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value);
});

const isBusy = computed(() => 
  requestState.value.status === 'sending' || 
  requestState.value.status === 'thinking' || 
  requestState.value.status === 'streaming' || 
  isImpersonating.value ||
  suggestionState.value.isLoading
);

const statusText = computed(() => {
    if (isRecording.value) return '正在聆听...';
    if (suggestionState.value.isLoading) return '正在获取建议...';
    switch(requestState.value.status) {
        case 'sending': return `正在连接服务... (${elapsedTime.value})`;
        case 'thinking': return `AI 正在思考... (${elapsedTime.value})`;
        case 'streaming': return `AI 正在生成... (${elapsedTime.value})`;
        case 'error': return '发生错误，请重试。';
        default: return '';
    }
});

function handleSend() {
  if (userInput.value.trim()) {
    emit('send', userInput.value);
    userInput.value = '';
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    handleSend();
  }
}

function selectSuggestion(text: string) {
  userInput.value = text;
  handleSend();
  showSuggestions.value = false;
  emit('clear-suggestions');
}

function toggleSuggestions() {
    showSuggestions.value = !showSuggestions.value;
    if (!showSuggestions.value) {
        emit('clear-suggestions');
    }
}

function handleSuggestion() {
    toggleSuggestions();
    if (showSuggestions.value && suggestionState.value.suggestions.length === 0) {
        emit('fetch-suggestions', '');
    }
}

async function acceptMemorySuggestions(suggestions: string[]) {
  const activeChar = characterStore.activeCharacter;
  if (!activeChar) return;
  
  const currentMemory = memoryStore.memories[activeChar.filename] || { entries: [] };
  const updatedEntries = [...currentMemory.entries, ...suggestions];
  
  await memoryStore.updateMemories(activeChar.filename, { entries: updatedEntries });
  chatStore.clearMemorySuggestions();
}

function dismissMemorySuggestions() {
  chatStore.clearMemorySuggestions();
}

watch(transcript, (newVal) => {
    if (newVal) userInput.value = newVal;
});
</script>