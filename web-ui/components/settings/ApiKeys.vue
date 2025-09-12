<template>
    <div class="space-y-6 max-w-4xl mx-auto">
        <section class="space-y-4">
            <h2 class="text-lg font-semibold text-purple-400">LLM 服务提供商</h2>
            <p class="text-sm text-gray-400">
                选择您想使用的核心语言模型服务。不同的服务有不同的模型、性能和内容策略。
            </p>
            <div>
                <label for="llm-provider" class="archive-label">当前服务</label>
                <select id="llm-provider" v-model="localLlmConfig.provider" class="archive-input focus:border-purple-500">
                    <option value="google_gemini">Google Gemini (推荐, 功能全面)</option>
                    <option value="koboldai_horde">KoboldAI Horde (免费, 社区驱动, 抗审查)</option>
                </select>
            </div>
        </section>

        <section v-if="localLlmConfig.provider === 'google_gemini'">
            <div class="p-4 bg-gray-800/50 rounded-lg border border-gray-700 space-y-3">
                <h3 class="font-semibold text-gray-300">Google AI 服务状态</h3>
                <div class="flex items-center gap-4">
                    <p class="text-sm">状态: <span :class="statusColor">{{ statusText }}</span></p>
                    <button @click="checkModels" class="btn btn-secondary !px-4 !py-1.5 text-xs" :disabled="settingsStore.modelStatus === 'checking'">
                        <span v-if="settingsStore.modelStatus === 'checking'" class="animate-spin h-4 w-4 border-2 border-t-transparent border-white rounded-full"></span>
                        <span v-else>连接并检查模型</span>
                    </button>
                </div>
                <p v-if="settingsStore.modelStatus === 'failed' && checkError" class="text-xs text-red-400">{{ checkError }}</p>
                <div v-if="settingsStore.modelStatus === 'connected'">
                    <p class="text-xs text-gray-400">已验证可用模型: <span class="font-mono text-green-400">{{ settingsStore.verifiedModels.map(m => m.display_name).join(', ') || '无' }}</span></p>
                </div>
            </div>

            <div v-if="tokenUsageData" class="mt-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                <h3 class="font-semibold text-gray-300 mb-2">Token 用量估算 (基于最新会话)</h3>
                <div ref="echartsContainer" class="w-full h-64"></div>
            </div>

            <h3 class="font-semibold text-gray-300 mt-6 mb-2">Google Gemini Keys</h3>
            <p class="text-sm text-gray-400 mb-2">
                您的 API Keys 将被安全地保存在您个人目录的配置文件中。
            </p>
            <div class="space-y-2">
                <div v-for="(apiKey, index) in localApiKeys" :key="apiKey.id" class="flex items-center gap-2 p-2 bg-gray-800/50 rounded">
                    <input type="text" v-model="apiKey.name" placeholder="名称 (例如: MyKey1)" class="archive-input !mt-0 w-48 text-sm">
                    <input type="password" v-model="apiKey.key" placeholder="粘贴您的 API Key" class="archive-input !mt-0 flex-grow text-sm font-mono">
                    <button @click="removeApiKey(index)" class="btn btn-danger !px-2 !py-1.5 text-xs">-</button>
                </div>
            </div>
            <div class="mt-3 flex items-center justify-between">
                <a href="https://aistudio.google.com/app/apikey" target="_blank" class="text-sm text-purple-400 hover:underline">
                    获取 Google AI Key
                </a>
                <button @click="addApiKey" class="btn btn-secondary text-sm">+ 添加 Key</button>
            </div>
        </section>

        <section v-if="localLlmConfig.provider === 'koboldai_horde'" class="space-y-4">
            <h3 class="font-semibold text-gray-300 mb-2">KoboldAI Horde 设置</h3>
            <div>
                <label for="horde-key" class="archive-label">Horde API Key (可选)</label>
                <input id="horde-key" type="password" v-model="localLlmConfig.api_key" class="archive-input focus:border-purple-500" placeholder="默认为 '0000000000' (匿名)">
                <a href="https://stablehorde.net/register" target="_blank" class="text-xs text-purple-400 hover:underline mt-1 block">注册以获得更高优先级</a>
            </div>
             <div>
                <label for="horde-models" class="archive-label">首选模型 (一行一个, 按优先级)</label>
                <textarea id="horde-models" v-model="hordeModelsText" rows="4" class="archive-textarea font-mono text-sm focus:border-purple-500" placeholder="例如: Chronos-Hermes-13b"></textarea>
                <a href="https://stablehorde.net/models" target="_blank" class="text-xs text-purple-400 hover:underline mt-1 block">查看可用模型列表</a>
            </div>
        </section>

        <section class="space-y-4 border-t border-gray-700 pt-4">
            <h3 class="font-semibold text-gray-300 mb-2">网络设置</h3>
            <div>
                <label for="proxy-url" class="archive-label">HTTP 代理地址 (可选)</label>
                <input id="proxy-url" type="text" v-model="localLlmConfig.proxy" class="archive-input focus:border-purple-500" placeholder="例如: http://127.0.0.1:7890">
                <p class="text-xs text-gray-500 mt-1">
                    用于连接 Google Gemini, Hugging Face 等需要代理的服务。
                </p>
            </div>
        </section>
        
        <footer class="pt-6 text-right w-full">
            <button @click="saveSettings" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500">
                保存 API 服务设置
            </button>
        </footer>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import type { ApiKey, LLMServiceConfig, TokenUsageStatsResponse } from '~/types/api';
