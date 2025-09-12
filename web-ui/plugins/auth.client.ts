import { useSettingsStore } from '~/stores/settings';
import { useWebSocket } from '~/services/websocket';

export default defineNuxtPlugin(async (nuxtApp) => {
  if (process.server) return;

  // [核心优化] 简化 auth 插件的职责。
  // 它现在的唯一任务就是在客户端初始化时，根据 settingsStore 中的 userId 建立 WebSocket 连接。
  // 所有的数据获取逻辑都已移交给 useBootstrapQuery，由组件的生命周期来驱动，这更加稳健。
  // 移除了复杂的 prefetchQuery，因为它可能在 userId 准备好之前运行，引发竞态条件。

  const settingsStore = useSettingsStore();
  console.log('[Auth Plugin] 插件已初始化。当前用户ID:', settingsStore.userId);

  const { connect } = useWebSocket();

  // [代码注释] 监听 userId 的变化。一旦 userId 变得有效（无论是从 localStorage 读取还是登录后设置），
  // 就立即尝试连接 WebSocket。
  watch(
    () => settingsStore.userId,
    (newUserId) => {
      if (newUserId) {
        console.log(`[Auth Plugin] 检测到有效用户ID '${newUserId}'，正在连接 WebSocket...`);
        connect();
      }
    },
    { immediate: true } // immediate: true 确保插件加载时会立即执行一次检查
  );
});