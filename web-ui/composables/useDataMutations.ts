import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { apiService } from '~/services/api';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import type { AllDataResponse, Character, Preset, WorldInfo, Filename, Group, DisplayOrder, PaginatedData } from '~/types/api';
import { BOOTSTRAP_QUERY_KEY } from '~/composables/useAllData';

type DataType = 'character' | 'preset' | 'world_info' | 'group' | 'persona';
type BackendDataItem = Omit<Character, 'filename'> | Omit<Preset, 'filename'> | Omit<WorldInfo, 'filename'> | Omit<Group, 'filename'>;
type StringIndexedRecord = Record<string, any>;

export function useDataMutations() {
  const queryClient = useQueryClient();
  const settingsStore = useSettingsStore();
  const uiStore = useUIStore();

  const createOrUpdateMutation = useMutation({
    mutationFn: (variables: { dataType: DataType; filename: Filename; data: BackendDataItem; isEditing: boolean }) => {
      if (!settingsStore.userId) throw new Error("用户未登录");
      const apiDataType = variables.dataType === 'persona' ? 'character' : variables.dataType;
      return apiService.createOrUpdateData(settingsStore.userId, apiDataType, variables.filename, variables.data, variables.isEditing)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['paginatedData'] });
    },
    onError: (err: Error, newItem, context) => {
      uiStore.setGlobalError(`保存 '${(newItem.data as any).displayName || (newItem.data as any).name}' 失败: ${err.message}`);
    },
  });

  const renameMutation = useMutation({
    mutationFn: (variables: { dataType: DataType; oldFilename: Filename; newDisplayName: string }) => {
      if (!settingsStore.userId) throw new Error("用户未登录");
      const apiDataType = variables.dataType === 'persona' ? 'character' : variables.dataType;
      return apiService.renameData(settingsStore.userId, apiDataType, variables.oldFilename, variables.newDisplayName)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['paginatedData'] });
    },
    onError: (err: Error, variables, context) => {
      uiStore.setGlobalError(`重命名 '${variables.oldFilename}' 失败: ${err.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (variables: { dataType: DataType; filename: Filename }) => {
      if (!settingsStore.userId) throw new Error("用户未登录");
      const apiDataType = variables.dataType === 'persona' ? 'character' : variables.dataType;
      return apiService.deleteData(settingsStore.userId, apiDataType, variables.filename)
    },
    onError: (err: Error, itemToDelete, context) => {
      if (!err.message.includes('[404]')) {
        uiStore.setGlobalError(`删除 '${itemToDelete.filename}' 失败: ${err.message}`);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['paginatedData'] });
    },
  });

  return { 
    createOrUpdate: createOrUpdateMutation.mutate,
    createOrUpdateAsync: createOrUpdateMutation.mutateAsync,
    rename: renameMutation.mutate,
    delete: deleteMutation.mutate,
  };
}

export function useDisplayOrderMutation() {
  const queryClient = useQueryClient();
  const settingsStore = useSettingsStore();
  const uiStore = useUIStore();

  return useMutation({
    mutationFn: (variables: { dataType: keyof DisplayOrder; order: Filename[] }) => {
      if (!settingsStore.userId) throw new Error("用户未登录");
      return apiService.updateDisplayOrder(settingsStore.userId, variables.dataType, variables.order)
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['paginatedData', variables.dataType.replace(/s$/, '')] });
    },
    onError: (err: Error, variables, context) => {
      uiStore.setGlobalError(`更新 ${variables.dataType} 顺序失败: ${err.message}`);
    },
  });
}