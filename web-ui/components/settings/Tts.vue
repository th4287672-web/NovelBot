<template>
    <div class="space-y-6 max-w-4xl mx-auto">
        <section class="space-y-4">
            <h2 class="text-lg font-semibold text-green-400">语音合成 (TTS) 设置</h2>
            <p class="text-sm text-gray-400">为聊天中的不同角色分配默认的声音。声音列表会自动从TTS服务获取。角色专属声音请在角色卡中设置。</p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label for="tts-voice-user" class="archive-label">你的声音 (User)</label>
                    <select id="tts-voice-user" v-model="localTtsAssignments.user" class="archive-input focus:border-green-500">
                        <option v-if="ttsStore.isLoadingVoices" value="">加载中...</option>
                        <option v-for="voice in ttsStore.voices" :key="voice.ShortName" :value="voice.ShortName">
                            {{ voice.DisplayName }} ({{ voice.Gender }})
                        </option>
                    </select>
                </div>
                <div>
                    <label for="tts-voice-char" class="archive-label">角色默认声音 (Character)</label>
                    <select id="tts-voice-char" v-model="localTtsAssignments.char" class="archive-input focus:border-green-500">
                        <option v-if="ttsStore.isLoadingVoices" value="">加载中...</option>
                        <option v-for="voice in ttsStore.voices" :key="voice.ShortName" :value="voice.ShortName">
                            {{ voice.DisplayName }} ({{ voice.Gender }})
                        </option>
                    </select>
                </div>
                <div>
                    <label for="tts-voice-narrator" class="archive-label">旁白声音 (Narrator)</label>
                    <select id="tts-voice-narrator" v-model="localTtsAssignments.narrator" class="archive-input focus:border-green-500">
                        <option v-if="ttsStore.isLoadingVoices" value="">加载中...</option>
                        <option v-for="voice in ttsStore.voices" :key="voice.ShortName" :value="voice.ShortName">
                            {{ voice.DisplayName }} ({{ voice.Gender }})
                        </option>
                    </select>
                </div>
            </div>
        </section>
        
        <footer class="pt-6 text-right w-full">
            <button @click="saveSettings" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500">
                保存所有设置
            </button>
        </footer>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useSettingsStore } from '~/stores/settings';
import { useTtsStore } from '~/stores/ttsStore';
import { useUIStore } from '~/stores/ui';
import type { TtsVoiceAssignments } from '~/types/api';
import { deepClone } from '~/utils/helpers';

const settingsStore = useSettingsStore();
const uiStore = useUIStore();
const ttsStore = useTtsStore();
const { ttsVoiceAssignments } = storeToRefs(settingsStore);

const localTtsAssignments = ref<TtsVoiceAssignments>({ user: '', char: '', narrator: '' });

onMounted(() => {
    ttsStore.fetchVoices();
});

watch(ttsVoiceAssignments, (newAssignments) => {
    if (newAssignments) {
        localTtsAssignments.value = deepClone(newAssignments);
    }
}, { immediate: true, deep: true });

async function saveSettings() {
    try {
        await settingsStore.updateUserConfigValue('tts_voice_assignments', localTtsAssignments.value);
        uiStore.setGlobalError('TTS 设置已成功保存！');
    } catch (error) {
        uiStore.setGlobalError(`保存 TTS 设置失败: ${error}`);
    }
}
</script>