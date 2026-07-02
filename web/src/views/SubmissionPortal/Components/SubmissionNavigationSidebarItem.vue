<script setup lang="ts">
import { computed } from 'vue';
import { RouteLocationRaw } from 'vue-router';

const props = defineProps<{
  title: string;
  link?: RouteLocationRaw;
  validationMessages: string[] | null;
}>();

const listItemProps = computed(() => {
  if (!props.link) {
    return {};
  }
  return {
    to: props.link,
    link: true,
  };
});

function getValidationTitle(validationMessages: string[]) {
  return validationMessages.join('\n');
}
</script>

<template>
  <v-list-item
    v-bind="listItemProps"
    :title="title"
  >
    <template
      v-if="Array.isArray(validationMessages)"
      #append
    >
      <v-badge
        v-if="validationMessages.length !== 0"
        inline
        color="red"
        :content="validationMessages.length"
        :title="getValidationTitle(validationMessages)"
      />
      <v-icon
        v-else
        style="margin-right: 2px"
        color="green"
      >
        mdi-check-circle-outline
      </v-icon>
    </template>
  </v-list-item>
</template>
