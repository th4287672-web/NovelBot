<template>
  <div class="h-full w-full p-6 flex flex-col items-center">
    <div class="w-full max-w-2xl space-y-6">
      <section class="p-6 bg-gray-800/50 rounded-lg border border-gray-700">
        <h2 class="text-lg font-semibold text-cyan-400">导出个人数据</h2>
        <p class="text-sm text-gray-400 mt-2">
          将您所有的私有角色卡、人设、预设、世界书和群组场景打包成一个单独的 `.json` 文件进行备份。
          这是一个很好的习惯，可以防止意外丢失数据。
        </p>
        <div class="mt-4">
          <button 
            @click="dataStore.exportData" 
            :disabled="dataStore.isExporting"
            class="btn btn-primary bg-cyan-600 hover:bg-cyan-500"
          >
            {{ dataStore.isExporting ? '正在导出...' : '导出全部数据' }}
          </button>
        </div>
      </section>

      <section class="p-6 bg-gray-800/50 rounded-lg border border-gray-700">
        <h2 class="text-lg font-semibold text-yellow-400">从备份文件导入</h2>
        <p class="text-sm text-gray-400 mt-2">
          从之前导出的 `.json` 备份文件恢复您的个人数据。导入过程**不会覆盖**任何现有同名项目，只会添加不存在的新项目。
        </p>
        <div class="mt-4">
          <input type="file" ref="fileInput" @change="handleFileSelect" accept=".json" class="hidden">
          <button 
            @click="triggerFileInput"
            :disabled="dataStore.isImporting"
            class="btn btn-primary bg-yellow-600 hover:bg-yellow-500"
          >
            {{ dataStore.isImporting ? '正在导入...' : '选择文件并导入' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useDataManagementStore } from '~/stores/dataManagementStore';
import type { ImportReport } from '~/types/api';

const dataStore = useDataManagementStore();
const fileInput = ref<HTMLInputElement | null>(null);

function triggerFileInput() {
  fileInput.value?.click();
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    await dataStore.importData(file);
    target.value = '';
  }
}
</script>