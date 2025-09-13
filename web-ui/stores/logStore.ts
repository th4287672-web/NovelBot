import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface LogEntry {
  id: number;
  timestamp: string;
  level: 'log' | 'warn' | 'error' | 'info' | 'debug';
  message: string;
}

export const useLogStore = defineStore('log', () => {
  const logs = ref<LogEntry[]>([]);
  const isVisible = ref(false);
  let logCounter = 0;

  function addLog(level: LogEntry['level'], args: any[]) {
    const message = args.map(arg => {
        try {
            if (arg instanceof Error) {
                return `Error: ${arg.message}\nStack: ${arg.stack}`;
            }
            if (typeof arg === 'object' && arg !== null) {
                return JSON.stringify(arg, null, 2);
            }
            return String(arg);
        } catch (e) {
            return '[Unserializable Object]';
        }
    }).join(' ');

    logs.value.push({
      id: logCounter++,
      timestamp: new Date().toISOString(),
      level,
      message,
    });
  }

  function clearLogs() {
    logs.value = [];
  }
  
  function toggleVisibility() {
      isVisible.value = !isVisible.value;
  }

  return {
    logs,
    isVisible,
    addLog,
    clearLogs,
    toggleVisibility,
  };
});