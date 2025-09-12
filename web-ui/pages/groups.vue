<template>
  <div class="h-full w-full">
    <ManagementLayout
      :is-loading="!isReady"
      :is-empty="filteredGroups.length === 0 && !searchQuery"
      @create="openModal('create')"
    >
      <template #title>// 群聊场景管理</template>
      <template #create-button-content>
        <div class="flex gap-4">
          <div class="relative">
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索场景..." 
              class="bg-gray-700/60 rounded-sm border-2 border-gray-500/80 px-3 py-2 text-white transition-colors duration-200 focus:outline-none focus:bg-gray-700 w-48 text-sm"
            />
          </div>
          <button class="btn btn-primary bg-indigo-600 hover:bg-indigo-500">创建新场景</button>
        </div>
      </template>
      
      <div v-if="filteredGroups.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div
          v-for="(group, index) in filteredGroups"
          :key="group.filename"
          class="relative transition-all"
          :draggable="true"
          @dragstart="onDragStart($event, index)"
          @dragover.prevent="onDragOver($event)"
          @dragleave="onDragLeave($event)"
          @drop="onDrop($event, index)"
          @dragend="onDragEnd($event)"
        >
          <GroupCard 
            :group="group"
            @edit="openModal('edit', group)"
            @delete="handleDeleteGroup"
          />
          <div class="drag-handle absolute -top-1 -right-1 p-1 cursor-grab text-gray-600 hover:text-white bg-gray-800 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M5 12a2 2 0 100-4 2 2 0 000 4zM12 10a2 2 0 11-4 0 2 2 0 014 0zM17 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
          </div>
        </div>
      </div>
       <div v-else-if="searchQuery" class="text-center py-20 text-gray-500">
        <p>未找到与 "{{ searchQuery }}" 匹配的场景。</p>
      </div>
    </ManagementLayout>

    <GroupEditModal
      v-if="isModalOpen"
      :mode="modalMode"
      :group="editingGroup"
      @close="closeModal"
      @save="handleSaveGroup"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useGroupStore } from '~/stores/groupStore';
import { useSettingsStore } from '~/stores/settings';
import { useDisplayOrderMutation } from '~/composables/useDataMutations';
import { useDraggable } from '~/composables/useDraggable';
import type { Group } from '~/types/api';
import ManagementLayout from '~/components/common/ManagementLayout.vue';
import GroupCard from '~/components/group/GroupCard.vue';
import GroupEditModal from '~/components/group/GroupEditModal.vue';

const groupStore = useGroupStore();
const settingsStore = useSettingsStore();
const { mutate: updateOrder } = useDisplayOrderMutation();

const { groups } = storeToRefs(groupStore);
const { isReady, userFullConfig } = storeToRefs(settingsStore);

const isModalOpen = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const editingGroup = ref<Group | null>(null);
const searchQuery = ref('');

const localOrderedGroups = ref<Group[]>([]);

const orderedGroupsComputed = computed(() => {
  const order = userFullConfig.value?.display_order?.groups || [];
  const allItems = Object.values(groups.value);

  return allItems.sort((a, b) => {
    const indexA = order.indexOf(a.filename);
    const indexB = order.indexOf(b.filename);
    if (indexA === -1 && indexB === -1) return a.name.localeCompare(b.name);
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });
});

const filteredGroups = computed(() => {
    if (!searchQuery.value) {
        return localOrderedGroups.value;
    }
    return localOrderedGroups.value.filter(g => 
        g.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        g.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    );
});

watch(orderedGroupsComputed, (newList) => {
  localOrderedGroups.value = newList;
}, { immediate: true });

const { onDragStart, onDragOver, onDragLeave, onDrop, onDragEnd } = useDraggable(
  localOrderedGroups,
  (newList) => {
    localOrderedGroups.value = newList;
    const newOrder = newList.map(g => g.filename);
    updateOrder({ dataType: 'groups', order: newOrder });
  }
);

function openModal(mode: 'create' | 'edit', group: Group | null = null) {
  modalMode.value = mode;
  editingGroup.value = group;
  isModalOpen.value = true;
}

function closeModal() {
  isModalOpen.value = false;
  editingGroup.value = null;
}

function handleSaveGroup(payload: { mode: 'create' | 'edit', data: Group }) {
  const isEditing = payload.mode === 'edit';
  const { filename, ...apiData } = payload.data;
  const nameForApi = isEditing ? filename : apiData.name;
  groupStore.createOrUpdateGroup(nameForApi, apiData, isEditing);
  closeModal();
}

function handleDeleteGroup(group: Group) {
  if (confirm(`确定要永久删除场景 "${group.name}" 吗？`)) {
    groupStore.deleteGroup(group.filename);
  }
}
</script>