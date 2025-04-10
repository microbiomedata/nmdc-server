<script lang="ts">
import {
  defineComponent, PropType, ref,
} from '@vue/composition-api';
import FindReplace from '@/views/SubmissionPortal/Components/FindReplace.vue';
import type HarmonizerApi from '@/views/SubmissionPortal/harmonizerApi';
import ContactCard from '@/views/SubmissionPortal/Components/ContactCard.vue';
import ImportExportButtons from '@/views/SubmissionPortal/Components/ImportExportButtons.vue';
import ColumnHelp from '@/views/SubmissionPortal/Components/ColumnHelp.vue';
import MetadataSuggester from '@/views/SubmissionPortal/Components/MetadataSuggester.vue';
import { ColumnHelpInfo, HarmonizerTemplateInfo } from '@/views/SubmissionPortal/types';

/**
 * The tabbed Data Harmonizer sidebar.
 */
export default defineComponent({
  components: {
    MetadataSuggester,
    ColumnHelp,
    ImportExportButtons,
    ContactCard,
    FindReplace,
  },
  props: {
    /**
     * Help information for the currently selected column.
     */
    columnHelp: {
      type: Object as PropType<ColumnHelpInfo | null>,
      default: null,
    },
    /**
     * Information about the active template.
     */
    harmonizerTemplate: {
      type: Object as PropType<HarmonizerTemplateInfo>,
      required: true,
    },
    /**
     * Whether the current user is allowed to edit metadata.
     */
    metadataEditingAllowed: {
      type: Boolean,
      default: false,
    },
    /**
     * The Harmonizer API instance.
     */
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
        label: 'Column Info',
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
  <div class="harmonizer-sidebar-content d-flex flex-column fill-height">
    <div class="flex-grow-0 flex-shrink-0">
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
    </div>

    <v-tabs-items
      v-model="tabModel"
      class="flex-grow-1 overflow-y-auto"
    >
      <v-tab-item>
        <ColumnHelp
          :column-help="columnHelp"
          :harmonizer-template="harmonizerTemplate"
          @full-reference-click="harmonizerApi.launchReference()"
        />
      </v-tab-item>
      <v-tab-item>
        <FindReplace
          :harmonizer-api="harmonizerApi"
        />
      </v-tab-item>
      <v-tab-item>
        <MetadataSuggester
          :enabled="metadataEditingAllowed"
          :harmonizer-api="harmonizerApi"
          :schema-class-name="harmonizerTemplate.schemaClass"
        />
      </v-tab-item>
      <v-tab-item>
        <ImportExportButtons
          :import-disabled="!metadataEditingAllowed"
          @export="$emit('export-xlsx')"
          @import="handleImport"
        />
      </v-tab-item>
      <v-tab-item>
        <ContactCard elevation="0" />
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
