<template>
  <div>
    <label class="archive-label">源图片</label>
    <div 
      class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-600 border-dashed rounded-md cursor-pointer hover:border-cyan-500 transition-colors"
      @click="triggerFileInput"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
      :class="{ 'border-cyan-500': isDragOver }"
    >
      <div class="space-y-1 text-center">
        <img v-if="base64" :src="base64" class="mx-auto h-24 w-auto object-contain" />
        <div v-else class="mx-auto h-12 w-12 text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true"><path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>
        </div>
        <div class="flex text-sm text-gray-500">
          <p class="pl-1">{{ base64 ? '点击或拖拽以更换图片' : '上传文件或拖拽到此处' }}</p>
        </div>
        <p class="text-xs text-gray-500">PNG, JPG, WEBP, up to 5MB</p>
      </div>
    </div>
    <input ref="fileInput" type="file" class="hidden" accept="image/png, image/jpeg, image/webp" @change="onFileChange">
  </div>
</template>

<script setup lang="ts">
import { ref, type PropType } from 'vue';
import { useUIStore } from '~/stores/ui';

const props = defineProps({
  base64: {
      type: String as PropType<string | null>,
      default: null,
  },
});
const emit = defineEmits(['update:base64']);

const uiStore = useUIStore();
const fileInput = ref<HTMLInputElement | null>(null);
const isDragOver = ref(false);

function triggerFileInput() {
  fileInput.value?.click();
}

function processFile(file: File) {
  if (file.size > 5 * 1024 * 1024) {
    uiStore.setGlobalError('图片文件不能超过 5MB');
    return;
  }
  const reader = new FileReader();
  reader.onload = (e) => {
    emit('update:base64', e.target?.result as string);
  };
  reader.readAsDataURL(file);
}

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    processFile(target.files[0]);
  }
}

function onDragOver() { isDragOver.value = true; }
function onDragLeave() { isDragOver.value = false; }
function onDrop(e: DragEvent) {
  isDragOver.value = false;
  if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
    processFile(e.dataTransfer.files[0]);
  }
}
</script>