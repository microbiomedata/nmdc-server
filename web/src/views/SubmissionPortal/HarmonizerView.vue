<script lang="ts">
import {
  computed, defineComponent, ref, nextTick, watch, onMounted, shallowRef,
} from '@vue/composition-api';
import {
  clamp, flattenDeep, has, sum,
} from 'lodash';
import { read, writeFile, utils } from 'xlsx';
import { urlify } from '@/data/utils';
import useRequest from '@/use/useRequest';

import { HarmonizerApi, HARMONIZER_TEMPLATES } from './harmonizerApi';
import {
  packageName,
  samplesValid,
  sampleData,
  status,
  submit,
  incrementalSaveRecord,
  templateList,
  mergeSampleData,
  hasChanged,
  SubmissionStatus,
  submissionStatus,
} from './store';
import FindReplace from './Components/FindReplace.vue';
import SubmissionStepper from './Components/SubmissionStepper.vue';

interface ValidationErrors {
  [error: string]: [number, number][],
}

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

const EXPORT_FILENAME = 'nmdc_sample_export.xlsx';

// controls which field is used to merge data from different DH views
const SCHEMA_ID = 'source_mat_id';

// used in determining which rows are shown in each view
const TYPE_FIELD = 'analysis_type';

// TODO: should this be derived from schema?
const COMMON_COLUMNS = ['samp_name', SCHEMA_ID, TYPE_FIELD];

// TODO: can this be imported from elsewhere?
const EMSL = 'emsl';
const JGI_MG = 'jgi_mg';
const JGT_MT = 'jgi_mt';

