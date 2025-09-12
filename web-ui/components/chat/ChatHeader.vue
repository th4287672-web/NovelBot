<template>
  <div class="p-3 border-b border-gray-700 bg-gray-800/50 flex items-center justify-between relative shrink-0">
    <!-- 左侧空白占位，用于平衡布局 -->
    <div class="w-1/4"></div>

    <!-- 中间：会话标题 -->
    <button 
      @click="isModalOpen = true" 
      class="text-center hover:bg-gray-700 p-2 rounded-md transition-colors w-1/2"
      :disabled="!isReady"
    >
      <h1 v-if="activeCharacter" class="text-lg font-semibold text-gray-200 truncate">
        {{ activeCharacter.displayName }}
      </h1>
      <p v-if="activeSession" class="text-xs text-gray-400 mt-1 truncate">
        {{ activeSession.title }}
      </p>
      <p v-else-if="isReady && !activeCharacter" class="text-lg font-semibold text-gray-500">
        请选择一个角色开始聊天
      </p>
       <p v-else class="text-lg font-semibold text-gray-500 animate-pulse">
        正在加载...
      </p>
    </button>
    
    <!-- 右侧：运行设置按钮 -->
    <div class="w-1/4 flex justify-end">
        <button 
            @click="uiStore.toggleRunSettingsPanel"
            title="运行设置"
            class="btn btn-secondary !p-2"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 16v-2m0-8v-2m0 12V10m6 6h2m-16 0h2m8 0h2M4 12H2m16 0h2M12 8a2 2 0 100-4 2 2 0 000 4zm0 12a2 2 0 100-4 2 2 0 000 4zm8-6a2 2 0 100-4 2 2 0 000 4zm-16 0a2 2 0 100-4 2 2 0 000 4z" /></svg>
        </button>
    </div>

    <ClientOnly>
      <SessionSelectionModal
        v-if="isModalOpen"
        :active-session-id="activeSessionId"
        @close="isModalOpen = false"
        @select-session="handleSelectSession"
        @create-new-session="handleCreateNewSession"
      />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useCharacterStore } from '~/stores/characterStore';
import { useSessionStore } from '~/stores/sessionStore';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui'; // [核心新增]
import SessionSelectionModal from './SessionSelectionModal.vue';
import type { SessionID, Filename } from '~/types/api';

const characterStore = useCharacterStore();
const sessionStore = useSessionStore();
const settingsStore = useSettingsStore();
const uiStore = useUIStore(); // [核心新增]
const router = useRouter();

const { activeCharacter } = storeToRefs(characterStore);
const { activeSessionId, sessionsByChar } = storeToRefs(sessionStore);
const { isReady } = storeToRefs(settingsStore);

const isModalOpen = ref(false);

const sessionsForCurrentChar = computed(() => {
  if (activeCharacter.value) {
    return sessionsByChar.value[activeCharacter.value.filename] || [];
  }
  return [];
});

const activeSession = computed(() => {
  return sessionsForCurrentChar.value.find(s => s.id === activeSessionId.value);
});

async function handleSelectSession(payload: { characterFilename: Filename, sessionId: SessionID }) {
  isModalOpen.value = false;
  
  if (settingsStore.activeCharacterKey !== payload.characterFilename) {
    await characterStore.setActiveCharacter(payload.characterFilename);
  }
  
  if (sessionStore.activeSessionId !== payload.sessionId) {
    await sessionStore.setActiveSession(payload.sessionId);
  }
  
  router.push(`/chat/${payload.sessionId}`);
}

async function handleCreateNewSession(characterFilename: Filename) {
  isModalOpen.value = false;

  if (settingsStore.activeCharacterKey !== characterFilename) {
    await characterStore.setActiveCharacter(characterFilename);
  }
  
  const newSession = await sessionStore.createNewSession(characterFilename);
  if (newSession) {
    router.push(`/chat/${newSession.id}`);
  }
}
</script>