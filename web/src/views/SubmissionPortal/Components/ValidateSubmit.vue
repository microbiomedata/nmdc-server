<script lang="ts">
import { defineComponent } from 'vue';
import { writeFile, utils } from 'xlsx';
import { submit, submitPayload } from '../store';
import { saveAs } from '@/util';
import useRequest from '@/use/useRequest';

export default defineComponent({
  setup(_, { root }) {
    // TODO: https://github.com/microbiomedata/nmdc-server/issues/852
    function downloadSamples() {
      const worksheet = utils.aoa_to_sheet([]);
      const workbook = utils.book_new();
      utils.book_append_sheet(workbook, worksheet, 'Sheet1');
      // @ts-ignore
      writeFile(workbook, 'nmdc_sample_export.tsv', { bookType: 'csv', FS: '\t' });
    }

    function downloadJson() {
      saveAs('nmdc_study.json', submitPayload.value);
    }

    const { request, loading: submitLoading, count: submitCount } = useRequest();
    const doSubmit = () => request(() => submit(root.$route.params.id));

    return {
      submitPayload,
      submitLoading,
      submitCount,
      downloadJson,
      downloadSamples,
      doSubmit,
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Submit
    </div>
    <div class="text-h5">
      Preview of the data submission
    </div>
    <v-card
      class="pa-3"
      outlined
      style="max-height: 550px; overflow-y: auto;"
    >
      <pre style="font-size: 14px">{{ submitPayload }}</pre>
    </v-card>
    <div class="d-flex my-3">
      <v-btn
        color="primary"
        class="mr-2"
        outlined
        @click="downloadJson"
      >
        <v-icon class="pr-2">
          mdi-file-code
        </v-icon>
        Download Full Submission JSON
      </v-btn>
      <v-btn
        color="primary"
        outlined
        @click="downloadSamples"
      >
        <v-icon class="pr-2">
          mdi-file-table
        </v-icon>
        Download Sample Metadata TSV
      </v-btn>
      <v-spacer />
      <v-btn
        color="primary"
        :loading="submitLoading"
        :disabled="submitLoading || submitCount > 0"
        @click="doSubmit"
      >
        <span v-if="submitCount === 0">Submit</span>
        <span v-else>Submission successful</span>
      </v-btn>
    </div>
  </div>
</template>
