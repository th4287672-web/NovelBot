<template>
  <div class="w-full">
    <input
      v-if="editing"
      ref="inputRef"
      v-model="editedValue"
      type="text"
      class="archive-input !mt-0 text-lg font-semibold w-full focus:border-green-500"
      @blur="handleSave"
      @keydown.enter.prevent="handleSave"
      @keydown.esc.prevent="emit('cancel')"
    />
    <h3 v-else class="text-lg font-semibold truncate group-hover:text-green-400" :class="isActive ? 'text-green-300' : 'text-white'">
      {{ value }}
    </h3>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue';

const props = defineProps<{
  value: string;
  editing: boolean;
  isActive?: boolean;
}>();

const emit = defineEmits<{
  (e: 'save', newValue: string): void;
  (e: 'cancel'): void;
}>();

const editedValue = ref(props.value);
const inputRef = ref<HTMLInputElement | null>(null);

watch(() => props.editing, async (isEditing) => {
  if (isEditing) {
    editedValue.value = props.value;
    await nextTick();
    inputRef.value?.focus();
    inputRef.value?.select();
  }
});

function handleSave() {
  if (props.editing && editedValue.value.trim() && editedValue.value.trim() !== props.value) {
    emit('save', editedValue.value.trim());
  } else {
    emit('cancel');
  }
}
</script>