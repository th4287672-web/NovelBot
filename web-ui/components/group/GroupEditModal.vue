<template>
  <CommonBaseModal :title="modalTitle" theme-color="purple" @close="emit('close')" max-width="48rem">
    <div class="space-y-4">
      <div>
        <label for="groupName" class="archive-label">场景名称 (必填)</label>
        <input id="groupName" v-model="localGroup.name" type="text" class="archive-input focus:border-indigo-500 focus:ring-indigo-500/30 focus:ring-2" />
      </div>
      <div>
        <label for="groupDesc" class="archive-label">场景描述</label>
        <textarea id="groupDesc" v-model="localGroup.description" rows="3" class="archive-textarea focus:border-indigo-500 focus:ring-indigo-500/30 focus:ring-2"></textarea>
      </div>
       <div>
        <label for="groupFirstMes" class="archive-label">开场白 (场景的初始旁白)</label>
        <textarea id="groupFirstMes" v-model="localGroup.first_mes" rows="3" class="archive-textarea focus:border-indigo-500 focus:ring-indigo-500/30 focus:ring-2"></textarea>
      </div>
      <div>
        <label class="archive-label">选择参与角色 (至少选择1个)</label>
        <div class="max-h-60 overflow-y-auto space-y-1 p-2 border border-gray-600 rounded-md">
          <label v-for="char in aiCharacters" :key="char.filename" class="flex items-center text-sm p-2 rounded hover:bg-gray-700 cursor-pointer">
            <input 
              type="checkbox" 
              :value="char.filename" 
              v-model="localGroup.character_filenames" 
              class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-indigo-500 focus:ring-indigo-600"
            >
            <span class="ml-3 text-gray-200">{{ char.displayName }}</span>
          </label>
        </div>
      </div>
    </div>

    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button @click="handleSave" class="btn btn-primary bg-indigo-600 hover:bg-indigo-500">保存场景</button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, watch, computed, type PropType } from 'vue';
import type { Group } from '~/types/api';
import { deepClone } from '~/utils/helpers';
import { useCharacterStore } from '~/stores/characterStore';
import { storeToRefs } from 'pinia';

const props = defineProps({
  mode: {
    type: String as PropType<'create' | 'edit'>,
    required: true,
  },
  group: {
    type: Object as PropType<Group | null>,
    default: null,
  }
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', payload: { mode: 'create' | 'edit', data: Group }): void;
}>();

const characterStore = useCharacterStore();
const { characters } = storeToRefs(characterStore);

const aiCharacters = computed(() => {
    return Object.values(characters.value).filter(char => !char.is_user_persona);
});

const modalTitle = computed(() => props.mode === 'create' ? '创建新场景' : `编辑场景: ${props.group?.name}`);

const defaultGroup: Group = {
  filename: '',
  name: '',
  description: '',
  first_mes: '',
  character_filenames: [],
  is_private: true,
};

const localGroup = ref<Group>(defaultGroup);

watch(() => [props.mode, props.group], () => {
  if (props.mode === 'edit' && props.group) {
    localGroup.value = deepClone(props.group);
  } else {
    localGroup.value = deepClone(defaultGroup);
  }
}, { immediate: true });

function handleSave() {
  if (!localGroup.value.name.trim()) {
    alert('场景名称不能为空！');
    return;
  }
  if (localGroup.value.character_filenames.length === 0) {
    alert('请至少选择一个参与角色！');
    return;
  }
  emit('save', { mode: props.mode, data: localGroup.value });
}
</script>
