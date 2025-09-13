<template>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="space-y-6">
            <section class="p-4 bg-gray-800/50 rounded-lg border border-gray-700 space-y-4">
                <h2 class="text-lg font-semibold text-purple-400">LLM 服务提供商</h2>
                <div>
                    <label for="llm-provider" class="archive-label">当前服务</label>
                    <select id="llm-provider" v-model="localLlmConfig.provider" @change="saveLlmAndNetwork" class="archive-input focus:border-purple-500">
                        <option value="google_gemini">Google Gemini (推荐)</option>
                        <option value="koboldai_horde">KoboldAI Horde (免费)</option>
                    </select>
                </div>
                <div v-if="localLlmConfig.provider === 'koboldai_horde'" class="space-y-4 pt-4 border-t border-gray-700/50">
                    <div>
                        <label for="horde-key" class="archive-label">Horde API Key (可选)</label>
                        <input id="horde-key" type="password" v-model="localLlmConfig.api_key" @change="saveLlmAndNetwork" class="archive-input focus:border-purple-500" placeholder="默认为 '0000000000' (匿名)">
                        <a href="https://stablehorde.net/register" target="_blank" class="text-xs text-purple-400 hover:underline mt-1 block">注册以获得更高优先级</a>
                    </div>
                     <div>
                        <label for="horde-models" class="archive-label">首选模型 (一行一个, 按优先级)</label>
                        <textarea id="horde-models" v-model="hordeModelsText" @change="saveLlmAndNetwork" rows="3" class="archive-textarea font-mono text-sm focus:border-purple-500" placeholder="例如: Chronos-Hermes-13b"></textarea>
                        <a href="https://stablehorde.net/models" target="_blank" class="text-xs text-purple-400 hover:underline mt-1 block">查看可用模型列表</a>
                    </div>
                </div>
            </section>
            <section v-if="localLlmConfig.provider === 'google_gemini'">
                <div class="p-4 bg-gray-800/50 rounded-lg border border-gray-700 space-y-3">
                    <div class="flex justify-between items-center">
                        <h3 class="font-semibold text-gray-300">Google AI 服务状态</h3>
                        <button @click="isStyleEditorOpen = true" class="btn btn-secondary !p-1.5" title="自定义样式">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                        </button>
                    </div>
                    <div class="flex items-center gap-4">
                        <p class="text-sm">状态: <span :class="statusColor">{{ statusText }}</span></p>
                        <button @click="checkAllModels" class="btn btn-secondary !px-4 !py-1.5 text-xs" :disabled="settingsStore.modelStatus === 'checking' || !localApiKeys.length">
                            <span v-if="settingsStore.modelStatus === 'checking'" class="animate-spin h-4 w-4 border-2 border-t-transparent border-white rounded-full"></span>
                            <span v-else>检查所有已保存的Key</span>
                        </button>
                    </div>
                    <p v-if="settingsStore.modelStatus === 'failed' && checkError" class="text-xs text-red-400">{{ checkError }}</p>
                    <div v-if="settingsStore.modelStatus === 'connected' && sortedVerifiedModels.length > 0">
                        <p class="text-sm text-gray-400 mb-2">已验证可用模型:</p>
                        <ul class="space-y-3">
                            <li v-for="model in sortedVerifiedModels" :key="model.name" class="grid grid-cols-2 gap-4 items-center">
                                <div class="flex items-center gap-2">
                                    <span class="text-green-400">✓</span>
                                    <span class="font-semibold" :style="{ fontSize: styles.displayName.fontSize + 'px', color: styles.displayName.color, fontFamily: styles.displayName.fontFamily }">{{ model.display_name }}</span>
                                </div>
                                <div class="flex items-center justify-end gap-2">
                                    <span class="truncate" :style="{ fontSize: styles.modelId.fontSize + 'px', color: styles.modelId.color, fontFamily: styles.modelId.fontFamily }">{{ model.name.replace('models/', '') }}</span>
                                    <button @click.stop="copyToClipboard(model.name.replace('models/', ''))" class="btn !p-1 !min-h-0 h-5 shrink-0" title="复制模型ID">
                                      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor"><path d="M7 9a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2H9a2 2 0 01-2-2V9z" /><path d="M5 3a2 2 0 00-2 2v6a2 2 0 002 2V5h6a2 2 0 00-2-2H5z" /></svg>
                                    </button>
                                    <a :href="model.docsUrl" target="_blank" rel="noopener noreferrer" @click.stop class="btn !p-1 !min-h-0 h-5 shrink-0" title="查看开发者文档">
                                      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clip-rule="evenodd" /></svg>
                                    </a>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>
            </section>
        </div>
        <div class="space-y-6">
             <section class="p-4 bg-gray-800/50 rounded-lg border border-gray-700 space-y-4">
                <h2 class="text-lg font-semibold text-purple-400">网络设置</h2>
                <div>
                    <label for="proxy-url" class="archive-label">HTTP 代理地址 (可选)</label>
                    <input id="proxy-url" type="text" v-model="localLlmConfig.proxy" @change="saveLlmAndNetwork" class="archive-input focus:border-purple-500" placeholder="例如: http://127.0.0.1:7890">
                    <p class="text-xs text-gray-500 mt-1">
                        用于连接 Google Gemini, Hugging Face 等需要代理的服务。
                    </p>
                </div>
            </section>
            <section v-if="localLlmConfig.provider === 'google_gemini'">
                <h3 class="font-semibold text-gray-300 mb-2">Google Gemini Keys</h3>
                <div class="space-y-2">
                    <div v-for="(apiKey, index) in localApiKeys" :key="apiKey.id" class="flex items-center gap-2 p-2 bg-gray-800/50 rounded">
                        <input type="text" v-model="apiKey.name" placeholder="名称 (例如: MyKey1)" class="archive-input !mt-0 w-40 text-sm">
                        <input :type="keyVisibility[apiKey.id] ? 'text' : 'password'" v-model="apiKey.key" placeholder="粘贴您的 API Key" class="archive-input !mt-0 flex-grow text-sm font-mono">
                        <button @click="toggleKeyVisibility(apiKey.id)" class="btn btn-secondary !p-1.5" :title="keyVisibility[apiKey.id] ? '隐藏' : '显示'">
                            <svg v-if="keyVisibility[apiKey.id]" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>
                        </button>
                        <button @click="testApiKey(apiKey)" class="btn btn-secondary !p-1.5" title="测试此 Key">
                            <span v-if="testStatus[apiKey.id] === 'testing'" class="animate-spin h-4 w-4 border-2 border-t-transparent border-white rounded-full"></span>
                            <span v-else-if="testStatus[apiKey.id] === 'success'" class="text-green-400">✓</span>
                            <span v-else-if="testStatus[apiKey.id] === 'error'" class="text-red-400">✗</span>
                            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                        </button>
                        <button @click="saveSingleApiKey(apiKey)" class="btn btn-secondary !p-1.5" title="保存此 Key">
                             <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>
                        </button>
                        <button @click="removeApiKey(index)" class="btn btn-danger !p-1.5" title="删除此 Key">-</button>
                    </div>
                </div>
                <div class="mt-3 flex items-center justify-between">
                    <a href="https://aistudio.google.com/app/apikey" target="_blank" class="text-sm text-purple-400 hover:underline">
                        获取 Google AI Key
                    </a>
                    <button @click="addApiKey" class="btn btn-secondary text-sm">+ 添加 Key</button>
                </div>
            </section>
        </div>
    </div>
    <ClientOnly>
        <CommonStyleEditorPopup
            v-if="isStyleEditorOpen"
            :initial-styles="styles"
            @close="isStyleEditorOpen = false"
            @save="handleStyleUpdate"
            @reset="resetStyles"
        />
    </ClientOnly>
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
import { apiService } from '~/services/api';
import { sortModels, type EnrichedModel } from '~/utils/modelSorter';
import { usePersistentStyle, type StyleConfig } from '~/composables/usePersistentStyle';
import CommonStyleEditorPopup from '~/components/common/StyleEditorPopup.vue';

