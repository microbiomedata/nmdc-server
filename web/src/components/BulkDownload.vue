<script lang="ts">
import { computed, defineComponent, ref } from '@vue/composition-api';
import { stateRefs, dataObjectFilter } from '@/store';
// @ts-ignore
import Treeselect from '@riophae/vue-treeselect';
import DownloadDialog from '@/components/DownloadDialog.vue';
import useBulkDownload from '@/use/useBulkDownload';
import { humanFileSize } from '@/data/utils';

export default defineComponent({
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

  components: {
    DownloadDialog,
    Treeselect,
  },

  setup() {
    const termsDialog = ref(false);

    const {
      loading,
      downloadSummary,
      downloadOptions,
      download,
    } = useBulkDownload(stateRefs.conditions, dataObjectFilter);

    const options = computed(() => Object.entries(downloadOptions.value)
      .map(([key, val]) => ({
        id: key,
        label: `${key} (${val.count})`,
        children: Object.entries(val.file_types).map(([filetype, count]) => ({
          id: `${key}::${filetype}`,
          label: `${filetype} (${count})`,
        })),
      })));

    async function createAndDownload() {
      const val = await download();
      termsDialog.value = false;
      window.location.assign(val.url);
    }

    return {
      bulkDownloadSelected: stateRefs.bulkDownloadSelected,
      options,
      loading,
      downloadSummary,
      termsDialog,
      createAndDownload,
      humanFileSize,
    };
  },
});
</script>

<template>
  <v-card
    outlined
    class="pa-3 d-flex flex-column align-end"
    color="primary"
  >
    <span
      class="text-caption font-weight-bold white--text"
    >
      <template v-if="disabled">
        Log in with OrcID to use bulk download.
      </template>
      <template v-else-if="downloadSummary.count === 0">
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
        <template #activator="{ on, attrs }">
          <v-icon
            small
            color="white"
            v-bind="attrs"
            class="pr-2"
            v-on="on"
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
        :disabled="disabled"
        :placeholder="disabled ? 'Log in to bulk download' : 'Select file type'"
      />
      <v-dialog
        v-if="!disabled"
        v-model="termsDialog"
        :width="400"
        :disabled="downloadSummary.count === 0"
      >
        <template #activator="{ on, attrs }">
          <v-btn
            class="ml-3"
            color="white"
            depressed
            v-bind="attrs"
            v-on="on"
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
    </div>
  </v-card>
</template>
