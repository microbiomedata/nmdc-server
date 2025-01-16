<script lang="ts">
import {
  defineComponent, ref,
} from '@vue/composition-api';
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
  emits: [
    'template-reference-button-click',
  ],
  setup() {
    const tab = ref(0);

    return {
      tab,
      urlify,
    };
  },
});
</script>

<template>
  <div class="harmonizer-sidebar-content">
    <v-tabs
      v-model="tab"
      grow
    >
      <v-tab>
        <v-icon>mdi-information-outline</v-icon>
      </v-tab>
      <v-tab>
        <v-icon>mdi-magnify</v-icon>
      </v-tab>
      <v-tab>
        <v-icon>mdi-assistant</v-icon>
      </v-tab>
      <v-tab>
        <v-icon>mdi-swap-vertical</v-icon>
      </v-tab>
      <v-tab>
        <v-icon>mdi-help-circle-outline</v-icon>
      </v-tab>
    </v-tabs>

    <v-tabs-items v-model="tab">
      <v-tab-item>
        <div
          v-if="columnHelp"
          class="mx-2"
        >
          <div class="text-h6 mt-3 font-weight-bold d-flex align-center">
            Column Help
            <v-spacer />
          </div>
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
            color="grey"
            outlined
            small
            block
            @click="$emit('template-reference-button-click')"
          >
            Full {{ template.displayName }} Reference
            <v-icon class="pl-1">
              mdi-open-in-new
            </v-icon>
          </v-btn>
        </div>
        <div v-else>
          <div class="mx-2">
            <div class="text-h6 mt-3 font-weight-bold d-flex align-center">
              Column Help
              <v-spacer />
            </div>
            <p class="my-2 text--disabled">
              Click on a cell or column to view help
            </p>
          </div>
        </div>
      </v-tab-item>
      <v-tab-item>
        FIND AND REPLACE
      </v-tab-item>
      <v-tab-item>
        SUGGESTER
      </v-tab-item>
      <v-tab-item>
        IMPORT / EXPORT
      </v-tab-item>
      <v-tab-item>
        SITE HELP
      </v-tab-item>
    </v-tabs-items>
  </div>
</template>

<style lang="scss" scoped>
.harmonizer-sidebar-content {
  font-size: 14px;

  .v-tab {
    min-width: 10px;
  }
}
</style>
