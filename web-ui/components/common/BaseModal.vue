<template>
  <Teleport to="body">
    <div v-if="isMounted" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" @click.self="handleClose">
      <div 
        class="archive-card w-11/12"
        :style="{ maxWidth: maxWidth }"
      >
        <header class="archive-header">
          <h2 class="archive-header-title" :style="{ color: `var(--color-theme-${themeColor})` }">
            <slot name="title">// {{ title }}</slot>
          </h2>
          <button v-if="closable" @click="handleClose" class="text-gray-400 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </header>

        <main class="archive-main">
          <slot></slot>
        </main>

        <footer class="archive-footer">
          <slot name="footer-actions"></slot>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, type PropType } from 'vue';

type ThemeColor = 'cyan' | 'purple' | 'yellow' | 'green' | 'gray' | 'indigo' | 'red';

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  maxWidth: {
    type: String,
    default: '80rem', // [核心修改] 将最大宽度上限增加到 '80rem' (1280px)
  },
  themeColor: {
    type: String as PropType<ThemeColor>,
    default: 'gray',
  },
  closable: {
    type: Boolean,
    default: true,
  }
});

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const isMounted = ref(false);

function handleClose() {
  if (props.closable) {
    emit('close');
  }
}

onMounted(() => {
  isMounted.value = true;
  document.body.style.overflow = 'hidden';
});

onUnmounted(() => {
  document.body.style.overflow = '';
});
</script>