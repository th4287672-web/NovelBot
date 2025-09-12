// web-ui/stores/taskStore.ts

import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiService } from '~/services/api';
import type { TaskStatusResponse, PaginatedData, Character } from '~/types/api';
import { useQueryClient } from '@tanstack/vue-query';
import { BOOTSTRAP_QUERY_KEY, useInvalidateAllData } from '~/composables/useAllData';
import { useSettingsStore } from './settings';

type TaskStatus = 'pending' | 'processing' | 'success' | 'failed';

export interface Task {
  id: string;
  type: string;
  status: TaskStatus;
  progress: number;
  status_text: string | null;
  start_time: number | null;
  end_time: number | null;
  result?: any;
  error?: any;
}

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Record<string, Task>>({});
  const pollInterval = ref<number | null>(null);
  const queryClient = useQueryClient();
  const invalidateAllData = useInvalidateAllData();
  
  let settingsStore: ReturnType<typeof useSettingsStore> | null = null;
  try {
    settingsStore = useSettingsStore();
  } catch (e) {
    console.warn("taskStore: could not get settingsStore instance immediately.");
  }


  async function pollTaskResult(taskId: string, timeout = 120000): Promise<TaskStatusResponse> {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
        try {
            const task = await apiService.getTaskStatus(taskId);
            if (task.status === 'success' || task.status === 'failed') {
                return task;
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        } catch (error) {
            throw new Error(`轮询任务状态失败: ${error}`);
        }
    }
    throw new Error('任务超时');
  }

  function startPolling() {
      if (pollInterval.value) return;
      pollInterval.value = window.setInterval(async () => {
          const activeTasks = Object.values(tasks.value).filter(t => ['pending', 'processing'].includes(t.status));
          if (activeTasks.length > 0) {
              for (const task of activeTasks) {
                  try {
                      const updatedTask = await apiService.getTaskStatus(task.id);
                      const existingTask = tasks.value[task.id];
                      if (existingTask) {
                          Object.assign(existingTask, updatedTask);
                          if (['success', 'failed'].includes(updatedTask.status)) {
                              if (updatedTask.status === 'success') {
                                if (!settingsStore) settingsStore = useSettingsStore();
                                
                                if (updatedTask.task_type === 'upload_avatar' || updatedTask.task_type === 'upload_character_image') {
                                    console.log(`[TaskStore] Image upload task ${updatedTask.id} succeeded. Invalidating all data queries.`);
                                    invalidateAllData();
                                }
                              }
                              setTimeout(() => dismissTask(updatedTask.id), 10000);
                          }
                      }
                  } catch (e) {
                      console.error(`Failed to poll task ${task.id}`, e);
                      const existingTask = tasks.value[task.id];
                      if (existingTask) {
                        existingTask.status = 'failed';
                      }
                  }
              }
          } else {
              stopPolling();
          }
      }, 3000);
  }

  function stopPolling() {
      if (pollInterval.value) {
          clearInterval(pollInterval.value);
          pollInterval.value = null;
      }
  }

  function addTask(task: Omit<Task, 'progress' | 'status_text' | 'start_time' | 'end_time'>) {
    const fullTask: Task = {
        ...task,
        progress: 0,
        status_text: '已提交',
        start_time: Date.now() / 1000,
        end_time: null,
    };
    tasks.value[task.id] = fullTask;
    startPolling();

    if (task.status === 'success' || task.status === 'failed') {
      setTimeout(() => dismissTask(task.id), 10000);
    }
  }

  function dismissTask(taskId: string) {
    if (tasks.value[taskId]) {
      delete tasks.value[taskId];
    }
  }

  return {
    tasks,
    addTask,
    dismissTask,
    pollTaskResult,
  };
});