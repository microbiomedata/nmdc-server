<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
// @ts-ignore
import Treeselect from '@zanmato/vue3-treeselect';
import { stateRefs, dataObjectFilter } from '@/store';
import DownloadDialog from '@/components/DownloadDialog.vue';
import useBulkDownload from '@/use/useBulkDownload';
import { humanFileSize } from '@/data/utils';
import { api } from '@/data/api';
import { downloadBlob } from '@/utils';
import ErrorDialog from './ErrorDialog.vue';

const {
  disabled = false,
  searchResultCount = 0,
} = defineProps<{
  disabled?: boolean;
  searchResultCount?: number;
}>();

const errorDialog = ref(false);
const bulkTermsDialog = ref(false);
const metadataTermsDialog = ref(false);
const metadataDownloadLoading = ref(false);
const downloadMenuOpen = ref(false);
const treeMenuOpen = ref(false);
const tab = ref('one');
const metadataDownloadSelected = ref<string[]>([]);
const bulkDownloadSelected = ref(stateRefs.bulkDownloadSelected);

const {
  loading,
  downloadSummary,
  downloadOptions,
  download,
} = useBulkDownload(stateRefs.conditions, dataObjectFilter);

function createLabelString(label: string, count: number, size: number): string {
  const labelString = `${label} (${count}`;
  if (size > 0) {
    return `${labelString}, ${humanFileSize(size)})`;
  }
  return `${labelString})`;
}

const dataProductOptions = computed(() => {
  if (!downloadOptions.value || typeof downloadOptions.value !== 'object') {
    return [];
  }
  return Object.entries(downloadOptions.value)
    .map(([key, val]) => ({
      id: key,
      label: createLabelString(key, val.count, val.size),
      children: Object.entries(val.file_types || {}).map(([filetype, fileTypeStats]) => ({
        id: `${key}::${filetype}`,
        label: createLabelString(filetype, fileTypeStats.count, fileTypeStats.size),
      })),
    }));
});

const metadataOptions = computed(() => [
  {
    id: 'biosamples',
    label: 'Biosamples',
  },
  {
    id: 'studies',
    label: 'Studies',
  },
]);

async function createAndDownload() {
  try {
    downloadMenuOpen.value = false;
    bulkTermsDialog.value = false;
    const val = await download();
    window.location.assign(val.url);
  } catch (error) {
    console.error('Failed to create bulk download:', error);
    errorDialog.value = true;
  }
}

function handleLoginClick() {
  api.initiateOrcidLogin();
}

async function downloadMetadata() {
  try {
    downloadMenuOpen.value = false;
    metadataDownloadLoading.value = true;
    metadataTermsDialog.value = false;
    const endpoints = metadataDownloadSelected.value;
    const blob = await api.getMetadataZip(stateRefs.conditions.value, endpoints);
    downloadBlob(blob, 'metadata.zip');
  } catch (error) {
    console.error('Failed to download metadata:', error);
    errorDialog.value = true;
  } finally {
    metadataDownloadLoading.value = false;
  }
}

const downloadProductsDisabledTooltip = computed(() => {
  if (searchResultCount === 0) {
    return 'No search results to download data products for.';
  } else if (downloadSummary.value.count === 0) {
    return 'Select at least one file type with data to download.';
  }
  return null;
});

const downloadMetadataDisabledTooltip = computed(() => {
  if (searchResultCount === 0) {
    return 'No search results to download metadata for.';
  } else if (metadataDownloadSelected.value.length === 0) {
    return 'Select at least one metadata type to download.';
  }
  return null;
});

watch(
  () => downloadMenuOpen.value,
  (newVal) => {
    if (newVal === false && treeMenuOpen.value === true) {
      downloadMenuOpen.value = true;
    }
  },
);
</script>