const settingsStore = useSettingsStore();
const uiStore = useUIStore();

const { styles, updateStyle, resetStyles } = usePersistentStyle('model-list-styles');

const localApiKeys = ref<ApiKey[]>([]);
const localLlmConfig = ref<LLMServiceConfig>({ provider: 'google_gemini' });
const checkError = ref<string | null>(null);
const keyVisibility = ref<Record<string, boolean>>({});
const testStatus = ref<Record<string, 'idle' | 'testing' | 'success' | 'error'>>({});
const isStyleEditorOpen = ref(false);

const echartsContainer = ref<HTMLElement | null>(null);
const { setOption } = useEcharts(echartsContainer);

const sortedVerifiedModels = computed(() => {
    return sortModels(settingsStore.verifiedModels);
});

const hordeModelsText = computed({
    get: () => (localLlmConfig.value.horde_models || []).join('\n'),
    set: (value) => {
        if(localLlmConfig.value) {
            localLlmConfig.value.horde_models = value.split('\n').map(m => m.trim()).filter(Boolean);
        }
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

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    uiStore.setGlobalError('模型ID已复制!', 2000);
  } catch (err) {
    uiStore.setGlobalError('复制失败!', 2000);
  }
}

function toggleKeyVisibility(id: string) {
    keyVisibility.value[id] = !keyVisibility.value[id];
}

async function testApiKey(apiKey: ApiKey) {
    if (!apiKey.key.trim()) {
        uiStore.setGlobalError('API Key 不能为空。');
        return;
    }
    testStatus.value[apiKey.id] = 'testing';
    try {
        await apiService.testApiKey(apiKey.key, localLlmConfig.value.proxy);
        testStatus.value[apiKey.id] = 'success';
        uiStore.setGlobalError(`Key "${apiKey.name}" 测试成功！`, 2000);
    } catch (error) {
        testStatus.value[apiKey.id] = 'error';
        uiStore.setGlobalError(`Key "${apiKey.name}" 测试失败: ${error}`);
    } finally {
        setTimeout(() => {
            if (testStatus.value[apiKey.id] !== 'testing') {
                testStatus.value[apiKey.id] = 'idle';
            }
        }, 3000);
    }
}

async function saveSingleApiKey(apiKey: ApiKey) {
    const index = localApiKeys.value.findIndex(k => k.id === apiKey.id);
    if (index > -1) {
        localApiKeys.value[index] = { ...apiKey };
        try {
            await settingsStore.updateUserConfigValue('api_keys', JSON.parse(JSON.stringify(localApiKeys.value)));
            uiStore.setGlobalError(`Key "${apiKey.name}" 已保存！`, 2000);
        } catch (error) {
            uiStore.setGlobalError(`保存 Key "${apiKey.name}" 失败: ${error}`);
        }
    }
}

function addApiKey() {
    const newKey: ApiKey = {
        id: uuidv4(),
        name: `新密钥 ${localApiKeys.value.length + 1}`,
        key: '',
        provider: 'google',
    };
    localApiKeys.value.push(newKey);
    saveSingleApiKey(newKey);
}

async function removeApiKey(index: number) {
    localApiKeys.value.splice(index, 1);
    try {
        await settingsStore.updateUserConfigValue('api_keys', JSON.parse(JSON.stringify(localApiKeys.value)));
        uiStore.setGlobalError('API Key 已删除！', 2000);
    } catch (error) {
        uiStore.setGlobalError(`删除 API Key 失败: ${error}`);
    }
}

async function saveLlmAndNetwork() {
    try {
        await settingsStore.updateUserConfigValue('llm_service_config', JSON.parse(JSON.stringify(localLlmConfig.value)));
        uiStore.setGlobalError('服务与网络设置已保存！', 2000);
    } catch (error) {
        uiStore.setGlobalError(`保存服务与网络设置失败: ${error}`);
    }
}

async function checkAllModels() {
    if (!settingsStore.isReady) {
        uiStore.setGlobalError("数据尚未完全加载，请稍后再试。");
        return;
    }
    const hasValidKey = localApiKeys.value.some(apiKey => apiKey.key && apiKey.key.trim() !== '');
    if (!hasValidKey) {
        uiStore.setGlobalError("请先添加并保存至少一个有效的 API Key。");
        return;
    }
    checkError.value = null;
    try {
        await settingsStore.checkModels();
    } catch(e) {
        checkError.value = e instanceof Error ? e.message : String(e);
    }
}

function handleStyleUpdate(newStyles: StyleConfig) {
    updateStyle('displayName', newStyles.displayName);
    updateStyle('modelId', newStyles.modelId);
}
</script>