import { defineStore } from 'pinia';
import { ref, watch, computed } from 'vue';
import type { Group, Filename, BackendGroup } from '~/types/api';
import { usePaginatedData } from '~/composables/useAllData';
import { useDataMutations } from '~/composables/useDataMutations';
import { useQueryClient } from '@tanstack/vue-query';
import { useSettingsStore } from './settings';

export const useGroupStore = defineStore('group', () => {
    const { createOrUpdate, delete: deleteData } = useDataMutations();
    const queryClient = useQueryClient();
    const settingsStore = useSettingsStore();
    
    const groups = computed<Record<string, Group>>(() => {
        const paginatedQueries = queryClient.getQueryCache().findAll({ queryKey: ['paginatedData', 'group'] });
        const allGroupsMap = new Map<Filename, Group>();

        paginatedQueries.forEach(query => {
            const pageData = query.state.data as any;
            if (pageData && pageData.items) {
                pageData.items.forEach((group: Group) => {
                    allGroupsMap.set(group.filename, group);
                });
            }
        });
        return Object.fromEntries(allGroupsMap);
    });

    function createOrUpdateGroup(filename: Filename, groupData: Omit<Group, 'filename'>, isEditing: boolean) {
        createOrUpdate({
            dataType: 'group',
            filename: filename,
            data: groupData,
            isEditing: isEditing,
        });
    }

    function deleteGroup(filename: string) {
        deleteData({ dataType: 'group', filename: filename });
    }

    return {
        groups,
        createOrUpdateGroup,
        deleteGroup,
    };
});