<template>
  <div 
    class="py-2 px-1 relative group" 
    @mouseenter="showMenu = true" 
    @mouseleave="showMenu = false"
  >
    <div class="flex items-start" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
      
      <div class="max-w-4xl w-full relative">
        
        <div 
            v-if="showMenu && !isEditing" 
            class="absolute -top-4 flex items-center space-x-1 bg-gray-900/80 backdrop-blur-sm p-1 rounded-md shadow-lg transition-opacity opacity-0 group-hover:opacity-100 z-10"
            :class="message.role === 'user' ? 'left-2' : 'right-2'"
        >
            <button title="播放语音" @click="handlePlayAudio" :disabled="ttsStore.isSynthesizing" class="p-1 hover:bg-gray-700 rounded text-sm disabled:opacity-50">
              <svg v-if="ttsStore.isSynthesizing" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              <span v-else>🔊</span>
            </button>
            <button title="编辑" @click="startEditing" class="p-1 hover:bg-gray-700 rounded text-sm">✏️</button>
            <button title="删除" @click="emit('delete', message.id)" class="p-1 hover:bg-gray-700 rounded text-sm">🗑️</button>
            <button v-if="message.role === 'model'" title="AI重写 (另一种说法)" @click="emit('rewrite', message.id)" class="p-1 hover:bg-gray-700 rounded text-sm">🔄</button>
            <button v-if="message.role === 'model'" title="AI重新生成" @click="emit('regenerate', message.id)" class="p-1 hover:bg-gray-700 rounded text-sm">✨</button>
            <button v-if="message.role === 'model' && message.isComplete" title="继续回复" @click="emit('continue', message.id)" class="p-1 hover:bg-gray-700 rounded text-sm">➡️</button>
        </div>

        <div class="p-3 rounded-lg" :class="[message.role === 'user' ? 'bg-cyan-800' : 'bg-gray-700', { 'border border-red-500/50': message.isError }]">
            <div v-if="message.role === 'user'">
                <textarea
                    v-if="isEditing"
                    ref="textareaRef"
                    v-model="editedContent"
                    class="w-full bg-cyan-900 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-shadow resize-none overflow-y-hidden"
                    @input="autoGrow"
                    @blur="saveEdit"
                    @keydown.enter.exact.prevent="saveEdit"
                    @keydown.esc.prevent="cancelEdit"
                ></textarea>
                <p v-else class="whitespace-pre-wrap">{{ message.content }}</p>
            </div>
          
            <div v-else>
                <div class="font-bold text-cyan-400 flex items-center select-none">
                    <span class="ml-1">{{ characterName }}</span>
                </div>
                
                <div class="mt-2">
                    <div>
                        <textarea
                            v-if="isEditing"
                            ref="textareaRef"
                            v-model="editedContent"
                            class="w-full bg-gray-800 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-shadow resize-none overflow-y-hidden"
                            @input="autoGrow"
                            @blur="saveEdit"
                            @keydown.enter.exact.prevent="saveEdit"
                            @keydown.esc.prevent="cancelEdit"
                        ></textarea>
                        <ClientOnly v-else>
                          <ContentRenderer :content="currentContent" />
                        </ClientOnly>
                         <span v-if="message.isStreaming && !currentContent" class="animate-pulse">▍</span>
                    </div>

                    <div v-if="message.isError" class="mt-3 p-2 bg-red-900/30 rounded-md border border-red-500/30">
                        <p class="text-xs text-red-300 whitespace-pre-wrap">{{ message.errorContent }}</p>
                        <button @click="emit('retry', message.id)" class="mt-2 text-xs bg-red-600 hover:bg-red-500 text-white font-semibold py-1 px-2 rounded transition-colors">
                          重试
                        </button>
                    </div>
                    
                    <div v-if="hasAlternatives || message.tokenUsage || message.aigcTask" class="flex items-center justify-center space-x-4 mt-2 text-xs text-gray-500">
                        <div v-if="hasAlternatives" class="flex items-center justify-center space-x-2">
                          <button @click="prevAlternative" class="p-1 hover:bg-gray-600 rounded-full">‹</button>
                          <span>{{ (message.activeAlternative ?? -1) + 2 }} / {{ totalAlternatives }}</span>
                          <button @click="nextAlternative" class="p-1 hover:bg-gray-600 rounded-full">›</button>
                        </div>
                        <div v-if="message.tokenUsage" class="font-mono" :title="`Prompt: ${message.tokenUsage.prompt_token_count} | Completion: ${message.tokenUsage.candidates_token_count}`">
                          T: {{ message.tokenUsage.total_token_count }}
                        </div>
                        <!-- [新增] AI绘画任务状态显示 -->
                        <div v-if="message.aigcTask" class="font-mono flex items-center gap-1" :title="`AIGC Task ID: ${message.aigcTask.taskId}`">
                          <span>🎨</span>
                          <span v-if="message.aigcTask.status === 'processing'" class="animate-pulse">生成中...</span>
                          <span v-if="message.aigcTask.status === 'failed'" class="text-red-400">失败</span>
                        </div>
                    </div>

                    <!-- [新增] AI生成的图片展示区域 -->
                    <div v-if="message.aigcTask?.status === 'success' && message.aigcTask.imageUrl" class="mt-3">
                      <img :src="message.aigcTask.imageUrl" class="max-w-full h-auto rounded-lg border border-gray-600" alt="AI Generated Image" />
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue';
import type { ChatMessage, TtsSegment } from '~/types/api';
import { useTtsStore } from '~/stores/ttsStore';
import { useSettingsStore } from '~/stores/settings';
import { useCharacterStore } from '~/stores/characterStore';
import { storeToRefs } from 'pinia';
import ContentRenderer from './ContentRenderer.client.vue';

