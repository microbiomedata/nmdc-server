<script lang="ts">
import {
  computed, defineComponent, ref, nextTick,
} from '@vue/composition-api';
import { HARMONIZER_TEMPLATES, IFRAME_BASE, useHarmonizerApi } from './harmonizerApi';

import { templateName } from './store';
import SubmissionStepper from './Components/SubmissionStepper.vue';

export default defineComponent({
  components: { SubmissionStepper },

  setup() {
    const iframeElement = ref();
    const harmonizerApi = useHarmonizerApi(iframeElement);
    const jumpToModel = ref();
    const highlightedValidationError = ref('');

    async function jumpTo(columnName: string) {
      harmonizerApi.jumpTo(columnName);
      await nextTick();
      jumpToModel.value = null;
    }

    function focus() {
      window.focus();
    }

    function errorClick(row: number, column: number) {
      harmonizerApi.jumpToRowCol(row, column);
      highlightedValidationError.value = `${row}.${column}`;
    }

    const templateFolderName = computed(() => (templateName.value ? HARMONIZER_TEMPLATES[templateName.value].folder : null));

    const fields = computed(() => Object.keys(harmonizerApi.schemaFields.value).sort((a, b) => {
      const nameA = a.toUpperCase();
      const nameB = b.toUpperCase();
      if (nameA < nameB) {
        return -1;
      }
      if (nameA > nameB) {
        return 1;
      }
      return 0;
    }));

    const validationErrors = computed(() => {
      if (harmonizerApi.validationErrors.value) {
        return Object.entries(harmonizerApi.validationErrors.value)
          .map(([row, val]) => Object.entries(val)
            .map(([column, cell]) => ({
              cell,
              row: Number.parseInt(row, 10),
              column: Number.parseInt(column, 10),
            }))).flat();
      }
      return [];
    });

    return {
      iframeElement,
      jumpToModel,
      harmonizerApi,
      templateName,
      templateFolderName,
      fields,
      validationErrors,
      highlightedValidationError,
      IFRAME_BASE,
      /* methods */
      errorClick,
      focus,
      jumpTo,
    };
  },
});
</script>

<template>
  <div
    style="overflow-y: hidden;"
    class="fill-height"
  >
    <SubmissionStepper />
    <div class="d-flex flex-column px-4">
      <div class="d-flex align-center justify-center py-2">
        <v-file-input
          label="Choose spreadsheet file..."
          prepend-inner-icon="mdi-file-table"
          :prepend-icon="null"
          outlined
          dense
          color="primary"
          hide-details
          class="mr-2"
          :truncate-length="50"
          @change="harmonizerApi.openFile"
        />
        <v-autocomplete
          v-model="jumpToModel"
          :items="fields"
          label="Jump to column..."
          class="shrink mr-2"
          outlined
          dense
          hide-details
          @focus="focus"
          @change="jumpTo"
        />
        <v-spacer />
        <v-btn
          color="accent"
          class="mr-2"
          @click="harmonizerApi.validate"
        >
          <v-icon class="pr-2">
            mdi-refresh
          </v-icon>
          Validate
        </v-btn>
        <v-text-field
          class="shrink mr-2"
          dense
          outlined
          readonly
          hide-details
          label="Schema template"
          :value="templateName"
        />
        <v-btn
          class="mr-2"
          color="grey"
          outlined
          rel="noopener noreferrer"
          target="_blank"
          :href="`${IFRAME_BASE}/template/${templateFolderName}/reference.html`"
        >
          <v-icon class="pr-2">
            mdi-information
          </v-icon>
          Schema reference
        </v-btn>
      </div>
      <div
        v-if="validationErrors.length"
        class="d-flex flex-row py-1"
      >
        <div class="mr-2 text-h5 font-weight-bold grow">
          {{ validationErrors.length }} Validation Errors:
        </div>
        <div
          style="overflow-x: auto;"
          class="d-flex flex-row"
        >
          <v-chip
            v-for="err in validationErrors"
            :key="`${err.row}.${err.column}`"
            color="error"
            class="mr-1 mb-2 grow mb-0"
            dense
            :outlined="highlightedValidationError !== `${err.row}.${err.column}`"
            dark
            @click="errorClick(err.row, err.column)"
          >
            {{ err.cell || 'Validation Error' }}
          </v-chip>
        </div>
      </div>
    </div>
    <div style="height: calc(100vh - 260px);">
      <iframe
        ref="iframeElement"
        title="Data Harmonizer"
        width="100%"
        height="100%"
        :src="`${IFRAME_BASE}/main.html?minified=true&template=${templateFolderName}`"
        sandbox="allow-popups allow-popups-to-escape-sandbox allow-scripts allow-modals allow-downloads allow-forms"
      />
    </div>
    <div class="d-flex grow ma-2">
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Environment Package' }"
      >
        <v-icon class="pr-1">
          mdi-arrow-left-circle
        </v-icon>
        Go to previous step
      </v-btn>
      <v-spacer />
      <v-btn
        color="primary"
        depressed
        :to="{ name: 'Validate And Submit' }"
      >
        <v-icon class="pr-1">
          mdi-arrow-right-circle
        </v-icon>
        Go to next step
      </v-btn>
    </div>
  </div>
</template>
