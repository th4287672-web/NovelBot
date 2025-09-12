<template>
  <CommonBaseModal :title="modalTitle" theme-color="yellow" max-width="80rem" @close="emit('close')">
    <form @submit.prevent="save" class="space-y-4">
        <div>
          <label class="archive-label">条目名称 (可选)</label>
          <input type="text" v-model="localEntry.name" class="archive-input focus:border-yellow-500 focus:ring-yellow-500/30 focus:ring-2" />
        </div>
        <div>
          <label class="archive-label">关键词 (用逗号分隔)</label>
          <input type="text" :value="(localEntry.keywords || []).join(', ')" @input="updateKeywords" class="archive-input focus:border-yellow-500 focus:ring-yellow-500/30 focus:ring-2" />
        </div>
        <div>
          <label class="archive-label">内容</label>
          <textarea v-model="localEntry.content" rows="8" class="archive-textarea focus:border-yellow-500 focus:ring-yellow-500/30 focus:ring-2"></textarea>
        </div>
    </form>
    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button @click="save" class="btn btn-primary bg-yellow-600 hover:bg-yellow-500">保存条目</button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, computed, watch, type PropType } from 'vue';
import type { WorldInfoEntry } from '~/types/api';
import { deepClone } from '~/utils/helpers';
import { v4 as uuidv4 } from 'uuid';

const props = defineProps({
  mode: {
    type: String as PropType<'create' | 'edit'>,
    required: true,
  },
  entry: {
    type: Object as PropType<WorldInfoEntry | null>,
    default: null,
  },
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', entry: WorldInfoEntry): void;
}>();

const localEntry = ref<WorldInfoEntry>({ uid: uuidv4(), name: '', keywords: [], content: '' });

const modalTitle = computed(() => props.mode === 'create' ? '创建新条目' : '编辑条目');

watch(() => props.entry, (newEntry) => {
  if (props.mode === 'edit' && newEntry) {
    localEntry.value = deepClone(newEntry);
  } else {
    localEntry.value = { uid: uuidv4(), name: '', keywords: [], content: '' };
  }
}, { immediate: true });

function updateKeywords(event: Event) {
  const target = event.target as HTMLInputElement;
  localEntry.value.keywords = target.value.split(',').map(k => k.trim()).filter(Boolean);
}

function save() {
  emit('save', localEntry.value);
}
</script>