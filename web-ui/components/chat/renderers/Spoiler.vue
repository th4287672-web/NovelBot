<template>
  <span 
    class="bg-gray-600 hover:bg-gray-700/80 text-gray-600 hover:text-white transition-colors duration-200 cursor-pointer p-1 rounded select-none"
    @click="revealed = !revealed"
  >
    <span v-if="!revealed">{{ placeholder }}</span>
    <span v-else><slot></slot></span>
  </span>
</template>

<script setup lang="ts">
import { ref } from 'vue';
defineProps({
  placeholder: {
    type: String,
    default: '（点击查看剧透）'
  }
});
const revealed = ref(false);
</script>