<script lang="ts">
import {
  computed,
  defineComponent,
  ref,
  nextTick,
  watch,
  onMounted,
  shallowRef,
  getCurrentInstance,

} from 'vue';
import {
  clamp, flattenDeep, has, sum,
} from 'lodash';
import { read, writeFile, utils } from 'xlsx';
import { api } from '@/data/api.ts';
import { urlify } from '@/data/utils';
import useRequest from '@/use/useRequest';

import ContactCard from '@/views/SubmissionPortal/Components/ContactCard.vue';
import { APP_HEADER_HEIGHT } from '@/components/Presentation/AppHeader.vue';
import { stateRefs } from '@/store';
import {
  HarmonizerApi,
  HARMONIZER_TEMPLATES,
  EMSL,
  JGI_MG,
  JGT_MT,
  JGI_MG_LR,
} from './harmonizerApi';
import {
  packageName,
  sampleData,
  status,
  submit,
  incrementalSaveRecord,
  templateList,
  mergeSampleData,
  hasChanged,
  tabsValidated,
  submissionStatus,
  canEditSampleMetadata,
  isOwner,
  isTestSubmission,
} from './store';
import FindReplace from './Components/FindReplace.vue';
import SubmissionStepper from './Components/SubmissionStepper.vue';
import SubmissionDocsLink from './Components/SubmissionDocsLink.vue';
import SubmissionPermissionBanner from './Components/SubmissionPermissionBanner.vue';

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

const HELP_SIDEBAR_WIDTH = '300px';

const EXPORT_FILENAME = 'nmdc_sample_export.xlsx';

const SAMP_NAME = 'samp_name';
const SOURCE_MAT_ID = 'source_mat_id';
const ANALYSIS_TYPE = 'analysis_type';

// controls which field is used to merge data from different DH views
const SCHEMA_ID = SAMP_NAME;

// used in determining which rows are shown in each view
const TYPE_FIELD = ANALYSIS_TYPE;

// TODO: should this be derived from schema?
const COMMON_COLUMNS = [SAMP_NAME, SOURCE_MAT_ID, ANALYSIS_TYPE];

const ALWAYS_READ_ONLY_COLUMNS = [
  'dna_seq_project',
  'rna_seq_project',
  'dna_samp_id',
  'rna_samp_id',
  'rna_seq_project_pi',
  'dna_seq_project_pi',
  'dna_project_contact',
  'rna_project_contact',
  'proposal_rna',
  'proposal_dna',
  'rna_seq_project_name',
  'dna_seq_project_name',
];

