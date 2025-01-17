<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import { urlify } from '@/data/utils';

export default defineComponent({
  props: {
    columnHelp: {
      type: Object,
      default: null,
    },
    template: {
      type: Object,
      default: null,
    },
  },
  emits: ['full-reference-click'],
  setup() {
    return {
      urlify,
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h6 mt-3 font-weight-bold d-flex align-center">
      Column Help
      <v-spacer />
    </div>

    <div v-if="columnHelp">
      <div class="my-2">
        <span class="font-weight-bold pr-2">Column:</span>
        <span
          :title="columnHelp.name"
          v-html="columnHelp.title"
        />
      </div>
      <div class="my-2">
        <span class="font-weight-bold pr-2">Description:</span>
        <span v-html="urlify(columnHelp.description)" />
      </div>
      <div class="my-2">
        <span class="font-weight-bold pr-2">Guidance:</span>
        <span v-html="urlify(columnHelp.guidance)" />
      </div>
      <div
        v-if="columnHelp.examples"
        class="my-2"
      >
        <span class="font-weight-bold pr-2">Examples:</span>
        <span v-html="urlify(columnHelp.examples)" />
      </div>
      <v-btn
        v-if="template"
        color="grey"
        outlined
        small
        block
        @click="$emit('full-reference-click')"
      >
        Full {{ template.displayName }} Reference
        <v-icon class="pl-1">
          mdi-open-in-new
        </v-icon>
      </v-btn>
    </div>
    <div v-else>
      <p class="my-2 text--disabled">
        Click on a cell or column to view help
      </p>
    </div>
  </div>
</template>
