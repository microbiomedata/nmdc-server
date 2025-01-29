<script lang="ts">
import {
  defineComponent, PropType, ref,
} from '@vue/composition-api';
import FindReplace from '@/views/SubmissionPortal/Components/FindReplace.vue';
import type { HarmonizerApi } from '@/views/SubmissionPortal/harmonizerApi';
import ContactCard from '@/views/SubmissionPortal/Components/ContactCard.vue';
import ImportExportButtons from '@/views/SubmissionPortal/Components/ImportExportButtons.vue';
import ColumnHelp from '@/views/SubmissionPortal/Components/ColumnHelp.vue';
import MetadataSuggester from '@/views/SubmissionPortal/Components/MetadataSuggester.vue';

export default defineComponent({
  components: {
    MetadataSuggester,
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
    const tabModel = ref(0);
    const TABS = [
      {
        icon: 'mdi-information-outline',
        label: 'Column Help',
      },
      {
        icon: 'mdi-text-search',
        label: 'Find & Replace',
      },
      {
        icon: 'mdi-assistant',
        label: 'Metadata Suggester',
      },
      {
        icon: 'mdi-swap-vertical',
        label: 'Import & Export',
      },
      {
        icon: 'mdi-help-circle-outline',
        label: 'Help',
      },
    ];

    // TODO: not sure why this can't be an inline arrow function in the template
    const handleImport = (...args: never[]) => {
      emit('import-xlsx', ...args);
    };

    return {
      TABS,
      handleImport,
      tabModel,
    };
  },
});
</script>

<template>
  <div class="harmonizer-sidebar-content">
    <v-tabs
      v-model="tabModel"
      grow
    >
      <v-tooltip
        v-for="tab in TABS"
        :key="tab.label"
        open-delay="600"
        top
        z-index="400"
      >
        <template #activator="{ on, attrs }">
          <v-tab
            v-bind="attrs"
            v-on="on"
          >
            <v-icon>{{ tab.icon }}</v-icon>
          </v-tab>
        </template>
        <span>{{ tab.label }}</span>
      </v-tooltip>
    </v-tabs>

    <v-divider />

    <v-tabs-items v-model="tabModel">
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
      <v-tab-item>
        <MetadataSuggester
          :harmonizer-api="harmonizerApi"
          :schema-class-name="template.schemaClass"
        />
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