export default defineComponent({
  components: {
    ContactCard,
    FindReplace,
    SubmissionStepper,
    SubmissionDocsLink,
    SubmissionPermissionBanner,
  },

  setup() {
    const root = getCurrentInstance();

    const { user } = stateRefs;

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

    const submitDialog = ref(false);

    const snackbar = ref(false);
    const importErrorSnackbar = ref(false);
    const notImportedWorksheetNames = ref([] as string[]);

    watch(activeTemplate, () => {
      // WARNING: It's important to do the column settings update /before/ data. Otherwise,
      // columns will not be rendered with the correct width.
      harmonizerApi.setColumnsReadOnly(ALWAYS_READ_ONLY_COLUMNS);

      // If the environment tab selected is a mixin it should be readonly
      const environmentList = templateList.value.filter((t) => HARMONIZER_TEMPLATES[t].status === 'mixin');
      if (environmentList.includes(activeTemplateKey.value)) {
        harmonizerApi.setColumnsReadOnly(COMMON_COLUMNS);
        harmonizerApi.setMaxRows(activeTemplateData.value.length);
      }
      harmonizerApi.loadData(activeTemplateData.value);
      harmonizerApi.setInvalidCells(invalidCells.value[activeTemplateKey.value] || {});
    });

    const validationErrors = computed(() => {
      const remapped: ValidationErrors = {};
      const invalid: Record<number, Record<number, string>> = invalidCells.value[activeTemplateKey.value] || {};
      if (Object.keys(invalid).length) {
        remapped['All Errors'] = [];
      }
      Object.entries(invalid).forEach(([row, rowErrors]) => {
        Object.entries(rowErrors).forEach(([col, errorText]) => {
          const entry: [number, number] = [parseInt(row, 10), parseInt(col, 10)];
          const issue = errorText || 'Other Validation Error';
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

    const saveRecordRequest = useRequest();
    const saveRecord = () => saveRecordRequest.request(() => incrementalSaveRecord(root?.proxy.$route.params.id as string));

    const onDataChange = async () => {
      hasChanged.value += 1;
      const data = harmonizerApi.exportJson();
      mergeSampleData(activeTemplate.value.sampleDataSlot, data);
      saveRecord(); // This is a background save that we intentionally don't wait for
      tabsValidated.value[activeTemplateKey.value] = false;
    };
    const { request: schemaRequest, loading: schemaLoading } = useRequest();
    onMounted(async () => {
      const [schema, goldEcosystemTree] = await schemaRequest(() => Promise.all([
        api.getSubmissionSchema(),
        api.getGoldEcosystemTree(),
      ]));
      const r = document.getElementById('harmonizer-root');
      if (r && schema) {
        await harmonizerApi.init(r, schema, activeTemplate.value.schemaClass, goldEcosystemTree);
        await nextTick();
        harmonizerApi.loadData(activeTemplateData.value);
        harmonizerApi.addChangeHook(onDataChange);
        if (!canEditSampleMetadata()) {
          harmonizerApi.setTableReadOnly();
        }
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
      saveRecord(); // This is a background save that we intentionally don't wait for
      if (valid === false) {
        errorClick(0);
      }
      tabsValidated.value = {
        ...tabsValidated.value,
        [activeTemplateKey.value]: valid,
      };

      snackbar.value = Object.values(tabsValidated.value).every((value) => value);
    }

    const canSubmit = computed(() => {
      let allTabsValid = true;
      Object.values(tabsValidated.value).forEach((value) => {
        allTabsValid = allTabsValid && value;
      });
      return allTabsValid && isOwner();
    });

    const fields = computed(() => flattenDeep(Object.entries(harmonizerApi.schemaSectionColumns.value)
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

    const { request: submitRequest, loading: submitLoading, count: submitCount } = useRequest();
    const doSubmit = () => submitRequest(async () => {
      const data = await harmonizerApi.exportJson();
      mergeSampleData(activeTemplate.value.sampleDataSlot, data);
      await submit(root?.proxy.$route.params.id as string, submissionStatus.SubmittedPendingReview);
      submitDialog.value = false;
    });

    function rowIsVisibleForTemplate(row: Record<string, any>, templateKey: string) {
      const environmentKeys = templateList.value.filter((t) => HARMONIZER_TEMPLATES[t].status === 'published');
      if (environmentKeys.includes(templateKey)) {
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
      if (templateKey === JGI_MG_LR) {
        return row_types.includes('metagenomics_long_read');
      }
      if (templateKey === JGT_MT) {
        return row_types.includes('metatranscriptomics');
      }
      return false;
    }

    function synchronizeTabData(templateKey: string) {
      const environmentKeys = templateList.value.filter((t) => HARMONIZER_TEMPLATES[t].status === 'published');
      if (environmentKeys.includes(templateKey)) {
        return;
      }
      const nextData = { ...sampleData.value };
      const templateSlot = HARMONIZER_TEMPLATES[templateKey].sampleDataSlot;

      const environmentSlots = templateList.value
        .filter((t) => HARMONIZER_TEMPLATES[t].status === 'published')
        .map((t) => HARMONIZER_TEMPLATES[t].sampleDataSlot);

      if (!templateSlot || !environmentSlots) {
        return;
      }

      // ensure the necessary keys exist in the data object
      environmentSlots.forEach((slot) => {
        if (!nextData[slot as string]) {
          nextData[slot as string] = [];
        }
      });

      if (!nextData[templateSlot]) {
        nextData[templateSlot] = [];
      }

      // add/update any rows from the environment tabs to the active tab if they apply and if
      // they aren't there already.
      environmentSlots.forEach((environmentSlot) => {
        nextData[environmentSlot as string].forEach((row) => {
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
      });
      // remove any rows from the active tab if they were removed from the environment tabs
      // or no longer apply to the active tab
      if (nextData[templateSlot].length > 0) {
        nextData[templateSlot] = nextData[templateSlot].filter((row) => {
          if (!rowIsVisibleForTemplate(row, templateKey)) {
            return false;
          }
          const rowId = row[SCHEMA_ID];
          return environmentSlots.some((environmentSlot) => {
            const environmentRow = nextData[environmentSlot as string].findIndex((r) => r[SCHEMA_ID] === rowId);
            return environmentRow >= 0;
          });
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
        utils.book_append_sheet(workbook, worksheet, template.excelWorksheetName || template.displayName);
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
        const notImported = [] as string[];
        Object.entries(workbook.Sheets).forEach(([name, worksheet]) => {
          const template = Object.values(HARMONIZER_TEMPLATES).find((template) => (
            template.excelWorksheetName === name || template.displayName === name
          ));
          if (!template || !template.sampleDataSlot || !template.schemaClass) {
            notImported.push(name);
            return;
          }

          // The spreadsheet has slot names as the header row. So `sheet_to_json` will produce array
          // of objects with slot names as keys. But we want the imported data to be keyed on slot
          // IDs. This code reads the worksheet data and remaps the keys from slot names to IDs.
          const slotIdToNameMap = harmonizerApi.getHeaderRow(template.schemaClass);
          const slotNameToIdMap = Object.fromEntries(Object.entries(slotIdToNameMap).map(([k, v]) => [v, k]));
          const worksheetData: Record<string, string>[] = utils.sheet_to_json(worksheet);
          const remappedData = worksheetData.map((row) => Object.fromEntries(Object.entries(row)
            .filter(([slotName]) => slotNameToIdMap[slotName] !== undefined)
            .map(([slotName, value]) => [slotNameToIdMap[slotName], value])));

          imported[template.sampleDataSlot] = harmonizerApi.unflattenArrayValues(
            remappedData,
            template.schemaClass,
          );
        });

        // Alert the user if any worksheets were not imported
        notImportedWorksheetNames.value = notImported;
        importErrorSnackbar.value = notImported.length > 0;

        // Load imported data
        sampleData.value = imported;

        // Clear validation state
        harmonizerApi.setInvalidCells({});
        invalidCells.value = {};
        Object.keys(tabsValidated.value).forEach((tab) => {
          tabsValidated.value[tab] = false;
        });

        // Sync with backend
        hasChanged.value += 1;
        saveRecord(); // This is a background save that we intentionally don't wait for

        // Load data for active tab into DataHarmonizer
        harmonizerApi.loadData(activeTemplateData.value);

        // Reset the file input so that the same filename can be loaded multiple times
        (document.getElementById('tsv-file-select') as HTMLInputElement).value = '';
      };
      reader.readAsArrayBuffer(file);
    }

    async function changeTemplate(index: number) {
      if (!harmonizerApi.ready.value) {
        return;
      }

      await validate();
      // When changing templates we may need to populate the common columns
      // from the environment tabs
      const nextTemplate = templateList.value[index];
      synchronizeTabData(nextTemplate);

      activeTemplateKey.value = nextTemplate;
      activeTemplate.value = HARMONIZER_TEMPLATES[nextTemplate];
      harmonizerApi.useTemplate(HARMONIZER_TEMPLATES[nextTemplate].schemaClass);
      harmonizerApi.addChangeHook(onDataChange);
    }

    return {
      user,
      APP_HEADER_HEIGHT,
      HELP_SIDEBAR_WIDTH,
      ColorKey,
      HARMONIZER_TEMPLATES,
      columnVisibility,
      harmonizerElement,
      jumpToModel,
      harmonizerApi,
      canSubmit,
      tabsValidated,
      saveRecordRequest,
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
      activeTemplateKey,
      invalidCells,
      validationErrors,
      validationErrorGroups,
      validationTotalCounts,
      submissionStatus,
      status,
      submitDialog,
      snackbar,
      schemaLoading,
      importErrorSnackbar,
      notImportedWorksheetNames,
      isTestSubmission,
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
      canEditSampleMetadata,
    };
  },
});
</script>

<template>
  <div
    :style="{'overflow-y': 'hidden', 'overflow-x': 'hidden', 'height': `calc(100vh - ${APP_HEADER_HEIGHT}px)`}"
    class="d-flex flex-column"
  >
    <SubmissionStepper />
    <submission-permission-banner
      v-if="!canEditSampleMetadata()"
    />
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
            @change="(evt: any) => openFile(evt.target.files[0])"
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
            :disabled="!canEditSampleMetadata()"
            @click="showOpenFileDialog"
          >
            1. Import XLSX file
            <v-icon class="pl-2">
              mdi-file-table
            </v-icon>
          </v-btn>
        </label>
        <v-btn
          v-if="validationErrorGroups.length === 0"
          color="primary"
          outlined
          :disabled="!canEditSampleMetadata()"
          @click="validate"
        >
          2. Validate
          <v-icon class="pl-2">
            mdi-refresh
          </v-icon>
        </v-btn>
        <v-snackbar
          v-model="snackbar"
          color="success"
          timeout="3000"
        >
          Validation Passed! You can now submit or continue editing.
        </v-snackbar>
        <v-snackbar
          v-model="importErrorSnackbar"
          color="error"
          timeout="5000"
        >
          The following worksheet names were not recognized: {{ notImportedWorksheetNames.join(', ') }}
        </v-snackbar>
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
        <submission-docs-link anchor="sample-metadata" />
        <span v-if="saveRecordRequest.count.value > 0">
          <span
            v-if="saveRecordRequest.loading.value"
            class="text-center"
          >
            <v-progress-circular
              color="primary"
              :width="1"
              size="20"
              indeterminate
            />
            Saving progress
          </span>
          <span v-if="!saveRecordRequest.error.value && !saveRecordRequest.loading.value">
            <v-icon
              color="green"
            >
              mdi-check
            </v-icon>
            Changes saved successfully
          </span>
          <span v-else-if="saveRecordRequest.error.value && !saveRecordRequest.loading.value">
            <v-icon
              color="red"
            >
              mdi-close
            </v-icon>
            Failed to save changes
          </span>
        </span>
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
                v-for="(sectionName, sectionTitle) in harmonizerApi.schemaSectionNames.value"
                :key="sectionName"
                :value="sectionName"
              >
                <template #label>
                  <span>
                    {{ sectionTitle }}
                  </span>
                </template>
              </v-radio>
            </v-radio-group>
          </v-card>
        </v-menu>
      </div>
    </div>

    <v-tabs @change="changeTemplate">
      <v-tooltip
        v-for="templateKey in templateList"
        :key="templateKey"
        right
      >
        <template #activator="{on, attrs}">
          <div
            style="display: flex;"
            v-bind="attrs"
            v-on="on"
          >
            <v-tab>
              <v-badge
                :content="validationTotalCounts[templateKey] || '!'"
                :value="validationTotalCounts[templateKey] > 0 || !tabsValidated[templateKey]"
                :color="validationTotalCounts[templateKey] > 0 ? 'error' : 'warning'"
              >
                {{ HARMONIZER_TEMPLATES[templateKey].displayName }}
              </v-badge>
            </v-tab>
          </div>
        </template>
        <span v-if="validationTotalCounts[templateKey] > 0">
          {{ validationTotalCounts[templateKey] }} validation errors
        </span>
        <span v-else-if="!tabsValidated[templateKey]">
          This tab must be validated before submission
        </span>
        <span v-else>
          {{ HARMONIZER_TEMPLATES[templateKey].displayName }}
        </span>
      </v-tooltip>
      <v-spacer />
      <v-menu
        offset-x
        left
        z-index="300"
      >
        <template #activator="{on, attrs}">
          <v-btn
            color="primary"
            small
            class="my-2 py-4"
            v-bind="attrs"
            v-on="on"
          >
            <v-icon
              class="mt-1"
            >
              mdi-message-question
            </v-icon>
          </v-btn>
        </template>
        <ContactCard />
      </v-menu>
    </v-tabs>

    <div v-if="schemaLoading">
      Loading...
    </div>

    <div
      class="harmonizer-style-container harmonizer-and-sidebar"
    >
      <div
        id="harmonizer-root"
        :style="{
          'padding-right': sidebarOpen ? HELP_SIDEBAR_WIDTH : '0px',
        }"
      />

      <div
        class="harmonizer-sidebar"
        :style="{
          'width': sidebarOpen ? HELP_SIDEBAR_WIDTH : '0px',
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
          <div v-else>
            <div class="mx-2">
              <div class="text-h6 mt-3 font-weight-bold d-flex align-center">
                Column Help
                <v-spacer />
              </div>
              <p class="my-2 text--disabled">
                Click on a cell or column to view help
              </p>
            </div>
          </div>
        </v-navigation-drawer>
      </div>
    </div>

    <div class="harmonizer-style-container">
      <div
        v-if="canEditSampleMetadata()"
        id="harmonizer-footer-root"
      />
    </div>
    <div class="d-flex ma-2">
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
      <v-tooltip top>
        <template #activator="{ on, attrs }">
          <div
            v-bind="attrs"
            v-on="on"
          >
            <v-btn
              color="success"
              depressed
              :disabled="!canSubmit || status !== submissionStatus.InProgress || submitCount > 0"
              :loading="submitLoading"
              @click="submitDialog = true"
            >
              <span v-if="status === submissionStatus.SubmittedPendingReview || submitCount">
                <v-icon>mdi-check-circle</v-icon>
                Submitted
              </span>
              <span v-else>
                3. Submit
              </span>
              <v-dialog
                v-model="submitDialog"
                activator="parent"
                width="auto"
              >
                <v-card v-if="isTestSubmission">
                  <v-card-title>
                    Submit
                  </v-card-title>
                  <v-card-text>
                    Test submissions cannot be submitted for NMDC review.
                  </v-card-text>
                  <v-card-actions>
                    <v-btn
                      text
                      @click="submitDialog = false"
                    >
                      Close
                    </v-btn>
                  </v-card-actions>
                </v-card>
                <v-card v-else>
                  <v-card-title>
                    Submit
                  </v-card-title>
                  <v-card-text>
                    You are about to submit this study and metadata for NMDC review. Would you like to continue?
                  </v-card-text>
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
        </template>
        <span v-if="!canSubmit">
          You must validate all tabs before submitting your study and metadata.
        </span>
        <span v-else>
          Submit for NMDC review.
        </span>
      </v-tooltip>
    </div>
  </div>
</template>

<style lang="scss">
// Handsontable attaches hidden elements to <body> in order to measure text widths. Therefore this
// cannot be nested inside .harmonizer-style-container or else the measurements will be off.
@import '/node_modules/data-harmonizer/lib/dist/es/index.css';

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
  @import '/node_modules/bootstrap/scss/_functions.scss';
  @import '/node_modules/bootstrap/scss/_variables.scss';
  @import '/node_modules/bootstrap/scss/_mixins.scss';
  @import "/node_modules/bootstrap/scss/_reboot.scss";
  @import '/node_modules/bootstrap/scss/_type.scss';
  @import '/node_modules/bootstrap/scss/_modal.scss';
  @import '/node_modules/bootstrap/scss/_buttons.scss';
  @import '/node_modules/bootstrap/scss/_forms.scss';
  @import '/node_modules/bootstrap/scss/_input-group.scss';
  @import '/node_modules/bootstrap/scss/_utilities.scss';
}

.handsontable.listbox td {
  border-radius: 3px;
  border: 1px solid silver;
  background-color: #DDD;

  &:hover, &.current.highlight {
    background-color: lightblue !important;
  }
}

.harmonizer-and-sidebar {
  position: relative;
  width: 100%;
  height: 100%;
  flex-grow: 1;
  overflow: auto;
}

.harmonizer-sidebar {
  font-size: 14px;
  position: absolute;
  top: 0;
  bottom: 0;
  right: 0;
}

/* Grid */
#harmonizer-root {
  width: 100%;
  height: 100%;

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
      background-color: yellow;
    }

    &.recommended {
      background-color: plum;
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
  border-radius: 3px;
  border: 1px solid silver;
  background-color: #DDD;

  &:hover, &.current.highlight {
    background-color: lightblue !important;
  }
}

.field-description-text select {
  min-width: 95%
}

#harmonizer-footer-root {
  width: 50%;
  padding: 12px 0;
}

.HandsontableCopyPaste {
  display: none;
}

.sidebar-toggle {
  background: white;
  z-index: 200;
  position: absolute;
  top: 0;
  left: 0;
  transform: translateX(-100%);
  border-color: rgb(152, 152, 152);
  border-right-color: rgba(152, 152, 152, 0.0);
}

.sidebar-toggle-close {
  transform: rotate(180deg);
}

.htDimmed {
  cursor: not-allowed;
}
</style>
