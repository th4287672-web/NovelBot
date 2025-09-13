import { useSessionStore } from '~/stores/sessionStore';
import { useSettingsStore } from '~/stores/settings';

export default defineNuxtRouteMiddleware(async (to, from) => {
  if (process.server) return;

  if (to.path === '/chat') {
    const settingsStore = useSettingsStore();
    const sessionStore = useSessionStore();
    
    // 等待 Pinia store 和 vue-query 初始化完成
    await settingsStore.hydrationPromise;
    
    const activeId = sessionStore.activeSessionId;
    if (activeId) {
      return navigateTo(`/chat/${activeId}`, { replace: true });
    }
    
    // 如果没有活动的ID，则创建一个新的
    return navigateTo('/chat/new', { replace: true });
  }
});