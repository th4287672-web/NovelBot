<template>
  <div class="h-full w-full">
    <ManagementLayout
      :is-loading="isLoading"
      :is-empty="filteredPresets.length === 0 && !searchQuery"
      @create="isCreateModalOpen = true"
    >
      <template #title>// AI 预设管理</template>
      <template #create-button-content>
        <div class="flex gap-4">
            <div class="relative">
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="搜索预设..." 
                class="bg-gray-700/60 rounded-sm border-2 border-gray-500/80 px-3 py-2 text-white transition-colors duration-200 focus:outline-none focus:bg-gray-700 w-48 text-sm"
              />
            </div>
            <input type="file" ref="fileInputRef" @change="handleFileSelected" accept=".json" class="hidden" />
            <button @click="triggerFileInput" class="btn btn-secondary">从文件导入</button>
            <button @click.stop="isImportModalOpen = true" class="btn btn-secondary">导入默认</button>
            <button class="btn btn-primary bg-green-600 hover:bg-green-500">创建新预设</button>
        </div>
      </template>
      
      <div v-if="filteredPresets.length > 0"
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
      >
        <div 
          v-for="(item, index) in filteredPresets" 
          :key="item.filename" 
          class="relative transition-all"
          :draggable="item.is_private"
          @dragstart="onDragStart($event, index)"
          @dragover.prevent="onDragOver($event)"
          @dragleave="onDragLeave($event)"
          @drop="onDrop($event, index)"
          @dragend="onDragEnd($event)"
        >
          <PresetsPresetCard
            :preset="item"
            :is-active="activePresetName === item.filename"
            @select="settingsStore.setActivePreset"
            @manage="openModulesModal"
            @delete="handleDeletePreset"
            @share="openShareModal"
          />
          <div v-if="item.is_private" class="drag-handle absolute top-2 right-2 p-1 cursor-grab text-gray-500 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 12a2 2 0 100-4 2 2 0 000 4zM12 10a2 2 0 11-4 0 2 2 0 014 0zM17 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
          </div>
        </div>
      </div>
      <div v-else-if="searchQuery" class="text-center py-20 text-gray-500">
        <p>未找到与 "{{ searchQuery }}" 匹配的预设。</p>
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

    <PresetsPresetEditModal
      v-if="isCreateModalOpen"
      @close="isCreateModalOpen = false"
      @create="handleCreatePreset"
    />

    <PresetsPresetModulesModal
      v-if="isModulesModalOpen"
      :preset="viewingModulesPreset"
      @close="closeModulesModal"
      @save="handleSavePreset"
      @delete="handleDeletePreset"
      @clone="handleClonePreset"
    />

     <CommonImportModal
        v-if="isImportModalOpen"
        data-type-name="预设"
        theme-color="green"
        :importable-items="importablePresets"
        @close="isImportModalOpen = false"
        @import="handleImport"
    />
    
    <CommunityShareModal
      v-if="sharingPreset"
      :item-to-share="sharingPreset"
      data-type="preset"
      @close="sharingPreset = null"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { usePresetStore } from '~/stores/presetStore';
import { useSettingsStore } from '~/stores/settings';
import { useDisplayOrderMutation } from '~/composables/useDataMutations';
import { useDraggable } from '~/composables/useDraggable';
import type { Preset, BackendPreset, Filename } from '~/types/api';
import { usePaginatedData } from '~/composables/useAllData';
import ManagementLayout from '~/components/common/ManagementLayout.vue';
import { useUIStore } from '~/stores/ui';
import CommunityShareModal from '~/components/community/CommunityShareModal.vue';
import CommonPagination from '~/components/common/Pagination.vue';

const presetStore = usePresetStore();
const settingsStore = useSettingsStore();
const uiStore = useUIStore();
const { mutate: updateOrder } = useDisplayOrderMutation();

const { importablePresets } = storeToRefs(presetStore);
const { isReady, activePresetName, userFullConfig } = storeToRefs(settingsStore);

const isCreateModalOpen = ref(false);
const isModulesModalOpen = ref(false);
const isImportModalOpen = ref(false);
const viewingModulesPreset = ref<Preset | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const isImporting = ref(false);
const searchQuery = ref('');
const sharingPreset = ref<Preset | null>(null);

