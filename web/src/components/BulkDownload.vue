<script lang="ts">
import { computed, defineComponent, ref, watch } from 'vue';
// @ts-ignore
import Treeselect from '@zanmato/vue3-treeselect';
import { stateRefs, dataObjectFilter } from '@/store';
import DownloadDialog from '@/components/DownloadDialog.vue';
import useBulkDownload from '@/use/useBulkDownload';
import { humanFileSize } from '@/data/utils';
import { api } from '@/data/api';
import { downloadBlob } from '@/utils';

export default defineComponent({

  components: {
    DownloadDialog,
    Treeselect,
  },
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
    searchResultCount: {
      type: Number,
      default: 0,
    },
  },

  setup() {
    const errorDialog = ref(false);
    const bulkTermsDialog = ref(false);
    const metadataTermsDialog = ref(false);
    const metadataDownloadLoading = ref(false);
    const downloadMenuOpen = ref(false);
    const treeMenuOpen = ref(false);
    const tab = ref('one');
    const metadataDownloadSelected = ref<string[]>([]);

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

    async function downloadSamplesMetadata() {
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
        metadataTermsDialog.value = false;
        metadataDownloadLoading.value = false;
      }
    }

    watch(
      () => downloadMenuOpen.value,
      (newVal) => {
        if (newVal === false && treeMenuOpen.value === true) {
          downloadMenuOpen.value = true;
        }
      },
    );

    return {
      errorDialog,
      bulkDownloadSelected: stateRefs.bulkDownloadSelected,
      dataProductOptions,
      metadataOptions,
      loading,
      downloadSummary,
      bulkTermsDialog,
      metadataTermsDialog,
      createAndDownload,
      humanFileSize,
      handleLoginClick,
      tab,
      downloadMenuOpen,
      treeMenuOpen,
      downloadSamplesMetadata,
      metadataDownloadSelected,
      metadataDownloadLoading,
    };
  },
});
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
          <v-card
            variant="flat"
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
                :disabled="downloadSummary.count === 0"
              >
                <template #activator="{ props }">
                  <v-btn
                    class="mt-3"
                    color="white"
                    v-bind="props"
                  >
                    <v-icon class="pr-3">
                      mdi-download
                    </v-icon>
                    Download Data Products ZIP
                  </v-btn>
                </template>
                <DownloadDialog
                  :loading="loading"
                  @clicked="createAndDownload"
                />
              </v-dialog>
            </div>
          </v-card>
        </v-tabs-window-item>
        <v-tabs-window-item value="metadata">
          <v-sheet class="pa-5">
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
              :disabled="metadataDownloadSelected.length === 0"
            >
              <template #activator="{ props }">
                <v-btn
                  class="mt-3"
                  color="white"
                  v-bind="props"
                >
                  <v-icon class="pr-3">
                    mdi-download
                  </v-icon>
                  Download Metadata Zip
                </v-btn>
              </template>
              <DownloadDialog
                :loading="metadataDownloadLoading"
                @clicked="downloadSamplesMetadata"
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
      Downloading data products
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
  <v-dialog
    v-model="errorDialog"
    :width="500"
  >
    <v-card>
      <v-card-title>
        <v-icon
          color="error"
        >
          mdi-alert-circle
        </v-icon>
        Download Failed
      </v-card-title>
      <v-card-text>
        Your download could not be completed at this time.
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn
          color="primary"
          text
          @click="errorDialog = false"
        >
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.download-menu {
  width: 550px;
}

.vue3-treeselect {
  z-index: 2001;
}
</style>