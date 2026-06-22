<script setup lang="ts">
import { ref } from 'vue';

/**
 * Component for wrapping visualizations and other panels that
 * should have a help tooltip in the upper-right corner.
 */
const props = withDefaults(defineProps<{
  /** If true, include a button to open this panel in a fullscreen modal */
  allowFullscreen?: boolean;
  /** Fixed height for the panel (if number, defaults to pixels) */
  height?: string | number;
  /** Text to show in the help tooltip */
  helpText?: string | null;
}>(), {
  height: '360px',
  helpText: null,
});

const isFullscreen = ref(false);
const heightString = typeof props.height === 'string' ? props.height : `${props.height}px`;
const toggle = () => {
  isFullscreen.value = !isFullscreen.value;
  window.dispatchEvent(new Event('resize'));
};
const close = () => { isFullscreen.value = false; };
</script>

<template>
  <Teleport
    v-if="allowFullscreen"
    to="body"
  >
    <div
      class="fullscreen-backdrop"
      :class="{ 'fullscreen-backdrop--visible': isFullscreen }"
      @click="close"
    />
  </Teleport>
  <Teleport
    to="body"
    :disabled="!isFullscreen"
  >
    <v-card :class="['fullscreen-container', { 'fullscreen-container--fullscreen': isFullscreen }]">
      <div class="fullscreen-toolbar">
        <v-tooltip
          v-if="helpText"
          location="left"
          offset="20"
          min-width="300px"
          max-width="300px"
          :z-index="isFullscreen ? 2500 : undefined"
        >
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon="mdi-help-circle"
              size="large"
              variant="text"
              color="grey-darken-1"
              density="compact"
            />
          </template>
          <span v-html="helpText" />
        </v-tooltip>
        <v-btn
          v-if="allowFullscreen"
          :icon="isFullscreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen'"
          size="x-large"
          variant="text"
          density="compact"
          :title="isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'"
          @click="toggle"
        />
      </div>
      <div
        class="fullscreen-scroll-area"
        :style="{ 
          height: isFullscreen ? '90vh' : heightString,
        }"
      >
        <slot 
          :is-fullscreen="isFullscreen"
          :toggle="toggle"
        />
      </div>
    </v-card>
  </Teleport>
</template>

<style scoped>
.fullscreen-container {
  position: relative;
  width: 100%;
}

.fullscreen-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 4px;
  min-height: 36px;
  position: absolute;
  top: 0;
  right: 0.75rem;
  z-index: 2;
}

.fullscreen-container--fullscreen .fullscreen-toolbar {
  right: 0.25rem;
}

.fullscreen-title {
  font-weight: 500;
  font-size: 0.95rem;
}

.fullscreen-scroll-area {
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
}

.fullscreen-container--fullscreen {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90vw;
  height: 90vh;
  z-index: 2400;
  background: rgb(var(--v-theme-surface));
  display: flex;
  flex-direction: column;
}

.fullscreen-container--fullscreen .fullscreen-scroll-area {
  display: flex;
  align-items: center;
  flex: 1;
  height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.fullscreen-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2399;
  background: #000;
  opacity: 0;
  pointer-events: none;
  transition: 0.3s;
}

.fullscreen-backdrop--visible {
  opacity: 0.32;
  pointer-events: auto;
}
</style>