export default defineComponent({
  components: { FindReplace, SubmissionStepper },

  setup(_, { root }) {
    const harmonizerElement = ref();
    const harmonizerApi = new HarmonizerApi();
    const jumpToModel = ref();
    const highlightedValidationError = ref(0);
    const validationActiveCategory = ref('All Errors');
    const columnVisibility = ref('all');
    const sidebarOpen = ref(true);
    const invalidCells = shallowRef({} as Record<string, Record<number, Record<number, string>>>);

    const activeTemplateKey = ref(templateList.value[0]);
    const activeTemplate = ref(HARMONIZER_TEMPLATES[activeTemplateKey.value]);
    const activeTemplateData = computed(() => {
      if (!activeTemplate.value.sampleDataSlot) {
        return [];
      }
      return sampleData.value[activeTemplate.value.sampleDataSlot] || [];
    });
    const activeInvalidCells = computed(() => invalidCells.value[activeTemplateKey.value] || {});

    const submitDialog = ref(false);

    watch(activeTemplateData, () => {
      harmonizerApi.loadData(activeTemplateData.value);
      // if we're not on the first tab, the common columns should be read-only
      if (activeTemplateKey.value !== templateList.value[0]) {
        harmonizerApi.setColumnsReadOnly([0, 1, 2]);
        harmonizerApi.setMaxRows(activeTemplateData.value.length);
      }
    });

    watch(activeInvalidCells, () => {
      harmonizerApi.setInvalidCells(activeInvalidCells.value);
    });

    const validationErrors = computed(() => {
      const remapped: ValidationErrors = {};
      const invalid: Record<number, Record<number, string>> = activeInvalidCells.value;
      if (Object.keys(invalid).length) {
        remapped['All Errors'] = [];
      }
      Object.entries(invalid).forEach(([row, rowErrors]) => {
        Object.entries(rowErrors).forEach(([col, errorText]) => {
          const entry: [number, number] = [parseInt(row, 10), parseInt(col, 10)];
          const issue = errorText || 'Validation Error';
          if (has(remapped, issue)) {
            remapped[issue].push(entry);
          } else {
            remapped[issue] = [entry];
          }
          remapped['All Errors'].push(entry);
        });
      });
      return remapped;
    });

    const validationErrorGroups = computed(() => Object.keys(validationErrors.value));

    const validationTotalCounts = computed(() => Object.fromEntries(
      Object.entries(invalidCells.value).map(([template, cells]) => ([
        template,
        sum(Object.values(cells).map((row) => Object.keys(row).length)),
      ])),
    ));

    const onDataChange = () => {
      hasChanged.value += 1;
      const data = harmonizerApi.exportJson();
      mergeSampleData(activeTemplate.value.sampleDataSlot, data);
      incrementalSaveRecord(root.$route.params.id);
    };

    onMounted(async () => {
      console.log(status);
      const r = document.getElementById('harmonizer-root');
      if (r) {
        await harmonizerApi.init(r, activeTemplate.value.schemaClass);
        await nextTick();
        harmonizerApi.loadData(activeTemplateData.value);
        harmonizerApi.addChangeHook(onDataChange);
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

    function errorClick(index: number) {
      const currentSeries = validationErrors.value[validationActiveCategory.value];
      highlightedValidationError.value = clamp(index, 0, currentSeries.length - 1);
      const currentError = currentSeries[highlightedValidationError.value];
      harmonizerApi.jumpToRowCol(currentError[0], currentError[1]);
    }

    async function validate() {
      const data = harmonizerApi.exportJson();
      mergeSampleData(activeTemplate.value.sampleDataSlot, data);
      const result = await harmonizerApi.validate();
      const valid = Object.keys(result).length === 0;
      if (!valid && !sidebarOpen.value) {
        sidebarOpen.value = true;
      }
      invalidCells.value = {
        ...invalidCells.value,
        [activeTemplateKey.value]: result,
      };
      incrementalSaveRecord(root.$route.params.id);
      if (valid === false) {
        errorClick(0);
        samplesValid.value = false;
      } else {
        samplesValid.value = true;
      }
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

    const validationItems = computed(() => validationErrorGroups.value.map((errorGroup) => {
      const errors = validationErrors.value[errorGroup];
      return {
        text: `${errorGroup} (${errors.length})`,
        value: errorGroup,
      };
    }));

    watch(validationActiveCategory, () => errorClick(0));
    watch(columnVisibility, () => {
      harmonizerApi.changeVisibility(columnVisibility.value);
    });

    const selectedHelpDict = computed(() => {
      if (harmonizerApi.selectedColumn.value) {
        return harmonizerApi.getHelp(harmonizerApi.selectedColumn.value);
      }
      return null;
    });

    const { request, loading: submitLoading, count: submitCount } = useRequest();
    const doSubmit = () => request(async () => {
      const data = await harmonizerApi.exportJson();
      mergeSampleData(activeTemplate.value.sampleDataSlot, data);
      await submit(root.$route.params.id, SubmissionStatus.SubmittedPendingReview);
      submitDialog.value = false;
    });

    function rowIsVisibleForTemplate(row: Record<string, any>, templateKey: string) {
      if (templateKey === templateList.value[0]) {
        return true;
      }
      const row_types = row[TYPE_FIELD];
      if (!row_types) {
        return false;
      }
      if (templateKey === EMSL) {
        return row_types.includes('metaproteomics')
          || row_types.includes('metabolomics')
          || row_types.includes('natural organic matter');
      }
      if (templateKey === JGI_MG) {
        return row_types.includes('metagenomics');
      }
      if (templateKey === JGT_MT) {
        return row_types.includes('metatranscriptomics');
      }
      return false;
    }

    function synchronizeTabData(templateKey: string) {
      if (templateKey === templateList.value[0]) {
        return;
      }
      const nextData = { ...sampleData.value };
      const templateSlot = HARMONIZER_TEMPLATES[templateKey].sampleDataSlot;
      const environmentSlot = HARMONIZER_TEMPLATES[templateList.value[0]].sampleDataSlot;

      if (!templateSlot || !environmentSlot) {
        return;
      }

      // ensure the necessary keys exist in the data object
      if (!nextData[environmentSlot]) {
        nextData[environmentSlot] = [];
      }
      if (!nextData[templateSlot]) {
        nextData[templateSlot] = [];
      }

      // add/update any rows from the first tab to the active tab if they apply and if
      // they aren't there already.
      nextData[environmentSlot].forEach((row) => {
        const rowId = row[SCHEMA_ID];
        const existing = nextData[templateSlot] && nextData[templateSlot].find((r) => r[SCHEMA_ID] === rowId);
        if (!existing && rowIsVisibleForTemplate(row, templateKey)) {
          const newRow = {} as Record<string, any>;
          COMMON_COLUMNS.forEach((col) => {
            newRow[col] = row[col];
          });
          nextData[templateSlot].push(newRow);
        }
        if (existing) {
          COMMON_COLUMNS.forEach((col) => {
            existing[col] = row[col];
          });
        }
      });
      // remove any rows from the active tab if they were removed from the first tab
      // or no longer apply to the active tab
      if (nextData[templateSlot].length > 0) {
        nextData[templateSlot] = nextData[templateSlot].filter((row) => {
          if (!rowIsVisibleForTemplate(row, templateKey)) {
            return false;
          }
          const rowId = row[SCHEMA_ID];
          const environmentRow = nextData[environmentSlot].findIndex((r) => r[SCHEMA_ID] === rowId);
          return environmentRow >= 0;
        });
      }
      sampleData.value = nextData;
    }

    async function downloadSamples() {
      templateList.value.forEach((templateKey) => {
        synchronizeTabData(templateKey);
      });

      const workbook = utils.book_new();
      templateList.value.forEach((templateKey) => {
        const template = HARMONIZER_TEMPLATES[templateKey];
        if (!template.sampleDataSlot || !template.schemaClass) {
          return;
        }
        const worksheet = utils.json_to_sheet([
          harmonizerApi.getHeaderRow(template.schemaClass),
          ...HarmonizerApi.flattenArrayValues(sampleData.value[template.sampleDataSlot]),
        ], {
          skipHeader: true,
        });
        utils.book_append_sheet(workbook, worksheet, template.displayName);
      });
      writeFile(workbook, EXPORT_FILENAME, { compression: true });
    }

    function showOpenFileDialog() {
      document.getElementById('tsv-file-select')?.click();
    }

    function openFile(file: File) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event == null || event.target == null) {
          return;
        }
        const workbook = read(event.target.result);
        const imported = {} as Record<string, any>;
        Object.entries(workbook.Sheets).forEach(([name, worksheet]) => {
          const template = Object.values(HARMONIZER_TEMPLATES).find((template) => template.displayName === name);
          if (!template || !template.sampleDataSlot || !template.schemaClass) {
            return;
          }
          imported[template.sampleDataSlot] = harmonizerApi.unflattenArrayValues(
            utils.sheet_to_json(worksheet, {
              header: harmonizerApi.getOrderedAttributeNames(template.schemaClass),
              range: 1,
            }),
            template.schemaClass,
          );
        });
        harmonizerApi.setInvalidCells({});
        sampleData.value = imported;
        incrementalSaveRecord(root.$route.params.id);
      };
      reader.readAsArrayBuffer(file);
    }

    async function changeTemplate(index: number) {
      if (!harmonizerApi.ready.value) {
        return;
      }

      onDataChange();

      await validate();

      // When changing templates we may need to populate the common columns
      // from the first tab
      const nextTemplate = templateList.value[index];
      synchronizeTabData(nextTemplate);

      activeTemplateKey.value = nextTemplate;
      activeTemplate.value = HARMONIZER_TEMPLATES[nextTemplate];
      harmonizerApi.useTemplate(HARMONIZER_TEMPLATES[nextTemplate].schemaClass);
      harmonizerApi.addChangeHook(onDataChange);
    }

    return {
      ColorKey,
      HARMONIZER_TEMPLATES,
      columnVisibility,
      harmonizerElement,
      jumpToModel,
      harmonizerApi,
      samplesValid,
      submitLoading,
      submitCount,
      selectedHelpDict,
      packageName,
      fields,
      highlightedValidationError,
      sidebarOpen,
      validationItems,
      validationActiveCategory,
      templateList,
      activeTemplate,
      invalidCells,
      validationErrors,
      validationErrorGroups,
      validationTotalCounts,
      submissionStatus,
      status,
      submitDialog,
      /* methods */
      doSubmit,
      downloadSamples,
      errorClick,
      showOpenFileDialog,
      openFile,
      focus,
      jumpTo,
      validate,
      changeTemplate,
      urlify,
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
    <div class="d-flex flex-column px-2">
      <div class="d-flex align-center">
        <label
          for="tsv-file-select"
        >
          <input
            id="tsv-file-select"
            type="file"
            style="position: fixed; top: -100em"
            accept=".xls,.xlsx"
            @change="(evt) => openFile(evt.target.files[0])"
          >
          <v-btn
            label="Choose spreadsheet file..."
            prepend-inner-icon="mdi-file-table"
            :prepend-icon="null"
            outlined
            dense
            color="primary"
            class="mr-2"
            hide-details
            @click="showOpenFileDialog"
          >
            1. Import XLSX file
            <v-icon class="pl-2">
              mdi-file-table
            </v-icon>
          </v-btn>
        </label>
        <v-btn
          v-if="validationErrorGroups.length == 0"
          color="primary"
          outlined
          @click="validate"
        >
          2. Validate
          <v-icon class="pl-2">
            mdi-refresh
          </v-icon>
        </v-btn>
        <v-card
          v-if="validationErrorGroups.length"
          color="error"
          width="600"
          class="d-flex py-2 align-center"
        >
          <v-select
            v-model="validationActiveCategory"
            :items="validationItems"
            solo
            color="error"
            style="z-index: 200 !important; background-color: red;"
            dense
            class="mx-2"
            hide-details
          >
            <template #selection="{ item }">
              <p
                style="font-size: 14px"
                class="my-0"
              >
                {{ item.text }}
              </p>
            </template>
          </v-select>
          <div class="d-flex align-center mx-2">
            <v-icon
              @click="errorClick(highlightedValidationError - 1)"
            >
              mdi-arrow-left-circle
            </v-icon>
            <v-spacer />
            <span class="mx-1">
              ({{ highlightedValidationError + 1 }}/{{ validationErrors[validationActiveCategory].length }})
            </span>
            <v-spacer />
            <v-icon
              @click="errorClick(highlightedValidationError + 1)"
            >
              mdi-arrow-right-circle
            </v-icon>
          </div>
          <v-btn
            outlined
            small
            class="mx-2"
            @click="validate"
          >
            <v-icon class="pr-2">
              mdi-refresh
            </v-icon>
            Re-validate
          </v-btn>
        </v-card>
        <v-spacer />
        <v-autocomplete
          v-model="jumpToModel"
          :items="fields"
          label="Jump to column..."
          class="shrink mr-2"
          style="z-index: 200 !important;"
          outlined
          dense
          hide-details
          offset-y
          :menu-props="{ maxHeight: 500 }"
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
            width="280"
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
      </div>
    </div>

    <v-tabs @change="changeTemplate">
      <v-tab
        v-for="templateKey in templateList"
        :key="templateKey"
      >
        <v-badge
          :content="validationTotalCounts[templateKey]"
          :value="validationTotalCounts[templateKey] > 0"
          color="error"
        >
          {{ HARMONIZER_TEMPLATES[templateKey].displayName }}
        </v-badge>
      </v-tab>
    </v-tabs>

    <div>
      <div
        class="harmonizer-style-container"
        :style="{
          'margin-right': sidebarOpen ? '300px' : '0px'
        }"
      >
        <div id="harmonizer-root" />
      </div>

      <div
        :style="{
          'float': 'right',
          'width': sidebarOpen ? '300px' : '0px',
          'margin-top': '9px',
          'font-size': '14px',
          'height': 'calc(100vh - 362px)'
        }"
      >
        <v-btn
          class="sidebar-toggle"
          small
          outlined
          tile
          @click="sidebarOpen = !sidebarOpen"
        >
          <v-icon
            v-if="sidebarOpen"
            class="sidebar-toggle-close"
          >
            mdi-menu-open
          </v-icon>
          <v-icon v-else>
            mdi-menu-open
          </v-icon>
        </v-btn>
        <v-navigation-drawer
          width="100%"
          :value="sidebarOpen"
          right
        >
          <FindReplace
            :harmonizer-api="harmonizerApi"
            class="ml-2 mr-2"
          />
          <div
            v-if="selectedHelpDict"
            class="mx-2"
          >
            <div class="text-h6 mt-3 font-weight-bold d-flex align-center">
              Column Help
              <v-spacer />
            </div>
            <div class="my-2">
              <span class="font-weight-bold pr-2">Column:</span>
              <span
                :title="selectedHelpDict.name"
                v-html="selectedHelpDict.title"
              />
            </div>
            <div class="my-2">
              <span class="font-weight-bold pr-2">Description:</span>
              <span v-html="urlify(selectedHelpDict.description)" />
            </div>
            <div class="my-2">
              <span class="font-weight-bold pr-2">Guidance:</span>
              <span v-html="urlify(selectedHelpDict.guidance)" />
            </div>
            <div
              v-if="selectedHelpDict.examples"
              class="my-2"
            >
              <span class="font-weight-bold pr-2">Examples:</span>
              <span v-html="urlify(selectedHelpDict.examples)" />
            </div>
            <v-btn
              color="grey"
              outlined
              small
              block
              @click="harmonizerApi.launchReference()"
            >
              Full {{ activeTemplate.displayName }} Reference
              <v-icon class="pl-1">
                mdi-open-in-new
              </v-icon>
            </v-btn>
          </div>
        </v-navigation-drawer>
      </div>
    </div>

    <div class="harmonizer-style-container">
      <div id="harmonizer-footer-root" />
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
        Download XLSX
      </v-btn>
      <v-btn
        color="primary"
        depressed
        :disabled="!samplesValid || status !== submissionStatus.InProgress || submitCount > 0"
        :loading="submitLoading"
        @click="submitDialog = true"
      >
        <span v-if="status === submissionStatus.SubmittedPendingReview || submitCount">
          <v-icon>mdi-check-circle</v-icon>
          Done
        </span>
        <span v-else>
          3. Submit
        </span>
        <v-dialog
          v-model="submitDialog"
          activator="parent"
          width="auto"
        >
          <v-card>
            <v-card-title>
              Submit
            </v-card-title>
            <v-card-text>You are about to submit this study and metadata for NMDC review. Would you like to continue?</v-card-text>
            <v-card-actions>
              <v-btn
                color="primary"
                class="mr-2"
                @click="doSubmit"
              >
                Yes- Submit
              </v-btn>
              <v-btn @click="submitDialog = false">
                Cancel
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-btn>
    </div>
  </div>
</template>

<style lang="scss">
/*
  https://developer.mozilla.org/en-US/docs/Web/CSS/overscroll-behavior#examples
  Prevent back button overscrolling
  Chrome-only
*/
html {
  margin: 0;
  overscroll-behavior: none;
}

.spreadsheet-input {
  width: 0px;
}

.harmonizer-style-container {
  /**
    Namespace these styles so that they don't affect the global styles.
    Read more about SASS interpolation: https://sass-lang.com/documentation/interpolation
    This stylesheet is loaded from node_modules rather than a CDN because we need an SCSS file
    See comment below.

    There's also some kind of performance bottleneck with "Force Reflow" when you include the whole
    stylesheet, so I brought in the minimum modules for things not to break.
  */
  @import '~bootstrap/scss/functions';
  @import '~bootstrap/scss/variables';
  @import '~bootstrap/scss/mixins';
  @import '~bootstrap/scss/modal';
  @import '~bootstrap/scss/buttons';
  @import '~bootstrap/scss/forms';
  @import '~bootstrap/scss/input-group';
  @import '~bootstrap/scss/utilities';

  @import '~data-harmonizer/lib/dist/es/index';
}

.handsontable.listbox td {
  border-radius:3px;
  border:1px solid silver;
  background-color: #DDD;

  &:hover, &.current.highlight {
    background-color: lightblue !important;
  }
}

/* Grid */
#harmonizer-root {
  overflow: hidden;
  height: calc(100vh - 362px) !important;
  float: left;
  margin-top: 8px;

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

.field-description-text select {min-width: 95%}

#harmonizer-footer-root {
  width: 50%;
  padding: 12px 0;
}

.HandsontableCopyPaste {
  display: none;
}

.sidebar-toggle {
  margin-top: -1px;
  margin-left: -50px;
  background: white;
  z-index: 500;
  position: absolute;
  border-color:rgb(152, 152, 152);
  border-right-color: rgba(152, 152, 152, 0.0);
}

.sidebar-toggle-close {
  transform: rotate(180deg);
}

</style>
