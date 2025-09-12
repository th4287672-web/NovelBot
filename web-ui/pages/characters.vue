<template>
  <div class="h-full w-full">
    <ManagementLayout
      :is-loading="isLoading"
      :is-empty="!data?.items.length && !searchQuery"
      @create="openModal('create')"
    >
      <template #title>// 角色卡管理</template>
      <template #create-button-content>
        <div class="flex gap-4 items-center">
            <!-- [核心新增] 视图切换 -->
            <div class="flex items-center bg-gray-700/60 rounded-md p-1">
              <button @click="viewType = 'grid'" class="p-1.5 rounded-md transition-colors" :class="{'bg-cyan-600 text-white': viewType === 'grid'}"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg></button>
              <button @click="viewType = 'list'" class="p-1.5 rounded-md transition-colors" :class="{'bg-cyan-600 text-white': viewType === 'list'}"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" /></svg></button>
            </div>
            <div class="relative">
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="搜索角色..." 
                class="bg-gray-700/60 rounded-sm border-2 border-gray-500/80 px-3 py-2 text-white transition-colors duration-200 focus:outline-none focus:bg-gray-700 w-48 text-sm"
              />
            </div>
            <button @click.stop="isImportModalOpen = true" class="btn btn-secondary">导入默认</button>
            <button class="btn btn-primary bg-cyan-600 hover:bg-cyan-500">创建新角色</button>
        </div>
      </template>
      
      <!-- [核心新增] 根据 viewType 切换布局 -->
      <div v-if="data?.items.length" :class="viewType === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' : 'space-y-3'">
        <div
          v-for="(char, index) in data.items"
          :key="char.filename"
          class="relative transition-all"
          :draggable="true"
          @dragstart="onDragStart($event, index)"
          @dragover.prevent="onDragOver($event)"
          @dragleave="onDragLeave($event)"
          @drop="onDrop($event, index)"
          @dragend="onDragEnd($event)"
        >
          <CharacterCard v-if="viewType === 'grid'"
            :character="char"
            :is-active="activeCharacterKey === char.filename"
            @select="handleSelectCharacter"
            @edit="openModal('edit', char)"
            @delete="handleDeleteCharacter"
            @share="openShareModal"
          />
          <CharacterListItem v-else
            :character="char"
            :is-active="activeCharacterKey === char.filename"
            @select="handleSelectCharacter"
            @edit="openModal('edit', char)"
            @delete="handleDeleteCharacter"
            @share="openShareModal"
          />
          <div v-if="viewType === 'grid'" class="drag-handle absolute -top-1 -right-1 p-1 cursor-grab text-gray-600 hover:text-white bg-gray-800 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M5 12a2 2 0 100-4 2 2 0 000 4zM12 10a2 2 0 11-4 0 2 2 0 014 0zM17 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
          </div>
        </div>
      </div>
       <div v-else-if="searchQuery" class="text-center py-20 text-gray-500">
        <p>未找到与 "{{ searchQuery }}" 匹配的角色。</p>
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

    <CharacterEditModal
      v-if="isModalOpen"
      :mode="modalMode"
      :character="editingCharacter"
      @close="closeModal"
      @save="handleSaveCharacter"
    />

    <CommonImportModal
        v-if="isImportModalOpen"
        data-type-name="角色"
        theme-color="cyan"
        :importable-items="importableCharacters"
        @close="isImportModalOpen = false"
        @import="handleImport"
    />
    
    <CommunityShareModal
      v-if="sharingCharacter"
      :item-to-share="sharingCharacter"
      data-type="character"
      @close="sharingCharacter = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useCharacterStore } from '~/stores/characterStore';
import { useSettingsStore } from '~/stores/settings';
import { useDisplayOrderMutation } from '~/composables/useDataMutations';
import { useDraggable } from '~/composables/useDraggable';
import { usePaginatedData } from '~/composables/useAllData';
import type { Character, Filename, BackendCharacter } from '~/types/api';
import ManagementLayout from '~/components/common/ManagementLayout.vue';
import CharacterCard from '~/components/character/CharacterCard.vue';
import CharacterListItem from '~/components/character/CharacterListItem.vue';
import CharacterEditModal from '~/components/character/CharacterEditModal.vue';
import CommunityShareModal from '~/components/community/CommunityShareModal.vue';
import { useStorage } from '@vueuse/core';
import CommonPagination from '~/components/common/Pagination.vue';

const characterStore = useCharacterStore();
const settingsStore = useSettingsStore();
const { mutate: updateOrder } = useDisplayOrderMutation();

const { importableCharacters } = storeToRefs(characterStore);
const { activeCharacterKey, isReady } = storeToRefs(settingsStore);

const isModalOpen = ref(false);
const isImportModalOpen = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const editingCharacter = ref<Character | null>(null);
const searchQuery = ref(''); 
const sharingCharacter = ref<Character | null>(null);
const viewType = useStorage<'grid' | 'list'>('mynovelbot-character-view', 'grid');

// [核心重构] 分页状态
const currentPage = ref(1);
const itemsPerPage = ref(20);

const { data, isLoading } = usePaginatedData<Character>('character', currentPage, itemsPerPage, searchQuery);

const { onDragStart, onDragOver, onDragLeave, onDrop, onDragEnd } = useDraggable(
  computed({
    get: () => data.value?.items || [],
    set: (newList) => { /* useDraggable will call the update callback */ }
  }),
  (newList) => { 
    const newOrder = newList.map(p => p.filename);
    updateOrder({ dataType: 'characters', order: newOrder });
  }
);

function openModal(mode: 'create' | 'edit', character: Character | null = null) {
  modalMode.value = mode;
  editingCharacter.value = character;
  isModalOpen.value = true;
}

function openShareModal(character: Character) {
  sharingCharacter.value = character;
}

function closeModal() {
  isModalOpen.value = false;
  editingCharacter.value = null;
}

function handleSelectCharacter(filename: Filename) {
  characterStore.setActiveCharacter(filename);
}

function handleSaveCharacter(payload: { mode: 'create' | 'edit', data: Character }) {
  const isEditing = payload.mode === 'edit';
  const { filename, ...apiData } = payload.data;
  const finalApiData: BackendCharacter = { ...apiData, is_user_persona: false };
  const nameForApi = isEditing ? filename : apiData.displayName;
  
  characterStore.createOrUpdateCharacter(nameForApi, finalApiData, isEditing);
  
  if (!isEditing) {
    currentPage.value = 1; 
  }
  closeModal();
}

function handleDeleteCharacter(character: Character) {
  if (confirm(`确定要永久删除角色 "${character.displayName}" 吗？`)) {
    characterStore.deleteCharacter(character.filename);
  }
}

function handleImport(keys: (string | number)[]) {
    const filenames = keys.filter((key): key is string => typeof key === 'string');
    characterStore.importPublicCharacters(filenames);
    isImportModalOpen.value = false;
}
</script>