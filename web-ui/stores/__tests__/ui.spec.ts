import { describe, it, expect, beforeEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useUIStore } from '~/stores/ui';

describe('UI Store 单元测试', () => {
  
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it('setGlobalError action 应该能设置错误信息', () => {
    const uiStore = useUIStore();
    const errorMessage = '这是一个测试错误';

    expect(uiStore.globalError).toBe(null);
    uiStore.setGlobalError(errorMessage);
    expect(uiStore.globalError).toBe(errorMessage);
  });
  
  it('toggleSidebar action 应该能正确切换侧边栏的折叠状态', () => {
    const uiStore = useUIStore();
    
    uiStore.persistentState.isSidebarCollapsed = false;
    expect(uiStore.persistentState.isSidebarCollapsed).toBe(false);

    uiStore.toggleSidebar();
    expect(uiStore.persistentState.isSidebarCollapsed).toBe(true);

    uiStore.toggleSidebar();
    expect(uiStore.persistentState.isSidebarCollapsed).toBe(false);
  });

  it('toggleSidebarSection action 应该能正确添加和移除折叠的区域ID', () => {
    const uiStore = useUIStore();
    const sectionId = 'test-section';

    expect(uiStore.isSidebarSectionCollapsed(sectionId)).toBe(false);

    uiStore.toggleSidebarSection(sectionId);
    expect(uiStore.isSidebarSectionCollapsed(sectionId)).toBe(true);
    expect(uiStore.persistentState.collapsedSidebarSections).toContain(sectionId);

    uiStore.toggleSidebarSection(sectionId);
    expect(uiStore.isSidebarSectionCollapsed(sectionId)).toBe(false);
    expect(uiStore.persistentState.collapsedSidebarSections).not.toContain(sectionId);
  });
});