<script lang="ts">
import {
  computed, defineComponent, ref, nextTick, PropType,
} from '@vue/composition-api';
import { HARMONIZER_TEMPLATES, IFRAME_BASE, useHarmonizerApi } from './harmonizerApi';

export default defineComponent({
  props: {
    templateName: {
      type: String as PropType<keyof typeof HARMONIZER_TEMPLATES>,
      required: true,
    },
  },
  setup(props) {
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

    const templateFolderName = computed(() => HARMONIZER_TEMPLATES[props.templateName].folder);

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
    <div class="d-flex flex-column px-4">
      <div class="d-flex align-center justify-center py-2">
        <v-btn
          color="primary"
          class="mr-2"
          @click="harmonizerApi.openFile()"
        >
          <v-icon class="pr-2">
            mdi-file-table
          </v-icon>
          Import data
        </v-btn>
        <v-autocomplete
          v-model="jumpToModel"
          :items="fields"
          label="Jump to column..."
          class="shrink"
          outlined
          dense
          hide-details
          @focus="focus"
          @change="jumpTo"
        />
        <v-spacer />
        <v-btn
          class="mx-2"
          outlined
          rel="noopener noreferrer"
          target="_blank"
          :href="`${IFRAME_BASE}/DataHarmonizer/template/${templateFolderName}/reference.html`"
        >
          <v-icon class="pr-2">
            mdi-information
          </v-icon>
          Reference Guide
        </v-btn>
        <v-btn
          color="primary"
          class="mx-2"
          @click="harmonizerApi.validate"
        >
          <v-icon class="pr-2">
            mdi-refresh
          </v-icon>
          Validate
        </v-btn>
        <v-text-field
          class="shrink"
          dense
          outlined
          readonly
          hide-details
          label="Chosen template"
          :value="templateName"
        />
      </div>
      <div
        v-if="validationErrors.length"
        class="d-flex flex-row py-1"
      >
        <div class="mr-2 text-h5 font-weight-bold shrink">
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
    <iframe
      ref="iframeElement"
      title="Data Harmonizer"
      width="100%"
      height="100%"
      :src="`${IFRAME_BASE}/DataHarmonizer/main.html?minified=true&template=${templateFolderName}`"
    />
  </div>
</template>
