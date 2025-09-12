<template>
    <CommonBaseModal title="图片反推提示词" theme-color="cyan" @close="emit('close')">
        <div class="space-y-4">
            <AIGCImageUploader v-model:base64="imageBase64" />
            <div>
                <label class="archive-label">分析策略</label>
                <div class="flex space-x-4">
                    <label class="flex items-center">
                        <input type="radio" v-model="strategy" value="gemini" class="form-radio text-cyan-500">
                        <span class="ml-2">Gemini (描述性)</span>
                    </label>
                    <label class="flex items-center">
                        <input type="radio" v-model="strategy" value="deepdanbooru" class="form-radio text-cyan-500">
                        <span class="ml-2">Danbooru (标签式)</span>
                    </label>
                </div>
            </div>
        </div>
        <template #footer-actions>
            <button @click="emit('close')" class="btn btn-secondary">取消</button>
            <button @click="handleAnalyze" :disabled="!imageBase64 || aigcStore.isAnalyzingPrompt" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500">
                {{ aigcStore.isAnalyzingPrompt ? '正在分析...' : '开始分析' }}
            </button>
        </template>
    </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useAigcStore } from '~/stores/aigcStore';
import AIGCImageUploader from './ImageUploader.vue';

const emit = defineEmits(['close', 'analyze']);

const aigcStore = useAigcStore();
const imageBase64 = ref<string | null>(null);
const strategy = ref<'gemini' | 'deepdanbooru'>('gemini');

function handleAnalyze() {
    if (imageBase64.value) {
        emit('analyze', { image_base64: imageBase64.value, strategy: strategy.value });
    }
}
</script>