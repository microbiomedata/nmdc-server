<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { urlify } from '@/data/utils';
import { ColumnHelpInfo, HarmonizerTemplateInfo } from '@/views/SubmissionPortal/types';

export default defineComponent({
  props: {
    columnHelp: {
      type: Object as PropType<ColumnHelpInfo | null>,
      default: null,
    },
    harmonizerTemplate: {
      type: Object as PropType<HarmonizerTemplateInfo>,
      required: true,
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
  <v-card elevation="0">
    <v-card-title>
      Column Info
    </v-card-title>

    <v-card-text
      v-if="columnHelp"
      class="text--primary"
    >
      <div class="mb-2">
        <span class="font-weight-bold pr-2">Column:</span>
        <span
          :title="columnHelp.name"
          v-html="columnHelp.title"
        />
      </div>
      <div class="mb-2">
        <span class="font-weight-bold pr-2">Description:</span>
        <span v-html="urlify(columnHelp.description)" />
      </div>
      <div class="mb-2">
        <span class="font-weight-bold pr-2">Guidance:</span>
        <span v-html="urlify(columnHelp.guidance)" />
      </div>
      <div
        v-if="columnHelp.examples"
        class="mb-2"
      >
        <span class="font-weight-bold pr-2">Examples:</span>
        <span v-html="urlify(columnHelp.examples)" />
      </div>
      <v-btn
        color="grey"
        outlined
        small
        block
        @click="$emit('full-reference-click')"
      >
        Full {{ harmonizerTemplate.displayName }} Reference
        <v-icon class="pl-1">
          mdi-open-in-new
        </v-icon>
      </v-btn>
    </v-card-text>

    <v-card-text
      v-else
      class="text--disabled"
    >
      Click on a cell or column to view help
    </v-card-text>
  </v-card>
</template>
