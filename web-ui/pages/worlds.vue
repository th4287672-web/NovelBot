<template>
  <CommonPageLayout>
    <template #title>// 世界书管理</template>
    <template #actions>
      <div class="flex gap-4">
          <div class="relative">
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索世界书..." 
              class="bg-gray-700/60 rounded-sm border-2 border-gray-500/80 px-3 py-2 text-white transition-colors duration-200 focus:outline-none focus:bg-gray-700 w-48 text-sm"
            />
          </div>
          <button @click.stop="isImportModalOpen = true" class="btn btn-secondary">导入默认</button>
          <button @click="handleSyncAll" class="btn btn-secondary" :disabled="isSyncing">
              <svg v-if="isSyncing" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              <span>{{ isSyncing ? '同步中...' : '同步到 Google AI' }}</span>
          </button>
          <button @click="openModal('create')" class="btn btn-primary bg-yellow-600 hover:bg-yellow-500">创建新世界书</button>
      </div>
    </template>
    <ManagementLayout
      :is-loading="isLoading"
      :is-empty="!data?.items.length && !searchQuery"
      :is-contained="true"
    >
      <div v-if="data?.items.length" class="space-y-2">
        <div 
          v-for="(item, index) in localOrderedWorlds" 
          :key="item.filename"
          class="p-3 flex items-center justify-between bg-gray-800/60 rounded-sm border border-gray-600/50 relative transition-all"
          :draggable="true"
          @dragstart="onDragStart($event, index)"
          @dragover.prevent="onDragOver($event)"
          @dragleave="onDragLeave($event)"
          @drop="onDrop($event, index)"
          @dragend="onDragEnd($event)"
        >
          <div class="flex items-center flex-grow min-w-0">
            <div class="drag-handle cursor-grab text-gray-500 hover:text-white mr-3">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 12a2 2 0 100-4 2 2 0 000 4zM12 10a2 2 0 11-4 0 2 2 0 014 0zM17 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
            </div>
            <input 
              type="checkbox"
              :id="`world-toggle-${item.filename}`"
              :checked="sessionActiveWorlds.includes(item.filename)"
              @change="worldStore.toggleSessionWorld(item.filename)"
              class="form-checkbox h-5 w-5 bg-gray-700 border-gray-500 rounded text-yellow-500 focus:ring-yellow-500/50 cursor-pointer shrink-0"
              title="在当前会话中激活/停用"
            />
            <label :for="`world-toggle-${item.filename}`" class="ml-4 flex-grow cursor-pointer truncate">
              <span class="font-semibold" :class="sessionActiveWorlds.includes(item.filename) ? 'text-yellow-300' : 'text-white'">{{ item.name }}</span>
            </label>
          </div>
          <div class="flex items-center space-x-3 shrink-0 ml-4">
            <button v-if="item.is_private" @click="openShareModal(item)" class="btn btn-secondary !px-3 !py-1 text-xs bg-indigo-600/20 hover:bg-indigo-500/30 border-indigo-500/50 text-indigo-300">分享</button>
            <button v-if="item.is_private" @click="openModal('edit', item)" class="btn btn-secondary text-xs !px-3 !py-1">编辑</button>
            <button @click="handleDeleteWorldBook(item)" class="btn btn-danger text-xs !px-3 !py-1">删除</button>
          </div>
        </div>
      </div>
       <div v-else-if="searchQuery" class="text-center py-20 text-gray-500">
        <p>未找到与 "{{ searchQuery }}" 匹配的世界书。</p>
      </div>
      <template #footer>
        <div class="mt-4 flex justify-center">
            <CommonPagination 
                :current-page="currentPage" 
                :total-pages="data?.total_pages || 1"
                @page-change="currentPage = $event"
            />
        </div>
      </template>
    </ManagementLayout>

    <WorldInfoModal
      v-if="isModalOpen"
      :mode="modalMode"
      :filename="editingBook?.filename ?? null"
      @close="closeModal"
      @save="handleSaveWorldBook"
    />
     <CommonImportModal
        v-if="isImportModalOpen"
        data-type-name="世界书"
        theme-color="yellow"
        :importable-items="importableWorlds"
        @close="isImportModalOpen = false"
        @import="handleImport"
    />
    <CommunityShareModal
      v-if="sharingWorldBook"
      :item-to-share="sharingWorldBook"
      data-type="world_info"
      @close="sharingWorldBook = null"
    />
  </CommonPageLayout>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useWorldStore } from '~/stores/worldStore';
