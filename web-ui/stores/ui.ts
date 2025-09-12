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
  
  // [核心新增] 控制运行设置面板的状态
  const isRunSettingsPanelOpen = ref(false);

  function setGlobalError(message: string | null) {
    globalError.value = message;
    if (message) { setTimeout(() => { if (globalError.value === message) { globalError.value = null; } }, 5000); }
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
  
  // [核心新增] 切换运行设置面板的 Action
  function toggleRunSettingsPanel() {
    isRunSettingsPanelOpen.value = !isRunSettingsPanelOpen.value;
  }

  return {
    globalError,
    isStreamingEnabled,
    isAutoScrollEnabled,
    persistentState,
    isRunSettingsPanelOpen, // 导出状态
    setGlobalError,
    toggleSidebar,
    toggleSidebarSection,
    isSidebarSectionCollapsed,
    toggleRunSettingsPanel, // 导出方法
  };
});