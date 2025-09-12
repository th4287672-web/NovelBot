<template>
  <span class="p-1 rounded" :style="{ backgroundColor: color, color: textColor }">
    <slot></slot>
  </span>
</template>

<script setup lang="ts">
defineProps({
  color: {
    type: String,
    default: 'yellow'
  },
  textColor: {
    type: String,
    default: 'black'
  }
});
</script>