const currentPage = ref(1);
const itemsPerPage = ref(20);

const { data, isLoading } = usePaginatedData<Preset>('preset', currentPage, itemsPerPage, searchQuery);

const localOrderedPresets = ref<Preset[]>([]);

const orderedPresetsComputed = computed(() => {
  if (!data.value?.items) return [];
  const order = userFullConfig.value?.display_order?.presets || [];
  const allItems = data.value.items;
  
  const sorted = [...allItems].sort((a, b) => {
    const indexA = order.indexOf(a.filename);
    const indexB = order.indexOf(b.filename);
    if (indexA === -1 && indexB === -1) {
      if (a.is_private && !b.is_private) return -1;
      if (!a.is_private && b.is_private) return 1;
      // [核心修复] 添加安全检查
      return (a.displayName || '').localeCompare(b.displayName || '');
    }
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });
  return sorted;
});


watch(orderedPresetsComputed, (newList) => {
  localOrderedPresets.value = newList;
}, { immediate: true });


const filteredPresets = computed(() => {
    return localOrderedPresets.value;
});

const { onDragStart, onDragOver, onDragLeave, onDrop, onDragEnd } = useDraggable(
  localOrderedPresets,
  (newList) => {
    localOrderedPresets.value = newList;
    const newOrder = newList.map(p => p.filename);
    updateOrder({ dataType: 'presets', order: newOrder });
  }
);


function openModulesModal(preset: Preset) {
  viewingModulesPreset.value = preset;
  isModulesModalOpen.value = true;
}

function openShareModal(preset: Preset) {
  sharingPreset.value = preset;
}

function closeModulesModal() {
    isModulesModalOpen.value = false;
    viewingModulesPreset.value = null;
    isImporting.value = false;
}

async function handleCreatePreset(presetData: BackendPreset) {
    const newFilename = await presetStore.createPreset(presetData);
    if (newFilename) {
        await settingsStore.setActivePreset(newFilename);
    }
    isCreateModalOpen.value = false;
}

async function handleSavePreset(preset: Preset) {
    if (isImporting.value) {
        const { filename, ...apiData } = preset;
        const newFilename = await presetStore.createPreset(apiData);
        if (newFilename) {
            await settingsStore.setActivePreset(newFilename);
        }
    } else {
        presetStore.updatePreset(preset);
    }
    closeModulesModal();
}

async function handleDeletePreset(preset?: Preset) {
  const presetToDelete = preset || viewingModulesPreset.value;
  if (presetToDelete && confirm(`你确定要删除预设 "${presetToDelete.displayName}" 吗？`)) {
    closeModulesModal();
    await presetStore.deletePreset(presetToDelete.filename);
  }
}

async function handleClonePreset() {
    const presetToClone = viewingModulesPreset.value;
    if (presetToClone) {
        closeModulesModal();
        await presetStore.clonePreset(presetToClone);
    }
}

function handleImport(keys: (string | number)[]) {
    const filenames = keys.filter((key): key is string => typeof key === 'string');
    presetStore.importPublicPresets(filenames);
    isImportModalOpen.value = false;
}

function triggerFileInput() {
    fileInputRef.value?.click();
}

function handleFileSelected(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files[0]) {
        const file = target.files[0];
        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target?.result as string;
            uiStore.setGlobalError('正在解析预设文件...');
            try {
                const parsedJson = JSON.parse(content);
                const importedPreset = presetStore.importPresetFromObject(parsedJson, file.name);
                if (importedPreset) {
                    isImporting.value = true;
                    openModulesModal(importedPreset);
                    uiStore.setGlobalError('预设已成功解析！请检查并保存。');
                }
            } catch (error) {
                const message = error instanceof Error ? error.message : '未知错误';
                uiStore.setGlobalError(`导入失败：${message}`);
            } finally {
                if (fileInputRef.value) {
                    fileInputRef.value.value = '';
                }
            }
        };
        reader.onerror = () => {
             uiStore.setGlobalError('读取文件失败！');
        }
        reader.readAsText(file);
    }
}
</script>