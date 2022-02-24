<script lang="ts">
import {
  computed, defineComponent, ref, nextTick, watch,
} from '@vue/composition-api';
import { flattenDeep } from 'lodash';
import { writeFile, utils } from 'xlsx';

import useRequest from '@/use/useRequest';

import { HARMONIZER_TEMPLATES, IFRAME_BASE, useHarmonizerApi } from './harmonizerApi';
import {
  templateName, samplesValid, sampleData, submit,
} from './store';
import SubmissionStepper from './Components/SubmissionStepper.vue';

const ColorKey = {
  required: {
    label: 'Required field',
    color: 'yellow',
  },
  recommended: {
    label: 'Recommended field',
    color: 'plum',
  },
  invalidCell: {
    label: 'Invalid cell',
    color: '#ffcccb',
  },
  emptyCell: {
    label: 'Empty invalid cell',
    color: '#ff91a4',
  },
};

export default defineComponent({
  components: { SubmissionStepper },

  setup() {
    const harmonizerElement = ref();
    const harmonizerApi = useHarmonizerApi(harmonizerElement);

    const jumpToModel = ref();
    const highlightedValidationError = ref('');
    const columnVisibility = ref('all');

    async function jumpTo({ row, column }: { row: number; column: number }) {
      harmonizerApi.jumpToRowCol(row, column);
      await nextTick();
      jumpToModel.value = null;
    }

    function focus() {
      window.focus();
    }

    async function validate() {
      const data = await harmonizerApi.exportJson();
      sampleData.value = data;
      samplesValid.value = await harmonizerApi.validate();
    }

    function errorClick(row: number, column: number) {
      harmonizerApi.jumpToRowCol(row, column);
      highlightedValidationError.value = `${row}.${column}`;
    }

    const templateFolderName = computed(() => (templateName.value ? HARMONIZER_TEMPLATES[templateName.value].folder : null));

    const fields = computed(() => flattenDeep(Object.entries(harmonizerApi.schemaSections.value)
      .map(([sectionName, children]) => Object.entries(children).map(([columnName, column]) => {
        const val = {
          text: columnName ? `  ${columnName}` : sectionName,
          value: {
            sectionName, columnName, column, row: 0,
          },
        };
        return val;
      }))));

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

    watch(columnVisibility, () => {
      harmonizerApi.changeVisibility(columnVisibility.value);
    });

    function hydrate() {
      harmonizerApi.loadData(sampleData.value);
    }

    const { request, loading: submitLoading, count: submitCount } = useRequest();
    const doSubmit = () => request(async () => {
      const data = await harmonizerApi.exportJson();
      sampleData.value = data;
      await submit();
    });

    async function downloadSamples() {
      const data = await harmonizerApi.exportJson();
      const worksheet = utils.aoa_to_sheet(data);
      const workbook = utils.book_new();
      utils.book_append_sheet(workbook, worksheet, 'Sheet1');
      // @ts-ignore
      writeFile(workbook, 'nmdc_sample_export.tsv', { bookType: 'csv', FS: '\t' });
    }

    return {
      ColorKey,
      columnVisibility,
      harmonizerElement,
      jumpToModel,
      harmonizerApi,
      samplesValid,
      submitLoading,
      submitCount,
      templateName,
      templateFolderName,
      fields,
      validationErrors,
      highlightedValidationError,
      IFRAME_BASE,
      /* methods */
      doSubmit,
      downloadSamples,
      errorClick,
      hydrate,
      focus,
      jumpTo,
      validate,
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
          height
          :menu-props="{ maxHeight: 600 }"
          @focus="focus"
          @change="jumpTo"
        >
          <template #item="{ item }">
            <span
              :class="{
                'pl-4': item.value.columnName !== '',
                'text-h5': item.value.columnName === '',
              }"
            >
              {{ item.value.columnName || item.value.sectionName }}
            </span>
          </template>
        </v-autocomplete>
        <v-menu
          offset-y
          nudge-bottom="4px"
          :close-on-click="true"
        >
          <template #activator="{on, attrs}">
            <v-btn
              outlined
              class="mr-2"
              v-bind="attrs"
              v-on="on"
            >
              <v-icon class="pr-1">
                mdi-eye
              </v-icon>
              <v-icon>
                mdi-menu-down
              </v-icon>
            </v-btn>
          </template>
          <v-card
            class="py-1 px-2"
            outlined
          >
            <v-radio-group
              v-model="columnVisibility"
              label="Column visibility"
            >
              <v-radio
                value="all"
              >
                <template #label>
                  <div class="black--text">
                    All Columns
                  </div>
                </template>
              </v-radio>
              <v-radio
                value="required"
              >
                <template #label>
                  <div class="black--text">
                    <span :style="{ 'background-color': ColorKey.required.color }">Required</span>
                    columns
                  </div>
                </template>
              </v-radio>
              <v-radio
                value="recommended"
              >
                <template #label>
                  <div class="black--text">
                    <span :style="{ 'background-color': ColorKey.required.color }">Required</span>
                    and
                    <span :style="{ 'background-color': ColorKey.recommended.color }">recommended</span>
                    columns
                  </div>
                </template>
              </v-radio>
              <v-divider class="mb-3" />
              <span
                class="grey--text text--darken-2 text-body-1 mb-2"
              >
                Show section
              </span>
              <v-radio
                v-for="(value, sectionName) in harmonizerApi.schemaSections.value"
                :key="sectionName"
                :value="sectionName"
              >
                <template #label>
                  <span>
                    {{ sectionName }}
                  </span>
                </template>
              </v-radio>
            </v-radio-group>
          </v-card>
        </v-menu>
        <v-spacer />
        <v-btn
          color="primary"
          class="mr-2"
          small
          @click="validate"
        >
          <v-icon class="pr-2">
            mdi-refresh
          </v-icon>
          Validate
        </v-btn>
        <v-btn
          class="mr-2"
          color="grey"
          outlined
          small
          rel="noopener noreferrer"
          target="_blank"
          :href="`${IFRAME_BASE}/template/${templateFolderName}/reference.html`"
          @load="hydrate"
        >
          {{ templateName }} Reference
          <v-icon class="pl-1">
            mdi-open-in-new
          </v-icon>
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
    <div :style="{ height: `calc(100vh - 260px  - ${validationErrors.length ? '48px' : '0px'})` }">
      <iframe
        ref="harmonizerElement"
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
      <div class="d-flex align-center">
        <span class="mr-1">Color key</span>
        <v-chip
          v-for="val in ColorKey"
          :key="val.label"
          :style="{ backgroundColor: val.color, opacity: 1 }"
          class="mr-1"
          disabled
        >
          {{ val.label }}
        </v-chip>
      </div>
      <v-spacer />
      <v-btn
        color="primary"
        class="mr-2"
        outlined
        @click="downloadSamples"
      >
        <v-icon class="pr-2">
          mdi-file-table
        </v-icon>
        Download TSV
      </v-btn>
      <v-btn
        color="primary"
        depressed
        :disabled="!samplesValid || submitCount > 0"
        :loading="submitLoading"
        @click="doSubmit"
      >
        <span v-if="submitCount > 0">
          <v-icon>mdi-check-circle</v-icon>
          Done
        </span>
        <span v-else>
          Submit
        </span>
      </v-btn>
    </div>
  </div>
</template>
