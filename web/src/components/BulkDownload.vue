<script lang="ts">
import { computed, defineComponent, ref } from 'vue';
// @ts-ignore
import Treeselect from '@riophae/vue-treeselect';
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

    const options = computed(() => Object.entries(downloadOptions.value)
      .map(([key, val]) => ({
        id: key,
        label: createLabelString(key, val.count, val.size),
        children: Object.entries(val.file_types).map(([filetype, fileTypeStats]) => ({
          id: `${key}::${filetype}`,
          label: createLabelString(filetype, fileTypeStats.count, fileTypeStats.size),
        })),
      })));

    async function createAndDownload() {
      const val = await download();
      termsDialog.value = false;
      window.location.assign(val.url);
    }

    function handleLoginClick() {
      api.initiateOrcidLogin();
    }

    return {
      bulkDownloadSelected: stateRefs.bulkDownloadSelected,
      options,
      loading,
      downloadSummary,
      termsDialog,
      createAndDownload,
      humanFileSize,
      handleLoginClick,
    };
  },
});
</script>

<template>
  <v-card
    variant="outlined"
    class="pa-3 d-flex flex-column align-end"
    color="primary"
  >
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
    <div class="d-flex flex-row align-center">
      <div class="white--text pr-2 text-caption grow font-weight-bold">
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
            small
            color="white"
            v-bind="props"
            class="pr-2"
          >
            mdi-help-circle
          </v-icon>
        </template>
        <span>
          Choose a group of files to download based on file type
          from the currently filtered search results.
        </span>
      </v-tooltip>
      <Treeselect
        v-model="bulkDownloadSelected"
        multiple
        value-consists-of="LEAF_PRIORITY"
        open-direction="below"
        :options="options"
        placeholder="Select file type"
      />
      <v-dialog
        v-if="!disabled"
        v-model="termsDialog"
        :width="400"
        :disabled="downloadSummary.count === 0"
      >
        <template #activator="{ props }">
          <v-btn
            class="ml-3"
            color="white"
            depressed
            v-bind="props"
          >
            Download ZIP
            <v-icon class="pl-3">
              mdi-download
            </v-icon>
          </v-btn>
        </template>
        <DownloadDialog
          :loading="loading"
          @clicked="createAndDownload"
        />
      </v-dialog>
      <v-chip
        v-else
        class="grow text-subtitle-1 ml-4"
        @click="handleLoginClick"
      >
        Log in to download
      </v-chip>
    </div>
  </v-card>
</template>
