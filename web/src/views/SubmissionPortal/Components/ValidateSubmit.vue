<script lang="ts">
import { computed, defineComponent } from '@vue/composition-api';
import { writeFile, utils } from 'xlsx';
import {
  studyForm, multiOmicsForm, templateName, sampleData,
} from '../store';
import { saveAs } from '@/util';

export default defineComponent({
  setup() {
    const payloadObject = computed(() => ({
      template: templateName.value,
      studyForm,
      multiOmicsForm,
      sampleData: sampleData.value,
    }));

    const payload = computed(() => {
      const value = JSON.stringify(payloadObject.value, null, 2);
      return value;
    });

    function downloadSamples() {
      const worksheet = utils.aoa_to_sheet(sampleData.value);
      const workbook = utils.book_new();
      utils.book_append_sheet(workbook, worksheet, 'Sheet1');
      // @ts-ignore
      writeFile(workbook, 'nmdc_sample_export.tsv', { bookType: 'csv', FS: '\t' });
    }

    function downloadJson() {
      saveAs('nmdc_study.json', payload.value);
    }

    function submit() {
      // console.log('whatever');
    }

    return {
      payload,
      downloadJson,
      downloadSamples,
      submit,
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
      <pre style="font-size: 14px">{{ payload }}</pre>
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
        @click="submit"
      >
        Submit
      </v-btn>
    </div>
  </div>
</template>
