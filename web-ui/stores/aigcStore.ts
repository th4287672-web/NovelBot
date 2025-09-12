// web-ui/stores/aigcStore.ts

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { apiService } from '~/services/api';
import { useUIStore } from './ui';
import { useSettingsStore } from './settings';
import type { DrawingConfig, GenerationRequest, Img2ImgRequest, ImageToPromptRequest } from '~/types/api';

export const useAigcStore = defineStore('aigc', () => {
    const uiStore = useUIStore();
    const settingsStore = useSettingsStore();

    const config = ref<DrawingConfig | null>(null);
    const isLoadingConfig = ref(false);
    const isGenerating = ref(false);
    const generatedImageUrl = ref<string | null>(null);

    const txt2imgParams = ref<GenerationRequest>({
        prompt: 'masterpiece, best quality, 1girl, solo, looking at viewer, short hair, brown hair, sailor uniform, classroom',
        negative_prompt: 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry',
        width: 512,
        height: 768,
        steps: 25,
        cfg_scale: 7.0,
        seed: -1,
        model: null,
    });

    const img2imgParams = ref<Omit<Img2ImgRequest, 'imageBase64'>>({
        prompt: 'masterpiece, best quality, 1girl',
        negative_prompt: 'lowres, bad anatomy',
        width: 512,
        height: 768,
        steps: 20,
        cfg_scale: 7.0,
        seed: -1,
        model: null,
        denoising_strength: 0.75
    });

    const sourceImageBase64 = ref<string | null>(null);
    const isAnalyzingPrompt = ref(false);

    async function pollTaskResult(taskId: string, timeout = 300000) {
        const startTime = Date.now();
        while (Date.now() - startTime < timeout) {
            try {
                const task = await apiService.getTaskStatus(taskId);
                if (task.status === 'success') {
                    return task.result;
                }
                if (task.status === 'failed') {
                    throw new Error(task.error?.error || '任务执行失败');
                }
                await new Promise(resolve => setTimeout(resolve, 3000)); 
            } catch (error) {
                 throw new Error(`轮询任务状态失败: ${error}`);
            }
        }
        throw new Error('任务超时');
    }

    async function fetchConfig() {
        if (config.value) return;
        isLoadingConfig.value = true;
        try {
            config.value = await apiService.getDrawingConfig();
            if (config.value.available_models && config.value.available_models.length > 0) {
                txt2imgParams.value.model = config.value.available_models[0];
                img2imgParams.value.model = config.value.available_models[0];
            }
        } catch (error) {
            uiStore.setGlobalError(`获取AI绘画配置失败: ${error}`);
        } finally {
            isLoadingConfig.value = false;
        }
    }

    async function generateTxt2Img() {
        if (isGenerating.value || !txt2imgParams.value.prompt || !settingsStore.userId) return;
        isGenerating.value = true;
        generatedImageUrl.value = null;
        uiStore.setGlobalError(null);
        try {
            const taskResponse = await apiService.generateTxt2Img(txt2imgParams.value, settingsStore.userId);
            const result = await pollTaskResult(taskResponse.task_id);
            generatedImageUrl.value = result.image_url;
        } catch (error) {
            uiStore.setGlobalError(`文生图失败: ${error}`);
        } finally {
            isGenerating.value = false;
        }
    }
    
    async function generateTxt2ImgFromChat(prompt: string): Promise<string | null> {
        if (!settingsStore.userId) return null;
        uiStore.setGlobalError(null);
        try {
            const params: GenerationRequest = {
                ...txt2imgParams.value,
                prompt: prompt,
            };
            const taskResponse = await apiService.generateTxt2Img(params, settingsStore.userId);
            return taskResponse.task_id;
        } catch (error) {
            uiStore.setGlobalError(`来自聊天的AI绘画任务启动失败: ${error}`);
            return null;
        }
    }

    async function generateImg2Img() {
        if (isGenerating.value || !sourceImageBase64.value || !img2imgParams.value.prompt || !settingsStore.userId) return;
        isGenerating.value = true;
        generatedImageUrl.value = null;
        uiStore.setGlobalError(null);
        try {
            const payload: Img2ImgRequest = {
                ...img2imgParams.value,
                imageBase64: sourceImageBase64.value
            };
            const taskResponse = await apiService.generateImg2Img(payload, settingsStore.userId);
            const result = await pollTaskResult(taskResponse.task_id);
            generatedImageUrl.value = result.image_url;
        } catch (error) {
            uiStore.setGlobalError(`图生图失败: ${error}`);
        } finally {
            isGenerating.value = false;
        }
    }

    async function analyzePromptFromImage(imageBase64: string, strategy: 'gemini' | 'deepdanbooru') {
        if (isAnalyzingPrompt.value) return;
        isAnalyzingPrompt.value = true;
        uiStore.setGlobalError(null);
        try {
            const payload: ImageToPromptRequest = { imageBase64, strategy };
            const response = await apiService.getImagePrompt(payload);
            
            if (txt2imgParams.value.prompt === '') {
                txt2imgParams.value.prompt = response.prompt;
            } else {
                img2imgParams.value.prompt = response.prompt;
            }
            uiStore.setGlobalError("提示词已成功生成并填充！");
        } catch (error) {
            uiStore.setGlobalError(`图片反推提示词失败: ${error}`);
        } finally {
            isAnalyzingPrompt.value = false;
        }
    }

    return {
        config,
        isLoadingConfig,
        isGenerating,
        generatedImageUrl,
        txt2imgParams,
        img2imgParams,
        sourceImageBase64,
        isAnalyzingPrompt,
        fetchConfig,
        generateTxt2Img,
        generateTxt2ImgFromChat,
        generateImg2Img,
        analyzePromptFromImage
    };
});