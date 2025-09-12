// web-ui/stores/ttsStore.ts

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { apiService } from '~/services/api';
import { useUIStore } from './ui';
import { useSettingsStore } from './settings';
import type { TtsVoice, TtsSegment, TtsParams } from '~/types/api';
import { useTaskStore } from './taskStore';

export const useTtsStore = defineStore('tts', () => {
    const uiStore = useUIStore();
    const settingsStore = useSettingsStore();
    const taskStore = useTaskStore();

    const allVoices = ref<TtsVoice[]>([]);
    const isLoadingVoices = ref(false);
    const isSynthesizing = ref(false);
    const isPlaying = ref(false);
    const textToSpeak = ref('你好，欢迎使用 MyNovelBot 的语音合成功能。');
    const selectedVoice = ref<string>('zh-CN-XiaoxiaoNeural');
    
    const params = ref<TtsParams>({
        rate: 50,
        volume: 50,
        pitch: 50
    });
    
    const audioDataUrl = ref<string | null>(null);
    let currentAudio: HTMLAudioElement | null = null;
    
    const playbackProgress = ref(0);
    const currentTime = ref(0);
    const duration = ref(0);

    const voices = computed(() => {
        const currentService = settingsStore.ttsServiceConfig.service;
        if (currentService === 'microsoft') {
            return allVoices.value.filter(v => v.Provider === 'Microsoft');
        }
        if (currentService === 'edge') {
            return allVoices.value.filter(v => v.Provider === 'Edge');
        }
        if (currentService === 'chat_tts') {
            return allVoices.value.filter(v => v.Provider === 'ChatTTS');
        }
        if (currentService === 'huggingface') {
            return allVoices.value.filter(v => v.Provider === 'HuggingFace');
        }
        if (currentService === 'coqui') {
            return allVoices.value.filter(v => v.Provider === 'Coqui');
        }
        if (currentService === 'aihorde') {
            return allVoices.value.filter(v => v.Provider === 'AIHorde');
        }
        return [];
    });
    
    const canSynthesize = computed(() => 
        !isSynthesizing.value && 
        textToSpeak.value.trim() !== '' && 
        selectedVoice.value !== '' &&
        voices.value.length > 0
    );
    
    const canPlay = computed(() => !isSynthesizing.value && !!audioDataUrl.value);

    const formatTime = (timeInSeconds: number) => {
        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = Math.floor(timeInSeconds % 60);
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    };
    const formattedCurrentTime = computed(() => formatTime(currentTime.value));
    const formattedDuration = computed(() => formatTime(duration.value));

    function generateAudioFilename(): string {
        const safeText = textToSpeak.value
            .trim()
            .substring(0, 30)
            .replace(/[\\/:\*\?"<>\|]/g, '_');
        return `${safeText || 'audio'}.mp3`;
    }

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
                await new Promise(resolve => setTimeout(resolve, 2000));
            } catch (error) {
                throw new Error(`轮询任务状态失败: ${error}`);
            }
        }
        throw new Error('任务超时');
    }

    function setupAudioListeners() {
        if (!currentAudio) return;
        currentAudio.onplay = () => { isPlaying.value = true; };
        currentAudio.onpause = () => { isPlaying.value = false; };
        currentAudio.onended = () => {
            isPlaying.value = false;
            playbackProgress.value = 100;
            currentTime.value = duration.value;
        };
        currentAudio.ontimeupdate = () => {
            if (!currentAudio) return;
            currentTime.value = currentAudio.currentTime;
            if (duration.value > 0) {
                playbackProgress.value = (currentAudio.currentTime / duration.value) * 100;
            }
        };
        currentAudio.onloadedmetadata = () => {
            if (!currentAudio) return;
            duration.value = currentAudio.duration;
        };
        currentAudio.onerror = () => {
            isPlaying.value = false;
            uiStore.setGlobalError("音频播放失败。");
        };
    }

    async function fetchVoices() {
        if (allVoices.value.length > 0) return;
        isLoadingVoices.value = true;
        try {
            const response = await apiService.getTtsVoices();
            allVoices.value = response.voices;
            if (voices.value.length > 0) {
                const currentServiceVoices = voices.value;
                const currentSelectedIsValid = currentServiceVoices.some(v => v.ShortName === selectedVoice.value);
                if (!currentSelectedIsValid && currentServiceVoices[0]) {
                    selectedVoice.value = currentServiceVoices[0].ShortName;
                }
            }
        } catch (error) {
            uiStore.setGlobalError(`获取TTS声音列表失败: ${error}`);
        } finally {
            isLoadingVoices.value = false;
        }
    }

    async function synthesizeBatch(segments: TtsSegment[], customParams?: Partial<TtsParams>) {
        if (segments.length === 0 || !settingsStore.userId) return;

        stop();
        isSynthesizing.value = true;
        uiStore.setGlobalError(null);
        audioDataUrl.value = null;

        const finalParams = { ...params.value, ...customParams };

        try {
            const taskResponse = await apiService.synthesizeTtsBatch(settingsStore.userId, segments, finalParams);
            taskStore.addTask({ id: taskResponse.task_id, type: 'tts_batch', status: 'processing' });
            const result = await pollTaskResult(taskResponse.task_id);
            audioDataUrl.value = result.audio_data;
            
            if (!audioDataUrl.value) {
                throw new Error("API did not return a valid audio data URL.");
            }
            
            currentAudio = new Audio(audioDataUrl.value);
            setupAudioListeners();
            
            return currentAudio;
        } catch (error) {
            uiStore.setGlobalError(`语音合成失败: ${error}`);
            return null;
        } finally {
            isSynthesizing.value = false;
        }
    }
    
    async function synthesize() {
        if (!canSynthesize.value) return;
        const audio = await synthesizeBatch([[textToSpeak.value, selectedVoice.value]]);
        audio?.play();
    }

    function togglePlayPause() {
        if (!currentAudio) return;
        if (isPlaying.value) {
            currentAudio.pause();
        } else {
            currentAudio.play();
        }
    }

    function stop() {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            playbackProgress.value = 0;
            currentTime.value = 0;
            isPlaying.value = false;
        }
    }

    function seek(percentage: number) {
        if (currentAudio && duration.value > 0) {
            currentAudio.currentTime = (percentage / 100) * duration.value;
        }
    }
    
    function cleanup() {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.onplay = null;
            currentAudio.onpause = null;
            currentAudio.onended = null;
            currentAudio.ontimeupdate = null;
            currentAudio.onloadedmetadata = null;
            currentAudio.onerror = null;
            currentAudio = null;
        }
    }

    return {
        allVoices,
        voices,
        isLoadingVoices,
        isSynthesizing,
        isPlaying,
        textToSpeak,
        selectedVoice,
        params,
        audioDataUrl,
        playbackProgress,
        currentTime,
        duration,
        formattedCurrentTime,
        formattedDuration,
        canSynthesize,
        canPlay,
        fetchVoices,
        synthesize,
        synthesizeBatch,
        togglePlayPause,
        stop,
        seek,
        cleanup,
        generateAudioFilename,
    };
});