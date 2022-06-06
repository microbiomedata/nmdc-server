<script lang="ts">
import {
  computed, defineComponent, ref, nextTick, watch, onMounted,
} from '@vue/composition-api';
import { flattenDeep } from 'lodash';
import { writeFile, utils } from 'xlsx';
import 'handsontable/dist/handsontable.full.css';

import useRequest from '@/use/useRequest';

import { HarmonizerApi } from './harmonizerApi';
import {
  packageName, samplesValid, sampleData, submit, incrementalSaveRecord, templateChoice,
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

  setup(_, { root }) {
    const harmonizerElement = ref();
    const harmonizerApi = new HarmonizerApi();
    const jumpToModel = ref();
    const highlightedValidationError = ref('');
    const columnVisibility = ref('all');

    onMounted(async () => {
      const r = document.getElementById('harmonizer-root');
      if (r) {
        await harmonizerApi.init(r);
        await nextTick();
        harmonizerApi.loadData(sampleData.value.slice(2));
      }
    });

    async function jumpTo({ row, column }: { row: number; column: number }) {
      harmonizerApi.jumpToRowCol(row, column);
      await nextTick();
      jumpToModel.value = null;
    }

    function focus() {
      window.focus();
    }

    async function validate() {
      const data = harmonizerApi.exportJson();
      sampleData.value = data;
      samplesValid.value = await harmonizerApi.validate();
      incrementalSaveRecord(root.$route.params.id);
    }

    function errorClick(row: number, column: number) {
      harmonizerApi.jumpToRowCol(row, column);
      highlightedValidationError.value = `${row}.${column}`;
    }

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

    watch(sampleData, () => {
      if (harmonizerApi.ready.value) {
        harmonizerApi.loadData(sampleData.value.slice(2));
      }
    });

    const { request, loading: submitLoading, count: submitCount } = useRequest();
    const doSubmit = () => request(async () => {
      const data = await harmonizerApi.exportJson();
      sampleData.value = data;
      await submit(root.$route.params.id);
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
      packageName,
      templateChoice,
      fields,
      validationErrors,
      highlightedValidationError,
      /* methods */
      doSubmit,
      downloadSamples,
      errorClick,
      focus,
      jumpTo,
      validate,
    };
  },
});
</script>

<template>
  <div
    style="overflow-y: hidden; overflow-x: hidden;"
    class="d-flex flex-column fill-height"
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
          @change="(evt) => harmonizerApi.openFile(evt)"
        />
        <v-autocomplete
          v-model="jumpToModel"
          :items="fields"
          label="Jump to column..."
          class="shrink mr-2"
          style="z-index: 200 !important;"
          outlined
          dense
          hide-details
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
          style="z-index: 200 !important;"
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
          @click="harmonizerApi.launchReference()"
        >
          {{ packageName }} Reference
          <v-icon class="pl-1">
            mdi-open-in-new
          </v-icon>
        </v-btn>
      </div>
    </div>
    <div class="harmonizer-container d-flex flex-row">
      <v-navigation-drawer
        v-if="validationErrors.length >= 1"
        width="260"
        class="grow"
        permanent
      >
        <template v-if="validationErrors.length">
          <div class="text-h6 mx-2">
            {{ validationErrors.length }} Validation Errors
          </div>
          <div
            style="overflow-x: auto;"
            class="d-flex flex-column"
          >
            <v-chip
              v-for="err in validationErrors"
              :key="`${err.row}.${err.column}`"
              color="error"
              class="mx-1 mb-1 grow mb-0 px-1"
              small
              :outlined="highlightedValidationError !== `${err.row}.${err.column}`"
              dark
              @click="errorClick(err.row, err.column)"
            >
              ({{ err.row }}, {{ err.column }}) {{ err.cell || 'Validation Error' }}
            </v-chip>
          </div>
        </template>
      </v-navigation-drawer>
      <div
        id="harmonizer-root"
        class="harmonizer-root"
        :style="{ 'width': validationErrors.length ? '100vw' : 'calc(100vw-260px)' }"
      />
    </div>
    <div class="d-flex shrink ma-2">
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

<style lang="scss">
// HACK-DH
// Import css from CDN.  We didn't need a SCSS file for this one because
// it doesn't have any globally conflicting styles.
@import 'https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.css';

.harmonizer-container {
  height: calc(100vh - 260px) !important;
}

.harmonizer-root {
  // Namespace these styles so that they don't affect the global styles.
  // Read more about SASS interpolation: https://sass-lang.com/documentation/interpolation

  // This stylesheet is loaded from node_modules rather than a CDN because we need an SCSS file
  // See comment below.
  @import '~bootstrap/scss/bootstrap.scss';
  // This stylesheet was unfortunately copy-pasted. In order to interpolate the content here,
  // an SCSS file is required (css will only be referenced).  There is no handsontable scss available,
  // so the CSS was renamed SCSS and copied into the project.  SCSS and CSS are treated differently
  // when imported within a parent scope (harmonizer-root class in this case)
  @import './library/handsontable.min.scss';
}
/* Grid */
#data-harmonizer-grid {
  overflow: hidden;
  height: calc(100vh - 340px) !important;
  margin-top: -16px;

  .secondary-header-cell:hover {
    cursor: pointer;
  }

  .htAutocompleteArrow {
    color: gray;
  }

  td {
    &.invalid-cell {
      background-color: #ffcccb !important;
    }
    &.empty-invalid-cell {
      background-color: #ff91a4 !important;
    }
  }
  th {
    text-align: left;

    &.required {
      background-color:yellow;
    }
    &.recommended {
      background-color:plum;
    }
  }
}

#loading-screen {
  display: none;
  background-color: rgba(108, 117, 125, 0.2);
  z-index: 1000;
}

#unmapped-headers-list {
  max-height: 50vh;
  overflow-y: auto;
}

/* Autocomplete */
.listbox {
  white-space: pre !important;
}
.handsontable.listbox td {
  border-radius:3px;
  border:1px solid silver;
  background-color: #DDD;

  &:hover, &.current.highlight {
    background-color: lightblue !important;
  }
}
</style>
