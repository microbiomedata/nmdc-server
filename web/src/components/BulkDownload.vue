<script lang="ts">
import { computed, defineComponent, ref, watch } from 'vue';
// @ts-ignore
import Treeselect from '@zanmato/vue3-treeselect';
import { stateRefs, dataObjectFilter } from '@/store';
import DownloadDialog from '@/components/DownloadDialog.vue';
import useBulkDownload from '@/use/useBulkDownload';
import { humanFileSize } from '@/data/utils';
import { api } from '@/data/api';

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
    const termsDialog = ref(false);
    const downloadMenuOpen = ref(false);
    const treeMenuOpen = ref(false);
    const tab = ref('one');

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

    const options = computed(() => {
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

    async function createAndDownload() {
      const val = await download();
      termsDialog.value = false;
      window.location.assign(val.url);
    }

    function handleLoginClick() {
      api.initiateOrcidLogin();
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
      bulkDownloadSelected: stateRefs.bulkDownloadSelected,
      options,
      loading,
      downloadSummary,
      termsDialog,
      createAndDownload,
      humanFileSize,
      handleLoginClick,
      tab,
      downloadMenuOpen,
      treeMenuOpen,
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
        </v-tab>
        <v-tab value="metadata">
          Metadata
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
            <div class="d-flex flex-row align-center justify-space-between mb-2">
              <div class="d-flex flex-row align-center mr-3">
                <div class="pr-2 text-caption font-weight-bold">
                  Bulk Download
                </div>
                <v-tooltip
                  left
                  nudge-bottom="20px"
                  min-width="300px"
                  max-width="300px"
                >
                  <template #activator="{ props }">
                    <v-icon
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
              </div>
              <span
                class="text-caption font-weight-bold white--text"
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
            </div>
            <div>
              <div @click.stop>
                <Treeselect
                  v-model="bulkDownloadSelected"
                  append-to-body
                  class="flex-1-1-0"
                  multiple
                  value-consists-of="LEAF_PRIORITY"
                  open-direction="below"
                  :options="options"
                  placeholder="Select file type"
                  z-index="2001"
                  @open="treeMenuOpen = true"
                  @close="treeMenuOpen = false"
                />
              </div>
              <v-dialog
                v-model="termsDialog"
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
                    Download ZIP
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
            <v-btn
              @click="termsDialog = true"
            >
              <v-icon class="pr-3">
                mdi-download
              </v-icon>
              Samples JSON
            </v-btn>
          </v-sheet>
        </v-tabs-window-item>
      </v-tabs-window>
    </v-sheet>
  </v-menu>
</template>

<style scoped>
.download-menu {
  width: 500px;
}

.vue3-treeselect {
  z-index: 2001;
}
</style>