import { useSettingsStore } from '~/stores/settings';
import { useDisplayOrderMutation } from '~/composables/useDataMutations';
import { useDraggable } from '~/composables/useDraggable';
import { storeToRefs } from 'pinia';
import type { WorldInfo, Filename, Preset } from '~/types/api';
import { usePaginatedData } from '~/composables/useAllData';
import CommonPageLayout from '~/components/common/PageLayout.vue';
import ManagementLayout from '~/components/common/ManagementLayout.vue';
import WorldInfoModal from '~/components/world_info/WorldInfoModal.vue';
import CommunityShareModal from '~/components/community/CommunityShareModal.vue';
import CommonPagination from '~/components/common/Pagination.vue';

const worldStore = useWorldStore();
const settingsStore = useSettingsStore();
const { mutate: updateOrder } = useDisplayOrderMutation();

const { importableWorlds } = storeToRefs(worldStore);
const { sessionActiveWorlds, isReady, userFullConfig } = storeToRefs(settingsStore);

const isModalOpen = ref(false);
const isImportModalOpen = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const editingBook = ref<WorldInfo | null>(null);
const isSyncing = ref(false);
const searchQuery = ref('');
const sharingWorldBook = ref<WorldInfo | null>(null);
const currentPage = ref(1);
const itemsPerPage = ref(20);

const { data, isLoading } = usePaginatedData<WorldInfo>('world_info', currentPage, itemsPerPage, searchQuery);

const localOrderedWorlds = ref<WorldInfo[]>([]);

const orderedWorldsComputed = computed(() => {
  if (!data.value?.items) return [];
  const order = userFullConfig.value?.display_order?.worlds || [];
  const allItems = data.value.items;

  return [...allItems].sort((a, b) => {
    const indexA = order.indexOf(a.filename);
    const indexB = order.indexOf(b.filename);
    if (indexA === -1 && indexB === -1) {
      return (a.name || '').localeCompare(b.name || '');
    }
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });
});

watch(orderedWorldsComputed, (newList) => {
    localOrderedWorlds.value = newList;
}, { immediate: true });


const { onDragStart, onDragOver, onDragLeave, onDrop, onDragEnd } = useDraggable(
  localOrderedWorlds,
  (newList) => {
    localOrderedWorlds.value = newList;
    const newOrder = newList.map(w => w.filename);
    updateOrder({ dataType: 'worlds', order: newOrder });
  }
);

function openModal(mode: 'create' | 'edit', book: WorldInfo | null = null) {
  modalMode.value = mode;
  editingBook.value = book;
  isModalOpen.value = true;
}

function openShareModal(book: WorldInfo) {
  sharingWorldBook.value = book;
}

function closeModal() {
  isModalOpen.value = false;
  editingBook.value = null;
}

function handleSaveWorldBook(payload: { mode: 'create' | 'edit', filename: Filename | null, data: Omit<WorldInfo, 'filename'> }) {
  const isEditing = payload.mode === 'edit';
  const apiData = payload.data;
  const nameForApi = isEditing ? payload.filename : apiData.name;
  if(!nameForApi) return;
  worldStore.createOrUpdateWorldBook(nameForApi, apiData, isEditing);
  closeModal();
}

async function handleDeleteWorldBook(book: WorldInfo) {
  if (confirm(`确定要永久删除世界书 "${book.name}" 吗？`)) {
    await worldStore.deleteWorldBook(book.filename);
  }
}

function handleImport(keys: (string | number)[]) {
    const filenames = keys.filter((key): key is string => typeof key === 'string');
    worldStore.importPublicWorlds(filenames);
    isImportModalOpen.value = false;
}

async function handleSyncAll() {
    if (!confirm(`确定要将所有私有世界书同步到 Google AI 吗？这会创建或更新云端的知识库，可能会产生少量费用。`)) return;
    
    isSyncing.value = true;
    try {
        const privateWorlds = (data.value?.items || []).filter(w => w.is_private);
        await worldStore.syncWorldBooksToGoogle(privateWorlds);
    } finally {
        isSyncing.value = false;
    }
}
</script>