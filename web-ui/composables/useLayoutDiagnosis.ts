import { onMounted, onUnmounted, nextTick, ref, readonly } from 'vue';

const isEnabled = ref(false);
const rect = ref<DOMRect | null>(null);
let intervalId: number | null = null;

function updateElementPosition() {
  if (!isEnabled.value) return;
  
  const actionsWrapper = document.getElementById('actions-wrapper');
  
  if (actionsWrapper) {
    rect.value = actionsWrapper.getBoundingClientRect();
  } else {
    rect.value = null;
  }
}

function startPolling() {
  if (intervalId) return;
  intervalId = window.setInterval(updateElementPosition, 500);
}

function stopPolling() {
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = null;
    rect.value = null;
  }
}

function toggle() {
  isEnabled.value = !isEnabled.value;
  if (isEnabled.value) {
    startPolling();
  } else {
    stopPolling();
  }
}

export function useLayoutDiagnosis() {
  onUnmounted(() => {
    stopPolling();
    isEnabled.value = false;
  });

  return {
    isEnabled: readonly(isEnabled),
    rect: readonly(rect),
    toggle,
  };
}