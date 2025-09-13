<template>
  <div class="h-full w-full p-6 flex flex-col">
    <header class="flex justify-between items-center shrink-0 mb-6">
      <h1 class="text-2xl font-bold">// 任务中心</h1>
      <button @click="fetchTasks" :disabled="isLoading" class="btn btn-secondary">
        刷新列表
      </button>
    </header>

    <main class="flex-grow min-h-0 overflow-y-auto pr-2">
      <div v-if="isLoading" class="flex items-center justify-center h-full">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
      </div>
      <div v-else-if="tasks.length === 0" class="text-center py-20 text-gray-500">
        <p class="text-lg">没有任务记录。</p>
        <p class="mt-2">当您执行耗时操作时，任务会出现在这里。</p>
      </div>
      <div v-else class="space-y-3">
        <div 
          v-for="task in tasks"
          :key="task.id"
        >
          <div v-if="task.status">
            <div
              class="p-4 bg-gray-800/60 rounded-lg border-l-4"
              :class="taskStatusStyles[task.status].border"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-semibold text-white">
                    {{ taskTitles[task.task_type] || '未知任务' }}
                  </p>
                  <p class="text-xs text-gray-400 font-mono" :title="task.id">{{ task.id.substring(0, 8) }}</p>
                </div>
                <div class="text-right">
                  <p class="text-sm font-semibold" :class="taskStatusStyles[task.status].text">
                    {{ taskStatusText[task.status] }}
                  </p>
                  <p class="text-xs text-gray-500">
                    {{ formatTimestamp(task.updated_at) }}
                  </p>
                </div>
              </div>
              <div v-if="task.status === 'processing'" class="mt-3">
                <div class="w-full bg-gray-700 rounded-full h-2.5">
                  <div class="bg-blue-500 h-2.5 rounded-full" :style="{ width: `${task.progress}%` }"></div>
                </div>
                <p class="text-xs text-blue-300 mt-1 text-right">{{ task.status_text }} ({{ task.progress }}%) - {{ getElapsedTime(task) }}</p>
              </div>
               <div v-if="task.status === 'failed' && task.error" class="mt-2 text-xs text-red-300 bg-red-900/20 p-2 rounded">
                {{ task.error.error }}
              </div>
              
              <div v-if="task.status === 'success' && task.result?.image_url" class="mt-3">
                <img 
                     :key="getResourceUrl({ image: task.result.image_url }) || task.id"
                     :src="getResourceUrl({ image: task.result.image_url })!"
                     class="max-h-48 rounded-md cursor-pointer" 
                     @click="previewImage(getResourceUrl({ image: task.result.image_url })!)"
                     :alt="`Task ${task.id} result`"
                />
              </div>

            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { apiService } from '~/services/api';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import type { TaskStatusResponse } from '~/types/api';
import { getResourceUrl } from '~/utils/urlBuilder';

const settingsStore = useSettingsStore();
const uiStore = useUIStore();

const tasks = ref<TaskStatusResponse[]>([]);
const isLoading = ref(true);
let pollInterval: number | null = null;

watch(tasks, (newTasks) => {
    const successTasks = newTasks.filter(t => t.status === 'success');
    if (successTasks.length > 0) {
        successTasks.forEach(task => {
            console.log(`[DIAG][TaskViewer] Task ${task.id} (${task.task_type}) succeeded with result:`, task.result);
        });
    }
}, { deep: true });

const taskTitles: Record<string, string> = {
  txt2img: '文生图',
  img2img: '图生图',
  tts_batch: '批量语音合成',
  upload_avatar: '上传头像',
  upload_character_image: '上传角色图片',
  import_data: '数据导入',
  export_data: '数据导出',
};

const taskStatusText: Record<string, string> = {
  pending: '等待中',
  processing: '处理中',
  success: '成功',
  failed: '失败',
};

const taskStatusStyles = {
  pending: { border: 'border-gray-500', text: 'text-gray-300' },
  processing: { border: 'border-blue-500', text: 'text-blue-300' },
  success: { border: 'border-green-500', text: 'text-green-300' },
  failed: { border: 'border-red-500', text: 'text-red-300' },
};

async function fetchTasks() {
    if (!settingsStore.userId || settingsStore.isAnonymous) {
        tasks.value = [];
        isLoading.value = false;
        return;
    };
    isLoading.value = true;
    try {
        tasks.value = await apiService.getAllTasksForUser(settingsStore.userId, 100, 0);
    } catch (e) {
        uiStore.setGlobalError(`获取任务列表失败: ${e}`);
    } finally {
        isLoading.value = false;
    }
}

function formatTimestamp(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleString();
}

function getElapsedTime(task: TaskStatusResponse): string {
    if (!task.start_time) return '';
    const end = task.end_time || Date.now() / 1000;
    const duration = end - task.start_time;
    return `${duration.toFixed(2)}s`;
}

function previewImage(url: string) {
    window.open(url, '_blank');
}

onMounted(() => {
    fetchTasks();
    pollInterval = window.setInterval(fetchTasks, 15000);
});

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval);
});
</script>