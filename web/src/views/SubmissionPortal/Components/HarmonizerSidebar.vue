<script lang="ts">
import {
  defineComponent, PropType, ref,
} from '@vue/composition-api';
import FindReplace from '@/views/SubmissionPortal/Components/FindReplace.vue';
import type { HarmonizerApi } from '@/views/SubmissionPortal/harmonizerApi';
import ContactCard from '@/views/SubmissionPortal/Components/ContactCard.vue';
import ImportExportButtons from '@/views/SubmissionPortal/Components/ImportExportButtons.vue';
import ColumnHelp from '@/views/SubmissionPortal/Components/ColumnHelp.vue';

export default defineComponent({
  components: {
    ColumnHelp,
    ImportExportButtons,
    ContactCard,
    FindReplace,
  },
  props: {
    columnHelp: {
      type: Object,
      default: null,
    },
    template: {
      type: Object,
      default: null,
    },
    importDisabled: {
      type: Boolean,
      default: false,
    },
    harmonizerApi: {
      type: Object as PropType<HarmonizerApi>,
      required: true,
    },
  },
  emits: ['export-xlsx', 'import-xlsx'],
  setup(props, { emit }) {
    const tab = ref(0);

    // TODO: not sure why this can't be an inline arrow function in the template
    const handleImport = (...args: never[]) => {
      emit('import-xlsx', ...args);
    };

    return {
      handleImport,
      tab,
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
        <v-icon>mdi-text-search</v-icon>
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
      <v-tab-item class="pa-2">
        <ColumnHelp
          :column-help="columnHelp"
          :template="template"
          @full-reference-click="harmonizerApi.launchReference()"
        />
      </v-tab-item>
      <v-tab-item class="pa-2">
        <FindReplace
          :harmonizer-api="harmonizerApi"
        />
      </v-tab-item>
      <v-tab-item class="pa-2">
        SUGGESTER
      </v-tab-item>
      <v-tab-item class="pa-2">
        <ImportExportButtons
          :import-disabled="importDisabled"
          @export="$emit('export-xlsx')"
          @import="handleImport"
        />
      </v-tab-item>
      <v-tab-item>
        <ContactCard
          elevation="0"
        />
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
