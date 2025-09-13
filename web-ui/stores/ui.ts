import { defineStore } from 'pinia';
import { ref, watch } from 'vue';
import { useStorage } from '@vueuse/core';

interface PersistentUIState {
  isSidebarCollapsed: boolean;
  collapsedSidebarSections: string[];
}

const usePersistentState = () => useStorage<PersistentUIState>('mynovelbot_ui_state', {
    isSidebarCollapsed: false,
    collapsedSidebarSections: [],
});

export const useUIStore = defineStore('ui', () => {
  const globalError = ref<string | null>(null);
  const isStreamingEnabled = ref<boolean>(true);
  const isAutoScrollEnabled = ref<boolean>(true);
  
  const persistentState = usePersistentState();
  
  const isRunSettingsPanelOpen = ref(false);

  let errorTimer: number | null = null;

  function setGlobalError(message: string | null, timeout: number = 5000) {
    if (errorTimer) {
      clearTimeout(errorTimer);
    }
    globalError.value = message;
    if (message) {
      errorTimer = window.setTimeout(() => {
        if (globalError.value === message) {
          globalError.value = null;
        }
      }, timeout);
    }
  }
  
  const toggleSidebar = () => { persistentState.value.isSidebarCollapsed = !persistentState.value.isSidebarCollapsed; };

  function toggleSidebarSection(sectionId: string) {
    const index = persistentState.value.collapsedSidebarSections.indexOf(sectionId);
    if (index > -1) {
      persistentState.value.collapsedSidebarSections.splice(index, 1);
    } else {
      persistentState.value.collapsedSidebarSections.push(sectionId);
    }
  }

  function isSidebarSectionCollapsed(sectionId: string): boolean {
    return persistentState.value.collapsedSidebarSections.includes(sectionId);
  }
  
  function toggleRunSettingsPanel() {
    isRunSettingsPanelOpen.value = !isRunSettingsPanelOpen.value;
  }

  return {
    globalError,
    isStreamingEnabled,
    isAutoScrollEnabled,
    persistentState,
    isRunSettingsPanelOpen,
    setGlobalError,
    toggleSidebar,
    toggleSidebarSection,
    isSidebarSectionCollapsed,
    toggleRunSettingsPanel,
  };
});