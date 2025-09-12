// web-ui/stores/dataManagementStore.ts

import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiService } from '~/services/api';
import { useSettingsStore } from './settings';
import { useUIStore } from './ui';
import { useInvalidateAllData } from '~/composables/useAllData';
import type { TaskSubmissionResponse, TaskStatusResponse } from '~/types/api';
import { useTaskStore } from './taskStore';

export const useDataManagementStore = defineStore('dataManagement', () => {
    const settingsStore = useSettingsStore();
    const uiStore = useUIStore();
    const taskStore = useTaskStore();
    const invalidateAllData = useInvalidateAllData();
    
    const isExporting = ref(false);
    const isImporting = ref(false);

    async function pollTaskResult(taskId: string): Promise<TaskStatusResponse> {
        while (true) {
            const task = await apiService.getTaskStatus(taskId);
            if (task.status === 'success' || task.status === 'failed') {
                return task;
            }
            await new Promise(resolve => setTimeout(resolve, 3000));
        }
    }

    async function exportData() {
        if (isExporting.value || !settingsStore.userId) return;
        isExporting.value = true;
        uiStore.setGlobalError("数据导出任务已提交至后台...");

        try {
            const taskResponse = await apiService.exportData(settingsStore.userId);
            taskStore.addTask({ id: taskResponse.task_id, type: 'export_data', status: 'processing' });
            
            const finalTask = await pollTaskResult(taskResponse.task_id);
            
            if (finalTask.status === 'success' && finalTask.result.download_url) {
                const a = document.createElement('a');
                a.href = finalTask.result.download_url;
                document.body.appendChild(a);
                a.click();
                a.remove();
                uiStore.setGlobalError("数据导出成功！下载已开始。");
            } else {
                throw new Error(finalTask.error?.error || '导出任务失败');
            }
        } catch (error) {
            uiStore.setGlobalError(`数据导出失败: ${error}`);
        } finally {
            isExporting.value = false;
        }
    }

    async function importData(file: File): Promise<void> {
        if (isImporting.value || !settingsStore.userId) return;
        isImporting.value = true;
        uiStore.setGlobalError("数据导入任务已提交至后台...");

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response: TaskSubmissionResponse = await apiService.importData(settingsStore.userId, formData);
            taskStore.addTask({ id: response.task_id, type: 'import_data', status: 'processing' });
            await invalidateAllData();
        } catch (error) {
            uiStore.setGlobalError(`数据导入失败: ${error}`);
        } finally {
            isImporting.value = false;
        }
    }

    return {
        isExporting,
        isImporting,
        exportData,
        importData,
    };
});