import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { apiService } from '~/services/api';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import type { AllDataResponse, Character, Preset, WorldInfo, Filename, Group, DisplayOrder } from '~/types/api';
import { BOOTSTRAP_QUERY_KEY } from '~/composables/useAllData';

type DataType = 'character' | 'preset' | 'world_info' | 'group';
type BackendDataItem = Omit<Character, 'filename'> | Omit<Preset, 'filename'> | Omit<WorldInfo, 'filename'> | Omit<Group, 'filename'>;
type StringIndexedRecord = Record<string, any>;

export function useDataMutations() {
  const queryClient = useQueryClient();
  const settingsStore = useSettingsStore();
  const uiStore = useUIStore();

  // [核心优化] 移除复杂的乐观更新逻辑。
  // 现在，变更操作的流程更简单、更可靠：
  // 1. 调用 `mutationFn` 将变更发送到后端。
  // 2. 如果成功 (`onSuccess`)，就让相关的查询缓存失效 (`invalidateQueries`)。
  // 3. Vue Query 会自动在后台重新获取最新的数据，从而更新UI。
  // 4. 如果失败 (`onError`)，只显示一个错误提示。

  const createOrUpdateMutation = useMutation({
    mutationFn: (variables: { dataType: DataType; filename: Filename; data: BackendDataItem; isEditing: boolean }) => {
      if (!settingsStore.userId) throw new Error("用户未登录");
      return apiService.createOrUpdateData(settingsStore.userId, variables.dataType, variables.filename, variables.data, variables.isEditing)
    },
    onSuccess: () => {
      // [代码注释] 让所有分页数据和 Persona 数据的缓存失效，触发自动刷新。
      queryClient.invalidateQueries({ queryKey: ['paginatedData', 'character'] });
      queryClient.invalidateQueries({ queryKey: ['paginatedData', 'persona'] });
      queryClient.invalidateQueries({ queryKey: ['paginatedData', 'preset'] });
      queryClient.invalidateQueries({ queryKey: ['paginatedData', 'world_info'] });
      queryClient.invalidateQueries({ queryKey: ['paginatedData', 'group'] });
    },
    onError: (err: Error, newItem, context) => {
      uiStore.setGlobalError(`保存 '${(newItem.data as any).displayName || (newItem.data as any).name}' 失败: ${err.message}`);
    },
  });

  const renameMutation = useMutation({
    mutationFn: (variables: { dataType: DataType; oldFilename: Filename; newDisplayName: string }) => {
      if (!settingsStore.userId) throw new Error("用户未登录");
      return apiService.renameData(settingsStore.userId, variables.dataType, variables.oldFilename, variables.newDisplayName)
    },
    onSuccess: () => {
      // [代码注释] 重命名成功后，同样让所有可能受影响的数据缓存失效。
      queryClient.invalidateQueries({ queryKey: ['paginatedData'] });
    },
    onError: (err: Error, variables, context) => {
      uiStore.setGlobalError(`重命名 '${variables.oldFilename}' 失败: ${err.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (variables: { dataType: DataType; filename: Filename }) => {
      if (!settingsStore.userId) throw new Error("用户未登录");
      return apiService.deleteData(settingsStore.userId, variables.dataType, variables.filename)
    },
    onSuccess: () => {
      // [代码注释] 删除成功后，失效缓存。
      queryClient.invalidateQueries({ queryKey: ['paginatedData'] });
    },
    onError: (err: Error, itemToDelete, context) => {
      uiStore.setGlobalError(`删除 '${itemToDelete.filename}' 失败: ${err.message}`);
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
      // [代码注释] 拖拽排序成功后，直接让对应的分页数据失效即可，无需操作 bootstrap 数据。
      queryClient.invalidateQueries({ queryKey: ['paginatedData', variables.dataType.replace(/s$/, '')] });
    },
    onError: (err: Error, variables, context) => {
      uiStore.setGlobalError(`更新 ${variables.dataType} 顺序失败: ${err.message}`);
    },
  });
}