<template>
  <div>
    <!-- This is a placeholder for the /tools route -->
    <!-- The actual content is rendered by the layout based on the active tab -->
  </div>
</template>

<script setup lang="ts">
// Redirect to the default tools tab
onMounted(() => {
  navigateTo('/tools/rules', { replace: true });
});
</script>```