const props = defineProps<{
  message: ChatMessage;
  characterName: string;
}>();

const emit = defineEmits<{
    (e: 'delete', messageId: number): void;
    (e: 'edit', payload: { messageId: number, newContent: string }): void;
    (e: 'regenerate', messageId: number): void;
    (e: 'continue', messageId: number): void;
    (e: 'retry', messageId: number): void;
    (e: 'set-active-alternative', payload: { messageId: number, index: number }): void;
    (e: 'rewrite', messageId: number): void;
    (e: 'complete-message', messageId: number): void;
    (e: 'send-option', content: string): void;
    (e: 'regenerate-options', messageId: number): void;
}>();

const ttsStore = useTtsStore();
const settingsStore = useSettingsStore();
const characterStore = useCharacterStore();
const { ttsVoiceAssignments } = storeToRefs(settingsStore);
const { characters, activeCharacter } = storeToRefs(characterStore);

const showMenu = ref(false);
const isEditing = ref(false);
const editedContent = ref('');
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const hasAlternatives = computed(() => (props.message.alternatives?.length ?? 0) > 0);
const totalAlternatives = computed(() => 1 + (props.message.alternatives?.length ?? 0));
const currentContent = computed(() => {
    if (props.message.activeAlternative === undefined || props.message.activeAlternative === -1) {
        return props.message.content;
    }
    return props.message.alternatives?.[props.message.activeAlternative] ?? props.message.content;
});

watch(isEditing, async (editing) => {
    if (editing) {
        editedContent.value = currentContent.value;
        await nextTick();
        if (textareaRef.value) {
            textareaRef.value.focus();
            textareaRef.value.style.height = 'auto';
            textareaRef.value.style.height = `${textareaRef.value.scrollHeight}px`;
        }
    }
});

function startEditing() { isEditing.value = true; }
function saveEdit() {
    if (isEditing.value && editedContent.value.trim() && editedContent.value.trim() !== currentContent.value) {
        emit('edit', { messageId: props.message.id, newContent: editedContent.value });
    }
    isEditing.value = false;
}
function cancelEdit() { isEditing.value = false; }

function autoGrow(event: Event) {
    const el = event.target as HTMLTextAreaElement;
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight}px`;
}

function setActiveAlternative(index: number) {
    emit('set-active-alternative', { messageId: props.message.id, index });
}

function prevAlternative() {
    const current = props.message.activeAlternative ?? -1;
    const newIndex = current <= -1 ? totalAlternatives.value - 2 : current - 1;
    setActiveAlternative(newIndex);
}

function nextAlternative() {
    const current = props.message.activeAlternative ?? -1;
    const newIndex = current >= totalAlternatives.value - 2 ? -1 : current + 1;
    setActiveAlternative(newIndex);
}

function parseContentForTTS(content: string): TtsSegment[] {
    const segments: TtsSegment[] = [];
    const assignments = ttsVoiceAssignments.value;
    const userPersona = characters.value[settingsStore.activePersonaKey || '']?.displayName || 'User';
    const charVoice = activeCharacter.value?.voice || assignments.char || 'zh-CN-XiaoxiaoNeural';

    const lines = content.split('\n').filter(line => line.trim() !== '');
    const speakerRegex = new RegExp(`^(${props.characterName}|${userPersona}):\\s*`);

    for (const line of lines) {
        const speakerMatch = line.match(speakerRegex);
        if (speakerMatch && speakerMatch[1]) {
            const speaker = speakerMatch[1];
            const text = line.substring(speakerMatch[0].length);
            const voice = speaker === props.characterName ? charVoice : assignments.user;
            segments.push([text, voice]);
        } else {
             segments.push([line, assignments.narrator]);
        }
    }
    return segments;
}


async function handlePlayAudio() {
  let segments: TtsSegment[] = [];
  const assignments = ttsVoiceAssignments.value;
  
  if (props.message.role === 'user') {
    segments = [[currentContent.value, assignments.user]];
  } else {
    segments = parseContentForTTS(currentContent.value);
  }

  if (segments.length > 0) {
    const audio = await ttsStore.synthesizeBatch(segments);
    audio?.play();
  }
}
</script>