<script setup lang="ts">
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const props = withDefaults(defineProps<{
  error?: string | null;
  loading?: boolean;
  height: number;
}>(), {
  error: null,
  loading: false,
});
</script>

<template>
  <div
    v-if="loading || error"
    class="d-flex justify-center align-center"
    :style="{
      position: 'absolute',
      zIndex: 2,
      height: `${height}px`,
      width: '100%',
      background: '#fff',
      opacity: 0.5,
    }"
  >
    <v-progress-circular
      v-if="loading"
      indeterminate
      color="primary"
    />
    <div v-else>
      {{ error }}
    </div>
  </div>
</template>