
<template>
    <section class="space-y-4">
        <div>
            <label class="archive-label">对话脚本</label>
            <p class="text-xs text-gray-500 mb-2">格式: `发言人: 对话内容`。发言人可以是 `user`, `char` 或 `narrator`。</p>
            <textarea v-model="script" rows="10" class="archive-textarea focus:border-green-500 font-mono text-sm" placeholder="user: 你好，今天天气不错。
char: 是的，很适合散步。
..."></textarea>
        </div>
        <div class="pt-2">
            <button @click="synthesizeDialogue" :disabled="!canSynthesizeDialogue" class="btn btn-primary bg-green-600 hover:bg-green-500 w-full text-base">
                 <svg v-if="ttsStore.isSynthesizing" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ ttsStore.isSynthesizing ? '正在合成...' : '合成对话' }}
            </button>
            <TTSPlayerControls />
        </div>
    </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useTtsStore } from '~/stores/ttsStore';
import { useSettingsStore } from '~/stores/settings';
import TTSPlayerControls from './PlayerControls.vue';
import type { TtsSegment } from '~/types/api';

const ttsStore = useTtsStore();
const settingsStore = useSettingsStore();
const script = ref('');

const canSynthesizeDialogue = computed(() => !ttsStore.isSynthesizing && script.value.trim() !== '');

function synthesizeDialogue() {
    const lines = script.value.split('\n').filter(line => line.trim());
    const segments: TtsSegment[] = [];
    const assignments = settingsStore.ttsVoiceAssignments;

    for (const line of lines) {
        const parts = line.split(/:\s*/);
        if (parts.length >= 2) {
            const speaker = parts[0]!.toLowerCase().trim();
            const text = parts.slice(1).join(': ');
            let voice = assignments.narrator;
            if (speaker === 'user') {
                voice = assignments.user;
            } else if (speaker === 'char') {
                voice = assignments.char || 'zh-CN-XiaoxiaoNeural';
            }
            segments.push([text, voice]);
        } else {
            segments.push([line, assignments.narrator]);
        }
    }

    if(segments.length > 0) {
        ttsStore.synthesizeBatch(segments);
    }
}
</script>