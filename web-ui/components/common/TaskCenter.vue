<template>
  <div class="fixed bottom-4 right-4 z-[100] w-80 space-y-2">
    <transition-group name="list">
      <div
        v-for="task in activeTasks"
        :key="task.id"
        class="p-3 rounded-lg shadow-lg border"
        :class="taskStatusStyles[task.status].bg"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div :class="taskStatusStyles[task.status].iconContainer">
              <svg v-if="task.status === 'processing'" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              <span v-else>{{ taskStatusStyles[task.status].icon }}</span>
            </div>
            <div>
              <p class="text-sm font-semibold text-white">{{ taskTitles[task.type] || '后台任务' }}</p>
              <p class="text-xs" :class="taskStatusStyles[task.status].text">{{ taskStatusText[task.status] }}</p>
            </div>
          </div>
          <button @click="taskStore.dismissTask(task.id)" class="text-gray-300 hover:text-white">&times;</button>
        </div>
        <div v-if="task.status === 'processing' && task.progress > 0" class="mt-2">
            <div class="w-full bg-gray-900/50 rounded-full h-1.5">
                <div class="bg-blue-400 h-1.5 rounded-full" :style="{ width: `${task.progress}%` }"></div>
            </div>
            <p class="text-xs text-blue-200 mt-1 text-right">{{ task.status_text }}... ({{ task.progress }}%)</p>
        </div>
        <p v-if="task.status === 'failed' && task.error" class="mt-2 text-xs text-red-200 break-all">{{ task.error.error }}</p>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useTaskStore } from '~/stores/taskStore';

const taskStore = useTaskStore();

const activeTasks = computed(() => Object.values(taskStore.tasks));

const taskTitles: Record<string, string> = {
  txt2img: '文生图',
  img2img: '图生图',
  tts_batch: '批量语音合成',
  upload_avatar: '上传头像',
  upload_character_image: '上传角色图片',
  import_data: '数据导入',
};

const taskStatusText: Record<string, string> = {
  pending: '等待中...',
  processing: '处理中...',
  success: '已完成',
  failed: '失败',
};

const taskStatusStyles = {
  pending: { bg: 'bg-gray-700 border-gray-600', text: 'text-gray-300', icon: '⏳', iconContainer: 'bg-gray-500/50 p-1.5 rounded-full' },
  processing: { bg: 'bg-blue-800 border-blue-600', text: 'text-blue-200', icon: '', iconContainer: 'p-1.5' },
  success: { bg: 'bg-green-800 border-green-600', text: 'text-green-200', icon: '✅', iconContainer: 'bg-green-500/50 p-1.5 rounded-full' },
  failed: { bg: 'bg-red-800 border-red-600', text: 'text-red-200', icon: '❌', iconContainer: 'bg-red-500/50 p-1.5 rounded-full' },
};
</script>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
