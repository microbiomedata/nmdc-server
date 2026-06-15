<script setup lang="ts">
/**
 * The tabbed Data Harmonizer sidebar.
 */
import { ref, watch } from 'vue';
import FindReplace from '@/views/SubmissionPortal/Components/FindReplace.vue';
import type HarmonizerApi from '@/views/SubmissionPortal/harmonizerApi';
import ContactCard from '@/views/SubmissionPortal/Components/ContactCard.vue';
import ImportExportButtons from '@/views/SubmissionPortal/Components/ImportExportButtons.vue';
import ColumnHelp from '@/views/SubmissionPortal/Components/ColumnHelp.vue';
import MetadataSuggester from '@/views/SubmissionPortal/Components/MetadataSuggester.vue';
import { ColumnHelpInfo, HarmonizerTemplateInfo } from '@/views/SubmissionPortal/types';
import { sampleData } from '../store';

interface HarmonizerSidebarProps {
  /**
   * The submission ID
   */
  submissionId: string;
  /**
   * Help information for the currently selected column.
   */
  columnHelp?: ColumnHelpInfo | null;
  /**
   * Information about the active template.
   */
  harmonizerTemplate: HarmonizerTemplateInfo;
  /**
   * Whether the current user is allowed to edit metadata.
   */
  metadataEditingAllowed?: boolean;
  /**
   * The Harmonizer API instance.
   */
  harmonizerApi: HarmonizerApi;
  /**
   * Callback to fetch suggestions from the study info forms.
   */
  fetchStudyInfoSuggestions?: () => Promise<any>;
}

withDefaults(defineProps<HarmonizerSidebarProps>(), {
  columnHelp: null,
  metadataEditingAllowed: false,
});

const emit = defineEmits<{
  'export-xlsx': [];
  'import-xlsx': [file: File];
}>();

const tabModel = ref(0);
const SUGGESTER_TAB_INDEX = 1;
const showBadge = ref(false);

// // Show badge when a cell in the spreadsheet changes and suggester tab is not active
// watch(hasChanged, (newVal: number, oldVal: number) => {
//   if (newVal > oldVal && tabModel.value !== SUGGESTER_TAB_INDEX) {
//     showBadge.value = true;
//   }
// });

// Show badge on page load/reload if the submission already has sample data
watch(() => sampleData.data, (newData: Record<string, any[]>) => {
  const hasData = Object.values(newData).some(rows => rows.length > 0);
  if (hasData && tabModel.value !== SUGGESTER_TAB_INDEX) {
    showBadge.value = true;
  }
}, { immediate: true });

// Clear badge when suggester tab is selected
watch(tabModel, (newTab: number) => {
  if (newTab === SUGGESTER_TAB_INDEX) {
    showBadge.value = false;
  }
});

const TABS = [
  {
    icon: 'mdi-information-outline',
    label: 'Column Info',
  },
  {
    icon: 'mdi-assistant',
    label: 'Metadata Suggester',
  },
  {
    icon: 'mdi-text-search',
    label: 'Find & Replace',
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

const handleImport = (file: File) => {
  emit('import-xlsx', file);
};
</script>

<template>
  <div class="harmonizer-sidebar-content d-flex flex-column fill-height">
    <div class="flex-0-0">
      <v-tabs
        v-model="tabModel"
        color="primary"
        grow
      >
        <v-tooltip
          v-for="(tab, tabIndex) in TABS"
          :key="tab.label"
          open-delay="600"
          location="top"
        >
          <template #activator="{ props: tabActivatorProps }">
            <v-tab
              v-bind="tabActivatorProps"
              style="overflow: visible;"
            >
              <v-icon size="x-large">{{ tab.icon }}</v-icon>
              <span
                v-if="tabIndex === SUGGESTER_TAB_INDEX && showBadge"
                class="suggester-dot"
              />
            </v-tab>
          </template>
          <span>{{ tab.label }}</span>
        </v-tooltip>
      </v-tabs>
      <v-divider />
    </div>

    <v-window
      v-model="tabModel"
      class="flex-grow-1 overflow-y-auto"
    >
      <v-window-item>
        <ColumnHelp
          :column-help="columnHelp"
          :harmonizer-template="harmonizerTemplate"
          @full-reference-click="harmonizerApi.launchReference()"
        />
      </v-window-item>
      <v-window-item>
        <MetadataSuggester
          :submission-id="submissionId"
          :enabled="metadataEditingAllowed"
          :harmonizer-api="harmonizerApi"
          :schema-class-name="harmonizerTemplate.schemaClass || ''"
          :fetch-study-info-suggestions="fetchStudyInfoSuggestions"
        />
      </v-window-item>
      <v-window-item>
        <FindReplace
          :harmonizer-api="harmonizerApi"
        />
      </v-window-item>
      <v-window-item>
        <ImportExportButtons
          :import-disabled="!metadataEditingAllowed"
          @export="$emit('export-xlsx')"
          @import="handleImport"
        />
      </v-window-item>
      <v-window-item>
        <ContactCard elevation="0" />
      </v-window-item>
    </v-window>
  </div>
</template>

<style lang="scss" scoped>
.harmonizer-sidebar-content {
  font-size: 14px;

  .v-tab {
    min-width: 10px;
  }
}

.tab-with-badge {
  overflow: visible !important;
  position: relative
}

.suggester-dot {
  position: absolute;
  top: 9px;
  right: 18px;
  width: 10px;
  height: 10px;
  background-color: #ff5330;
  border-radius: 50%;
  pointer-events: none;
}
</style>
