<template>
  <CommonBaseModal title="创建新预设" theme-color="green" max-width="80rem" @close="emit('close')">
    <div>
      <label for="presetName" class="archive-label">预设名称</label>
      <input 
        id="presetName"
        v-model="presetDisplayName"
        type="text"
        class="archive-input focus:border-green-500 focus:ring-green-500/30 focus:ring-2"
      />
    </div>
    
    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button @click="handleSave" class="btn btn-primary bg-green-600 hover:bg-green-500">创建</button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { BackendPreset } from '@/types/api';

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'create', data: BackendPreset): void;
}>();

const presetDisplayName = ref('我的新预设');

function handleSave() {
  const trimmedName = presetDisplayName.value.trim();
  if (!trimmedName) {
    alert('预设名称不能为空！');
    return;
  }
  
  // [核心修复] 确保创建的对象严格符合 BackendPreset 类型
  const newPresetData: BackendPreset = { 
      name: trimmedName, 
      displayName: trimmedName, 
      prompts: [] 
  };
  emit('create', newPresetData);
}
</script>