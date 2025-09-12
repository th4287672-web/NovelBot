<template>
    <section class="space-y-4">
        <div>
            <label for="tts-service" class="archive-label">TTS 服务提供商</label>
            <select id="tts-service" v-model="localConfig.service" class="archive-input focus:border-green-500">
                <option value="microsoft">Microsoft Azure (推荐, 中文)</option>
                <option value="edge">Microsoft Edge (免费, 高质量中文)</option>
                <option value="chat_tts">ChatTTS (本地部署, 表现力强)</option>
                <option value="huggingface">Hugging Face (Qwen-Audio)</option>
                <option value="coqui">Coqui TTS (多语言, 英文效果好)</option>
                <option value="aihorde">AI Horde TTS (社区驱动)</option>
            </select>
        </div>
        <!-- Microsoft Azure 特定配置 -->
        <div v-if="localConfig.service === 'microsoft'">
            <label for="tts-api-key" class="archive-label">API Key (可选)</label>
            <input id="tts-api-key" type="password" v-model="localConfig.apiKey" class="archive-input focus:border-green-500" placeholder="通常不需要，内置Key可用">
            <label for="tts-region" class="archive-label mt-2">服务区域 (可选)</label>
            <input id="tts-region" type="text" v-model="localConfig.region" class="archive-input focus:border-green-500" placeholder="例如: eastus">
        </div>
        <!-- ChatTTS 特定配置 -->
        <div v-if="localConfig.service === 'chat_tts'">
            <label for="chat-tts-url" class="archive-label">ChatTTS API URL</label>
            <input id="chat-tts-url" type="text" v-model="localConfig.chatTtsApiUrl" class="archive-input focus:border-green-500" placeholder="例如: http://127.0.0.1:9966">
             <p class="text-xs text-gray-500 mt-1">
                需要您在本地单独运行 ChatTTS 的 API 服务。
            </p>
        </div>
        <!-- Hugging Face 特定配置 -->
        <div v-if="localConfig.service === 'huggingface'">
            <label for="hf-api-key" class="archive-label">Hugging Face API Key</label>
            <input id="hf-api-key" type="password" v-model="localConfig.huggingfaceApiKey" class="archive-input focus:border-green-500" placeholder="粘贴您的 HF Read Token">
            <label for="hf-model-id" class="archive-label mt-2">模型 ID</label>
            <input id="hf-model-id" type="text" v-model="localConfig.qwenTtsModelId" class="archive-input focus:border-green-500">
        </div>

        <div class="pt-4">
             <button @click="saveTtsConfig" class="btn btn-primary bg-green-600 hover:bg-green-500 w-full">
                保存服务设置
            </button>
        </div>
    </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import type { TtsServiceConfig } from '~/types/api';
import { deepClone } from '~/utils/helpers';

const settingsStore = useSettingsStore();
const uiStore = useUIStore();
const localConfig = ref<TtsServiceConfig>({ service: 'microsoft', apiKey: '', region: '' });

watch(() => settingsStore.ttsServiceConfig, (newConfig) => {
    if (newConfig) {
        localConfig.value = deepClone(newConfig);
    }
}, { immediate: true, deep: true });

async function saveTtsConfig() {
    try {
        await settingsStore.updateUserConfigValue('tts_service_config', localConfig.value);
        uiStore.setGlobalError("TTS 服务设置已保存！");
    } catch (e) {
        uiStore.setGlobalError(`保存失败: ${e}`);
    }
}
</script>