<template>
  <v-chip
    v-if="disabled"
    class="text-subtitle-1 ml-4"
    @click="handleLoginClick"
  >
    Log in to download
  </v-chip>
  <v-menu 
    v-else
    v-model="downloadMenuOpen"
    :close-on-content-click="false"
  >
    <template #activator="{ props }">
      <v-btn
        color="primary"
        elevation="0"
        v-bind="props"
      >
        <v-icon class="pr-2">
          mdi-download
        </v-icon>
        Download
        <v-icon class="pl-2">
          mdi-chevron-down
        </v-icon>
      </v-btn>
    </template>
    <v-sheet
      elevation="4"
    >
      <v-tabs 
        v-model="tab"
        color="primary"
      >
        <v-tab value="data-products">
          Data Products
          <v-tooltip
            location="top"
            min-width="300px"
            max-width="300px"
          >
            <template #activator="{ props }">
              <v-icon
                class="ml-2"
                size="small"
                v-bind="props"
              >
                mdi-help-circle
              </v-icon>
            </template>
            <span>
              Choose a group of files to download based on file type
              from the currently filtered search results.
            </span>
          </v-tooltip>
        </v-tab>
        <v-tab value="metadata">
          Metadata
          <v-tooltip
            location="top"
            min-width="300px"
            max-width="300px"
          >
            <template #activator="{ props }">
              <v-icon
                class="ml-2"
                size="small"
                v-bind="props"
              >
                mdi-help-circle
              </v-icon>
            </template>
            <span>
              Download metadata as JSON for the currently filtered search results.
            </span>
          </v-tooltip>
        </v-tab>
      </v-tabs>
      <v-divider />
      <v-tabs-window 
        v-model="tab" 
        class="download-menu"
      >
        <v-tabs-window-item value="data-products">
          <v-sheet
            class="pa-3 d-flex flex-column"
          >
            <span
              class="text-caption font-weight-bold"
            >
              <template v-if="downloadSummary.count === 0">
                No files selected
              </template>
              <template v-else>
                Download {{ downloadSummary.count }} files
                from {{ searchResultCount }} sample search results.
                (Download archive size {{ humanFileSize(downloadSummary.size) }})
              </template>
            </span>
            <div>
              <div @click.stop>
                <Treeselect
                  v-model="bulkDownloadSelected"
                  append-to-body
                  class="flex-1-1-0"
                  multiple
                  value-consists-of="LEAF_PRIORITY"
                  open-direction="below"
                  :options="dataProductOptions"
                  placeholder="Select file types"
                  z-index="2001"
                  @open="treeMenuOpen = true"
                  @close="treeMenuOpen = false"
                />
              </div>
              <v-dialog
                v-model="bulkTermsDialog"
                :width="400"
              >
                <template #activator="{ props: dialogProps }">
                  <v-tooltip
                    :disabled="!downloadProductsDisabledTooltip"
                    location="top"
                  >
                    <template #activator="{ props: tooltipProps }">
                      <span v-bind="tooltipProps">
                        <v-btn
                          class="mt-3"
                          color="white"
                          :disabled="!!downloadProductsDisabledTooltip"
                          v-bind="dialogProps"
                        >
                          <v-icon class="pr-3">
                            mdi-download
                          </v-icon>
                          Download Data Products Zip
                        </v-btn>
                      </span>
                    </template>
                    <span>{{ downloadProductsDisabledTooltip }}</span>
                  </v-tooltip>
                </template>
                <DownloadDialog
                  :loading="loading"
                  @clicked="createAndDownload"
                />
              </v-dialog>
            </div>
          </v-sheet>
        </v-tabs-window-item>
        <v-tabs-window-item value="metadata">
          <v-sheet class="pa-3">
            <div @click.stop>
              <Treeselect
                v-model="metadataDownloadSelected"
                append-to-body
                class="flex-1-1-0"
                multiple
                value-consists-of="LEAF_PRIORITY"
                open-direction="below"
                :options="metadataOptions"
                placeholder="Select metadata types"
                z-index="2001"
                @open="treeMenuOpen = true"
                @close="treeMenuOpen = false"
              />
            </div>
            <v-dialog
              v-model="metadataTermsDialog"
              :width="400"
            >
              <template #activator="{ props: dialogProps }">
                <v-tooltip
                  :disabled="!downloadMetadataDisabledTooltip"
                  location="top"
                >
                  <template #activator="{ props: tooltipProps }">
                    <span v-bind="tooltipProps">
                      <v-btn
                        class="mt-3"
                        color="white"
                        :disabled="!!downloadMetadataDisabledTooltip"
                        v-bind="dialogProps"
                      >
                        <v-icon class="pr-3">
                          mdi-download
                        </v-icon>
                        Download Metadata Zip
                      </v-btn>
                    </span>
                  </template>
                  <span>{{ downloadMetadataDisabledTooltip }}</span>
                </v-tooltip>
              </template>
              <DownloadDialog
                :loading="metadataDownloadLoading"
                @clicked="downloadMetadata"
              />
            </v-dialog>
          </v-sheet>
        </v-tabs-window-item>
      </v-tabs-window>
    </v-sheet>
  </v-menu>
  <v-snackbar
    v-model="loading"
    location="right bottom"
    timeout="-1"
  >
    <v-progress-circular
      indeterminate
      class="mr-3"
    />
    <span>
      Preparing data products for download
    </span>
  </v-snackbar>
  <v-snackbar
    v-model="metadataDownloadLoading"
    location="right bottom"
    timeout="-1"
  >
    <v-progress-circular
      indeterminate
      class="mr-3"
    />
    <span>
      Downloading metadata
    </span>
  </v-snackbar>
  <ErrorDialog
    v-model:show="errorDialog"
  />
</template>

<style scoped>
.download-menu {
  width: 550px;
}

.vue3-treeselect {
  z-index: 2001;
}
</style>