import { v4 as uuidv4 } from 'uuid';
import { deepClone } from '~/utils/helpers';
import { useEcharts } from '~/composables/useEcharts';
import type { EChartsOption } from 'echarts';

const settingsStore = useSettingsStore();
const uiStore = useUIStore();

const localApiKeys = ref<ApiKey[]>([]);
const localLlmConfig = ref<LLMServiceConfig>({ provider: 'google_gemini' });
const checkError = ref<string | null>(null);

const echartsContainer = ref<HTMLElement | null>(null);
const { setOption } = useEcharts(echartsContainer);

const hordeModelsText = computed({
    get: () => (localLlmConfig.value.horde_models || []).join('\n'),
    set: (value) => {
        localLlmConfig.value.horde_models = value.split('\n').map(m => m.trim()).filter(Boolean);
    }
});

const statusText = computed(() => {
    switch (settingsStore.modelStatus) {
        case 'unchecked': return '未检查';
        case 'checking': return '检查中...';
        case 'connected': return '连接成功';
        case 'failed': return '连接失败';
        default: return '未知';
    }
});

const statusColor = computed(() => {
    switch (settingsStore.modelStatus) {
        case 'connected': return 'text-green-400 font-semibold';
        case 'failed': return 'text-red-400 font-semibold';
        default: return 'text-gray-400';
    }
});

const tokenUsageData = computed<EChartsOption | null>(() => {
    const stats = settingsStore.tokenUsageStats as TokenUsageStatsResponse | null;
    if (!stats) return null;
    return {
        tooltip: { trigger: 'axis' as const },
        xAxis: { type: 'category' as const, data: ['每小时', '每天', '每月'] },
        yAxis: { type: 'value' as const, name: 'Tokens' },
        series: [{ data: [stats.hourly, stats.daily, stats.monthly], type: 'bar' as const }]
    };
});

watch(tokenUsageData, (newData) => {
    if (newData) {
        setOption(newData, true);
    }
});

watch(() => settingsStore.userApiKeys, (newKeys) => {
    localApiKeys.value = deepClone(newKeys || []);
}, { immediate: true, deep: true });

watch(() => settingsStore.llmServiceConfig, (newLlmConfig) => {
    localLlmConfig.value = deepClone(newLlmConfig || { provider: 'google_gemini' });
}, { immediate: true, deep: true });

function addApiKey() {
    localApiKeys.value.push({
        id: uuidv4(),
        name: `新密钥 ${localApiKeys.value.length + 1}`,
        key: '',
        provider: 'google',
    });
}

function removeApiKey(index: number) {
    localApiKeys.value.splice(index, 1);
}

async function checkModels() {
    if (!settingsStore.isReady) {
        uiStore.setGlobalError("数据尚未完全加载，请稍后再试。");
        return;
    }
    checkError.value = null;
    try {
        await settingsStore.updateMultipleUserConfigValues({
            llm_service_config: localLlmConfig.value,
            api_keys: localApiKeys.value
        });
        await settingsStore.checkModels();
    } catch(e) {
        checkError.value = e instanceof Error ? e.message : String(e);
    }
}


async function saveSettings() {
    if (!settingsStore.isReady) {
        uiStore.setGlobalError("数据尚未完全加载，无法保存设置。请稍后再试。");
        console.warn('[DIAG] saveSettings aborted because settingsStore.isReady is false.');
        return;
    }
    console.log('[DIAG] saveSettings clicked. Preparing to save:', {
        api_keys: localApiKeys.value,
        llm_service_config: localLlmConfig.value
    });
    try {
        await settingsStore.updateMultipleUserConfigValues({
            api_keys: localApiKeys.value,
            llm_service_config: localLlmConfig.value
        });
        uiStore.setGlobalError('API 服务设置已成功保存！');
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error('[DIAG] saveSettings failed:', error);
        uiStore.setGlobalError(`保存 API 服务设置失败: ${message}`);
    }
}
</script>