<template>
  <CommonBaseModal title="编辑列表样式" theme-color="purple" @close="emit('close')" max-width="40rem">
    <div class="space-y-6">
      <div v-for="(style, key) in localStyles" :key="key" class="p-4 bg-gray-900/50 rounded-lg border border-gray-700">
        <h3 class="font-semibold text-purple-300 mb-3">{{ key === 'displayName' ? '模型名称样式' : '模型型号样式' }}</h3>
        <div class="space-y-4">
          <div>
            <label :for="`${key}-fontSize`" class="archive-label flex justify-between">
              <span>字体大小</span>
              <span class="text-gray-400">{{ style.fontSize }}px</span>
            </label>
            <input :id="`${key}-fontSize`" type="range" min="8" max="24" v-model.number="style.fontSize" class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500">
          </div>
          <div>
            <label :for="`${key}-color`" class="archive-label">颜色</label>
            <div class="flex items-center gap-2">
              <input :id="`${key}-color`" type="color" v-model="style.color" class="p-1 h-10 w-10 block bg-gray-700 border-gray-600 cursor-pointer rounded-lg disabled:opacity-50 disabled:pointer-events-none">
              <input type="text" v-model="style.color" class="archive-input !mt-0">
            </div>
          </div>
          <div>
            <label :for="`${key}-fontFamily`" class="archive-label">字体</label>
            <select :id="`${key}-fontFamily`" v-model="style.fontFamily" class="archive-input">
              <option value="'Roboto', sans-serif">Roboto (通用)</option>
              <option value="'Fira Code', monospace">Fira Code (代码)</option>
              <option value="'Inter', sans-serif">Inter (现代)</option>
              <option value="'Source Serif 4', serif">Source Serif (衬线)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
    <template #footer-actions>
      <button @click="resetToDefaults" class="btn btn-secondary">恢复默认</button>
      <button @click="save" class="btn btn-primary bg-purple-600 hover:bg-purple-500">应用并保存</button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, type PropType } from 'vue';
import type { StyleConfig, TextStyle } from '~/composables/usePersistentStyle';
import { deepClone } from '~/utils/helpers';

const props = defineProps({
  initialStyles: {
    type: Object as PropType<StyleConfig>,
    required: true,
  },
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', newStyles: StyleConfig): void;
  (e: 'reset'): void;
}>();

const localStyles = ref<StyleConfig>(deepClone(props.initialStyles));

function save() {
  emit('save', localStyles.value);
  emit('close');
}

function resetToDefaults() {
    emit('reset');
    emit('close');
}
</script>