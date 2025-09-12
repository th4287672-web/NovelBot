// web-ui/plugins/logger.client.ts
import { useLogStore } from '~/stores/logStore';

export default defineNuxtPlugin((nuxtApp) => {
  if (process.client) {
    const logStore = useLogStore();

    const originalConsole = {
      log: console.log,
      warn: console.warn,
      error: console.error,
      info: console.info,
      debug: console.debug,
    };

    const createLogger = (level: 'log' | 'warn' | 'error' | 'info' | 'debug') => {
      return (...args: any[]) => {
        logStore.addLog(level, args);
        originalConsole[level](...args);
      };
    };

    console.log = createLogger('log');
    console.warn = createLogger('warn');
    console.error = createLogger('error');
    console.info = createLogger('info');
    console.debug = createLogger('debug');
    
    window.addEventListener('error', (event) => {
      logStore.addLog('error', [event.message, event.filename, event.lineno, event.colno, event.error]);
    });

    window.addEventListener('unhandledrejection', (event) => {
      logStore.addLog('error', ['Unhandled Promise Rejection:', event.reason]);
    });
  }
});