<script lang="ts">
import {
  computed, defineComponent, ref, nextTick, watch, onMounted, shallowRef, inject,
} from 'vue';
import {
  clamp, debounce, flattenDeep, has, sum,
} from 'lodash';
import { read, writeFile, utils } from 'xlsx';
import { api } from '@/data/api';
import useRequest from '@/use/useRequest';

import {
  DATA_MG_INTERLEAVED,
  DATA_MG,
  DATA_MT,
  DATA_MT_INTERLEAVED,
  HARMONIZER_TEMPLATES,
  EMSL,
  JGI_MG,
  JGI_MT,
  JGI_MG_LR,
  SuggestionsMode,
} from '@/views/SubmissionPortal/types';
import HarmonizerSidebar from '@/views/SubmissionPortal/Components/HarmonizerSidebar.vue';
import { APP_HEADER_HEIGHT } from '@/components/Presentation/AppHeader.vue';
import { stateRefs } from '@/store';
import { getPendingSuggestions } from '@/store/localStorage';
import HarmonizerApi from './harmonizerApi';
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
  canEditSampleMetadata,
  isOwner,
  addMetadataSuggestions,
  suggestionMode,
  metadataSuggestions,
  isTestSubmission,
  canEditSubmissionByStatus,
  SubmissionStatusEnum,
  validForms,
} from './store';
import { AppBannerHeightKey } from './SubmissionView.vue';
import SubmissionNavigationSidebar from './Components/SubmissionNavigationSidebar.vue';
import SubmissionDocsLink from './Components/SubmissionDocsLink.vue';
import SubmissionPermissionBanner from './Components/SubmissionPermissionBanner.vue';
import StatusAlert from './Components/StatusAlert.vue';
import { useRoute } from 'vue-router';

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

const HELP_SIDEBAR_WIDTH = 320;
const TABS_HEIGHT = 48;

const SUGGESTION_REQUEST_DELAY = 3000;

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
  'jgi_seq_project',
  'jgi_samp_id',
  'jgi_seq_project_name',
  'jgi_project_pi',
  'jgi_proposal_id',
];

export default defineComponent({
  components: {
    HarmonizerSidebar,
    SubmissionNavigationSidebar,
    SubmissionDocsLink,
    SubmissionPermissionBanner,
    StatusAlert,
  },

  setup() {
    const { user } = stateRefs;
    const route = useRoute();

    const harmonizerElement = ref();
    const harmonizerApi = new HarmonizerApi();
    const jumpToModel = ref();
    const highlightedValidationError = ref(0);
    const validationActiveCategory = ref('All Errors');
    const columnVisibility = ref('all');
    const sidebarOpen = ref(true);
    const invalidCells = shallowRef({} as Record<string, Record<number, Record<number, string>>>);

    const activeTemplateKey = ref(templateList.value[0]);
    const activeTemplate = ref(HARMONIZER_TEMPLATES[activeTemplateKey.value!]);
    const activeTabIndex = ref(0);
    const activeTemplateData = computed(() => {
      if (!activeTemplate.value?.sampleDataSlot) {
        return [];
      }
      return sampleData.value[activeTemplate.value.sampleDataSlot] || [];
    });

    const submitDialog = ref(false);
    const missingTabsText = computed(() => {
      const text: Array<string> = [];
      if (validForms.templatesValid === false) {
        text.push('No tabs will be present until one or more templates are selected in the Sample Environment form.');
      }
      if (validForms.multiOmicsFormValid.length > 0) {
        text.push('Facility tabs will not be present until the Multiomics Form is complete.');
      }
      return text;
    });
    function determineMissingTabs() {
      if (missingTabsText.value.length > 0) {
        return true;
      }
      return false;
    }
    const missingTabs = ref(determineMissingTabs());

    watch(missingTabsText, () => {
      if (missingTabsText.value.length > 0) {
        missingTabs.value = true;
      }
    });

    const validationSuccessSnackbar = ref(false);
    const importErrorSnackbar = ref(false);
    const notImportedWorksheetNames = ref([] as string[]);
    const emptySheetSnackbar = ref(false);

    watch(activeTemplate, () => {
      // WARNING: It's important to do the column settings update /before/ data. Otherwise,
      // columns will not be rendered with the correct width.
      harmonizerApi.setColumnsReadOnly(ALWAYS_READ_ONLY_COLUMNS);

      // If the environment tab selected is a mixin it should be readonly
      const environmentList = templateList.value.filter((t) => HARMONIZER_TEMPLATES[t]?.status === 'mixin');
      if (environmentList.includes(activeTemplateKey.value!)) {
        harmonizerApi.setColumnsReadOnly(COMMON_COLUMNS);
        harmonizerApi.setMaxRows(activeTemplateData.value.length);
      }
      harmonizerApi.loadData(activeTemplateData.value);
      harmonizerApi.setInvalidCells(invalidCells.value[activeTemplateKey.value!] || {});
      harmonizerApi.changeVisibility(columnVisibility.value);
    });

    const validationErrors = computed(() => {
      const remapped: ValidationErrors = {};
      const invalid: Record<number, Record<number, string>> = invalidCells.value[activeTemplateKey.value!] || {};
      if (Object.keys(invalid).length) {
        remapped['All Errors'] = [];
      }
      Object.entries(invalid).forEach(([row, rowErrors]) => {
        Object.entries(rowErrors).forEach(([col, errorText]) => {
          const entry: [number, number] = [parseInt(row, 10), parseInt(col, 10)];
          const issue = errorText || 'Other Validation Error';
          if (has(remapped, issue)) {
            remapped[issue]?.push(entry);
          } else {
            remapped[issue] = [entry];
          }
          remapped['All Errors']?.push(entry);
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
    const saveRecord = () => saveRecordRequest.request(() => incrementalSaveRecord((route.params as { id: string }).id));

    let changeBatch: any[] = [];
    const debouncedSuggestionRequest = debounce(async () => {
      const changedRowData = harmonizerApi.getDataByRows(changeBatch.map((change) => change[0]));
      await addMetadataSuggestions((route.params as { id: string }).id, activeTemplate.value?.schemaClass!, changedRowData);
      changeBatch = [];
    }, SUGGESTION_REQUEST_DELAY, { leading: false, trailing: true });

    watch(suggestionMode, () => {
      // If live suggestions are disabled, clear the queue and cancel the timer
      if (suggestionMode.value !== SuggestionsMode.LIVE) {
        changeBatch = [];
        debouncedSuggestionRequest.cancel();
      }
    });

    function rowIsVisibleForTemplate(row: Record<string, any>, templateKey: string) {
      const environmentKeys = templateList.value.filter((t) => HARMONIZER_TEMPLATES[t]?.status === 'published');
      if (environmentKeys.includes(templateKey)) {
        return true;
      }
      const row_types = row[TYPE_FIELD];
      if (!row_types) {
        return false;
      }
      if (templateKey === EMSL) {
        return row_types.includes('lipidomics')
          || row_types.includes('metaproteomics')
          || row_types.includes('metabolomics')
          || row_types.includes('natural organic matter');
      }
      if (templateKey === JGI_MG) {
        return row_types.includes('metagenomics');
      }
      if (templateKey === JGI_MG_LR) {
        return row_types.includes('metagenomics_long_read');
      }
      if (templateKey === JGI_MT) {
        return row_types.includes('metatranscriptomics');
      }
      if (templateKey === DATA_MG) {
        return row_types.includes('metagenomics');
      }
      if (templateKey === DATA_MG_INTERLEAVED) {
        return row_types.includes('metagenomics');
      }
      if (templateKey === DATA_MT) {
        return row_types.includes('metatranscriptomics');
      }
      if (templateKey === DATA_MT_INTERLEAVED) {
        return row_types.includes('metatranscriptomics');
      }
      return false;
    }

    // DataHarmonizer is a bit loose in its definition of empty cells. They can be null or and empty string.
    const isNonEmpty = (val: any) => val !== null && val !== '';

    function synchronizeTabData(templateKey: string) {
      const environmentKeys = templateList.value.filter((t) => HARMONIZER_TEMPLATES[t]?.status === 'published');
      if (environmentKeys.includes(templateKey)) {
        return;
      }
      const nextData = { ...sampleData.value };
      const templateSlot = HARMONIZER_TEMPLATES[templateKey]?.sampleDataSlot;

      const environmentSlots = templateList.value
        .filter((t) => HARMONIZER_TEMPLATES[t]?.status === 'published')
        .map((t) => HARMONIZER_TEMPLATES[t]?.sampleDataSlot);

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
        nextData[environmentSlot as string]?.forEach((row) => {
          const rowId = row[SCHEMA_ID];

          const existing = nextData[templateSlot] && nextData[templateSlot].find((r) => r[SCHEMA_ID] === rowId);
          if (!existing && rowIsVisibleForTemplate(row, templateKey)) {
            const newRow = {} as Record<string, any>;
            COMMON_COLUMNS.forEach((col) => {
              newRow[col] = row[col];
            });
            nextData[templateSlot]?.push(newRow);
            //update validation status for the tab, if data changed it needs to be revalidated
            tabsValidated.value[templateKey] = false;
          }
          if (existing) {
            COMMON_COLUMNS.forEach((col) => {
              existing[col] = row[col];
            });
            //update validation status for the tab, if data changed it needs to be revalidated
            tabsValidated.value[templateKey] = false;
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
          //update validation status for the tab, if data changed it needs to be revalidated
          tabsValidated.value[templateKey] = false;
          const rowId = row[SCHEMA_ID];
          return environmentSlots.some((environmentSlot) => {
            const environmentRow = nextData[environmentSlot as string]?.findIndex((r) => r[SCHEMA_ID] === rowId);
            return environmentRow !== undefined && environmentRow >= 0;
          });
        });
      }
      sampleData.value = nextData;
    }

    /**
     * This should be called whenever rows are removed from the data harmonizer.
     * It ensures that row deletion is cascaded to facility templates from the main
     * environment templates
     */
    const syncAndMergeTabsForRemovedRows = async () => {
      mergeSampleData(
        activeTemplate.value?.sampleDataSlot,
        harmonizerApi.exportJson(),
      );
      // If there are any sampleDataSlots populated that somehow are missing from
      // the template list, make sure those data are updated as well.
      Object.keys(sampleData.value).forEach((key) => {
        // Loop through keys in the sampleData for the submission. Each
        // key maps to a template. We have to find that template.
        const [templateKey, template] = Object.entries(HARMONIZER_TEMPLATES).find(([, template]) => (
          template?.sampleDataSlot === key
        )) || [undefined, undefined];
        if (template && templateKey) {
          // If we found the template, synchronize the data
          // Make sure we carry the deletion through to the sampleData
          // The current tab's data needs to be updated first, then synchronized
          synchronizeTabData(templateKey);
        }
      });
    };

    const onDataChange = async (changes: any[]) => {
      // If we're in live suggestion mode and the user can edit the metadata, add the changes to a batch. Once the user
      // has not made further changes for a certain amount of time, send the batch to the backend for suggestions.
      if (suggestionMode.value === SuggestionsMode.LIVE && canEditSampleMetadata()) {
        // Many "empty" changes can be fired when clearing an entire row or column. We only care about the ones
        // where either the previous value or updated value (or both) are non-empty.
        const nonEmptyChanges = changes.filter((change) => isNonEmpty(change[2]) || isNonEmpty(change[3]));
        changeBatch.push(...nonEmptyChanges);
        debouncedSuggestionRequest();
      }
      // If any changes touched the sample name or analysis/data type columns on an environment
      // tab, we need to synch those changes to non-active tabs
      const templateOrderedAttrNames = harmonizerApi.getOrderedAttributeNames(activeTemplate.value?.schemaClass || '');
      const shouldSynchronizeTabs = !!changes.find((change) => {
        const isRelevantColumn = templateOrderedAttrNames[change[1]] === SAMP_NAME || templateOrderedAttrNames[change[1]] === ANALYSIS_TYPE;
        const isNonemptyChange = isNonEmpty(change[2]) || isNonEmpty(change[3]);
        return isNonemptyChange && isRelevantColumn;
      });

      hasChanged.value += 1;
      if (shouldSynchronizeTabs) {
        syncAndMergeTabsForRemovedRows();
      } else {
        const data = harmonizerApi.exportJson();
        mergeSampleData(activeTemplate.value?.sampleDataSlot, data);
      }
      saveRecord(); // This is a background save that we intentionally don't wait for
      tabsValidated.value[activeTemplateKey.value!] = false;
    };

    const { request: schemaRequest, loading: schemaLoading } = useRequest();

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
      highlightedValidationError.value = clamp(index, 0, (currentSeries?.length || 0) - 1);
      const currentError = currentSeries ? currentSeries[highlightedValidationError.value] : null;
      if (currentError && currentError[0] !== undefined && currentError[1] !== undefined) {
        harmonizerApi.jumpToRowCol(currentError[0], currentError[1]);
      }
    }

    async function validate() {
      const data = harmonizerApi.exportJson(); // Gets data from harmonizer API

      // Check if the spreadsheet is empty
      const isEmpty = Object.keys(data).length === 0;
      // Update invalid cells if empty
      if (isEmpty) {
        invalidCells.value = {
          ...invalidCells.value,
          [activeTemplateKey.value!]: data,
        };
        tabsValidated.value = {
          ...tabsValidated.value,
          [activeTemplateKey.value!]: false,
        };
        emptySheetSnackbar.value = true;

        return;
      }

      mergeSampleData(activeTemplate.value?.sampleDataSlot, data);
      const result = await harmonizerApi.validate();
      const valid = Object.keys(result).length === 0;
      if (!valid && !sidebarOpen.value) {
        sidebarOpen.value = true;
      }

      invalidCells.value = {
        ...invalidCells.value,
        [activeTemplateKey.value!]: result,
      };
      saveRecord(); // This is a background save that we intentionally don't wait for
      if (valid === false) {
        errorClick(0);
      }
      tabsValidated.value = {
        ...tabsValidated.value,
        [activeTemplateKey.value!]: valid,
      };

      validationSuccessSnackbar.value = Object.values(tabsValidated.value).every((value) => value);
    }

    const submissionState = computed(() => {
      let allTabsValid = true;
      Object.values(tabsValidated.value).forEach((value) => {
        allTabsValid = allTabsValid && value;
      });
      const hasSubmitPermission = isOwner() || stateRefs.user?.value?.is_admin;
      const canSubmitByStatus = status.value === 'InProgress'
      const isSubmitted = submitCount.value > 0 || status.value === 'SubmittedPendingReview';
      validForms.harmonizerValid = allTabsValid && isOwner() && validForms.templatesValid;
      let submitDisabledReason: string | null = null;
      if (!allTabsValid) {
        submitDisabledReason = 'All tabs must be validated before submission.';
      } else if (validForms.templatesValid || validForms.studyFormValid.length === 0 || validForms.multiOmicsFormValid.length === 0) {
        submitDisabledReason = 'Validation issues on other screens must be fixed.';
      } else if (!hasSubmitPermission) {
        submitDisabledReason = 'You do not have permission to submit this record.';
      } else if (!canSubmitByStatus) {
        submitDisabledReason = `Submission cannot be made while in status: ${status.value}.`;
      }
      return {
        isSubmitted,
        submitDisabledReason,
        canSubmit: submitDisabledReason === null,
      };
    });

    const handleSubmitClick = () => {
      if (submissionState.value.canSubmit) {
        submitDialog.value = true;
      }
    };

    const fields = computed(() => flattenDeep(Object.entries(harmonizerApi.schemaSectionColumns.value)
      .map(([sectionName, children]) => Object.entries(children).map(([columnName, column]) => {
        const val = {
          type: !columnName ? 'subheader' : 'item',
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
        text: `${errorGroup} (${errors?.length})`,
        value: errorGroup,
      };
    }));

    watch(validationActiveCategory, () => errorClick(0));
    watch(columnVisibility, () => {
      harmonizerApi.changeVisibility(columnVisibility.value);
    });

    watch(activeTabIndex, (newIndex) => {
      changeTemplate(newIndex);
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
      mergeSampleData(activeTemplate.value?.sampleDataSlot, data);
      await submit((route.params as { id: string }).id, 'SubmittedPendingReview');
      submitDialog.value = false;
    });

    async function downloadSamples() {
      templateList.value.forEach((templateKey) => {
        synchronizeTabData(templateKey);
      });

      const workbook = utils.book_new();
      templateList.value.forEach((templateKey) => {
        const template = HARMONIZER_TEMPLATES[templateKey];
        if (!template?.sampleDataSlot || !template.schemaClass) {
          return;
        }
        const worksheet = utils.json_to_sheet([
          harmonizerApi.getHeaderRow(template.schemaClass),
          ...HarmonizerApi.flattenArrayValues(sampleData.value[template.sampleDataSlot] || []),
        ], {
          skipHeader: true,
        });
        utils.book_append_sheet(workbook, worksheet, template.excelWorksheetName || template.displayName);
      });
      writeFile(workbook, EXPORT_FILENAME, { compression: true });
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
          const templateSelected = templateList.value.find((selectedTemplate) => {
            const templateName = HARMONIZER_TEMPLATES[selectedTemplate]?.displayName || '';
            return (
              template?.displayName === templateName
              || template?.excelWorksheetName === templateName
            );
          });
          if (!template || !template.sampleDataSlot || !template.schemaClass || !templateSelected) {
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
      };
      reader.readAsArrayBuffer(file);
    }

    /**
     * Set up the hands on table with appropriate event handlers
     * for interactions with the Data Harmonizer.
     */
    function addHooks() {
      harmonizerApi.addChangeHook(onDataChange);
      harmonizerApi.addRowRemovedHook(async () => {
        syncAndMergeTabsForRemovedRows();
        hasChanged.value += 1;
        saveRecord();
      });
    }

    async function changeTemplate(index: number) {
      if (!harmonizerApi.ready.value) {
        return;
      }

      await validate();

      const nextTemplateKey = templateList.value[index];
      const nextTemplate = nextTemplateKey ? HARMONIZER_TEMPLATES[nextTemplateKey] : null;

      if (nextTemplate && nextTemplateKey) {
        // Get the stashed suggestions (if any) for the next template and present them.
        metadataSuggestions.value = getPendingSuggestions((route.params as { id: string }).id, nextTemplate.schemaClass!);

        // When changing templates we may need to populate the common columns
        // from the environment tabs
        synchronizeTabData(nextTemplateKey);
        activeTemplateKey.value = nextTemplateKey;
        activeTemplate.value = nextTemplate;
        harmonizerApi.useTemplate(nextTemplate.schemaClass);
        addHooks();
      }
    }

    watch(() => canEditSampleMetadata(), (canEdit) => {
      if (harmonizerApi.ready.value) {
        if (!canEdit) {
          harmonizerApi.setTableReadOnly();
        }
      }
    });

    onMounted(async () => {
      const [schema, goldEcosystemTree] = await schemaRequest(() => Promise.all([
        api.getSubmissionSchema(),
        api.getGoldEcosystemTree(),
      ]));
      const r = document.getElementById('harmonizer-root');
      if (r && schema) {
        await harmonizerApi.init(r, schema, activeTemplate.value?.schemaClass, goldEcosystemTree);
        await nextTick();
        harmonizerApi.loadData(activeTemplateData.value);
        addHooks();
        metadataSuggestions.value = getPendingSuggestions(
          (route.params as { id: string }).id,
          activeTemplate.value?.schemaClass!,
        );
        if (!canEditSampleMetadata()) {
          harmonizerApi.setTableReadOnly();
        }
      }
    });

    // Get app banner height provided by SubmissionView. This will be used to correctly size
    // the DataHarmonizer container, which needs a fixed height.
    const appBannerHeight = inject(AppBannerHeightKey);

    return {
      user,
      APP_HEADER_HEIGHT,
      appBannerHeight,
      HELP_SIDEBAR_WIDTH,
      TABS_HEIGHT,
      ColorKey,
      HARMONIZER_TEMPLATES,
      columnVisibility,
      harmonizerElement,
      jumpToModel,
      harmonizerApi,
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
      activeTabIndex,
      invalidCells,
      validationErrors,
      validationErrorGroups,
      validationTotalCounts,
      SubmissionStatusEnum,
      status,
      submitDialog,
      missingTabs,
      missingTabsText,
      validationSuccessSnackbar,
      schemaLoading,
      importErrorSnackbar,
      notImportedWorksheetNames,
      emptySheetSnackbar,
      isTestSubmission,
      StatusAlert,
      submissionState,
      /* methods */
      doSubmit,
      downloadSamples,
      errorClick,
      openFile,
      focus,
      jumpTo,
      validate,
      changeTemplate,
      canEditSampleMetadata,
      canEditSubmissionByStatus,
      handleSubmitClick,
    };
  },
});
</script>

<template>
  <div v-if="missingTabs">
    <SubmissionNavigationSidebar />
    <v-container centered>
      <v-card elevation="5">
        <v-card-title class="text-center justify-center text-h4">
          Not all tabs may be present!
        </v-card-title>
        <v-card-text class="text-center justify-center text-h5">
          <div
            v-for="(item, index) in missingTabsText"
            :key="index"
            class="mb-2"
          >
            {{ item }}
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
  <div
    v-else
    :style="{'overflow-y': 'hidden', 'overflow-x': 'hidden', 'height': `calc(100vh - ${APP_HEADER_HEIGHT + (appBannerHeight || 0)}px)`}"
    class="d-flex flex-column"
  >
    <SubmissionNavigationSidebar />
    <submission-permission-banner
      v-if="canEditSubmissionByStatus() && !canEditSampleMetadata()"
    />
    <StatusAlert v-if="!canEditSubmissionByStatus()" />
    <div class="d-flex flex-column px-2 pb-2 pt-2">
      <div class="d-flex align-center">
        <v-btn
          v-if="validationErrorGroups.length === 0"
          color="primary"
          variant="outlined"
          :disabled="!canEditSampleMetadata()"
          @click="validate"
        >
          Validate
          <v-icon class="pl-2">
            mdi-refresh
          </v-icon>
        </v-btn>
        <v-snackbar
          v-model="validationSuccessSnackbar"
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
        <v-snackbar
          v-model="emptySheetSnackbar"
          color="error"
          timeout="5000"
        >
          The spreadsheet is empty. Please add data.
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
            item-title="text"
            solo
            style="background-color: #ffffff; color: #000000;"
            density="compact"
            class="mx-2 z-above-sidebar"
            hide-details
          >
            <template #selection="{ item }">
              <p
                style="font-size: 14px"
                class="my-0"
              >
                {{ item.title }}
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
              ({{ highlightedValidationError + 1 }}/{{ validationErrors[validationActiveCategory]?.length }})
            </span>
            <v-spacer />
            <v-icon
              @click="errorClick(highlightedValidationError + 1)"
            >
              mdi-arrow-right-circle
            </v-icon>
          </div>
          <v-btn
            variant="outlined"
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
          item-title="text"
          item-value="value"
          label="Jump to column..."
          class="flex-0-0 mr-2 z-above-sidebar"
          variant="outlined"
          density="compact"
          hide-details
          :menu-props="{ maxHeight: 500 }"
          width="233"
          @focus="focus"
          @update:model-value="jumpTo"
        />
        <v-menu
          offset-y
          nudge-bottom="4px"
          :close-on-click="true"
        >
          <template #activator="{ props }">
            <v-btn
              variant="outlined"
              v-bind="props"
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
            variant="outlined"
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

    <v-layout class="harmonizer-and-sidebar">
      <v-tabs
        v-model="activeTabIndex"
        color="primary"
      >
        <v-tooltip
          v-for="templateKey in templateList"
          :key="templateKey"
          right
        >
          <template #activator="{ props }">
            <div
              style="display: flex;"
              v-bind="props"
            >
              <v-tab>
                {{ HARMONIZER_TEMPLATES[templateKey]?.displayName }}
                <v-badge
                  :content="validationTotalCounts[templateKey] || '!'"
                  max="99"
                  inline
                  :model-value="(validationTotalCounts[templateKey] && validationTotalCounts[templateKey] > 0) || !tabsValidated[templateKey]"
                  :color="(validationTotalCounts[templateKey] && validationTotalCounts[templateKey] > 0) ? 'error' : 'warning'"
                />
              </v-tab>
            </div>
          </template>
          <span v-if="validationTotalCounts[templateKey] && validationTotalCounts[templateKey] > 0">
            {{ validationTotalCounts[templateKey] }} validation errors
          </span>
          <span v-else-if="!tabsValidated[templateKey]">
            This tab must be validated before submission
          </span>
          <span v-else>
            {{ HARMONIZER_TEMPLATES[templateKey]?.displayName }}
          </span>
        </v-tooltip>
      </v-tabs>

      <div v-if="schemaLoading">
        Loading...
      </div>

      <div
        id="harmonizer-root"
        class="harmonizer-style-container"
        :style="{
          'right': sidebarOpen ? `${HELP_SIDEBAR_WIDTH}px` : '0px',
          'top': `${TABS_HEIGHT}px`,
        }"
      />

      <v-btn
        class="sidebar-toggle"
        tile
        variant="plain"
        color="black"
        :ripple="false"
        :height="TABS_HEIGHT"
        :width="TABS_HEIGHT"
        :style="{
          'right': sidebarOpen ? `${HELP_SIDEBAR_WIDTH}px` : '0px',
        }"
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
        v-model="sidebarOpen"
        :width="HELP_SIDEBAR_WIDTH"
        absolute
        temporary
        location="right"
        class="z-above-data-harmonizer"
      >
        <HarmonizerSidebar
          :column-help="selectedHelpDict"
          :harmonizer-api="harmonizerApi"
          :harmonizer-template="activeTemplate!"
          :metadata-editing-allowed="canEditSampleMetadata()"
          @import-xlsx="openFile"
          @export-xlsx="downloadSamples"
        />
      </v-navigation-drawer>
    </v-layout>
    <div class="harmonizer-bottom-container">
      <div class="harmonizer-style-container">
        <div
          v-if="canEditSampleMetadata()"
          id="harmonizer-footer-root"
        />
      </div>
      <div class="d-flex ma-2">
        <v-btn-grey :to="{ name: 'Sample Environment' }">
          <v-icon class="pr-1">
            mdi-arrow-left-circle
          </v-icon>
          Go to Template Selection
        </v-btn-grey>
        <v-spacer />
        <div class="d-flex align-center">
          <span class="mr-1">Color key</span>
          <v-chip
            v-for="val in ColorKey"
            :key="val.label"
            :style="{ backgroundColor: val.color, opacity: 1, color: '#000000' }"
            class="mr-1"
            variant="flat"
          >
            {{ val.label }}
          </v-chip>
        </div>
        <v-spacer />
        <v-tooltip
          top
        >
          <template #activator="{ props }">
            <div
              v-bind="props"
            >
              <v-btn
                color="success"
                depressed
                :disabled="!submissionState.canSubmit"
                :loading="submitLoading"
                @click="handleSubmitClick"
              >
                <span v-if="submissionState.isSubmitted">
                  <v-icon>mdi-check-circle</v-icon>
                  Submitted
                </span>
                <span v-else>
                  Submit
                </span>
                <v-dialog
                  v-model="submitDialog"
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
          <span v-if="!submissionState.canSubmit">
            {{ submissionState.submitDisabledReason }}
          </span>
          <span v-if="submissionState.canSubmit">
            Submit for NMDC review.
          </span>
        </v-tooltip>
      </div>
    </div>
  </div>
</template>

<style lang="scss">
// Handsontable attaches hidden elements to <body> in order to measure text widths. Therefore this
// cannot be nested inside .harmonizer-style-container or else the measurements will be off.
@import '@microbiomedata/data-harmonizer/data-harmonizer.css';

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
  @import 'bootstrap/scss/functions';
  @import 'bootstrap/scss/variables';
  @import 'bootstrap/scss/mixins';
  @import "bootstrap/scss/reboot";
  @import 'bootstrap/scss/type';
  @import 'bootstrap/scss/modal';
  @import 'bootstrap/scss/buttons';
  @import 'bootstrap/scss/forms';
  @import 'bootstrap/scss/input-group';
  @import 'bootstrap/scss/utilities';
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
  overflow: hidden;
}

.v-navigation-drawer__scrim {
  display: none;
}

/* Grid */
#harmonizer-root {
  position: absolute;
  bottom: 0;
  left: 0;

  /**
    This ensures that the bootstrap modal appears
    below the app header.
  */
  .modal {
    top: 61px !important;
  }

  .secondary-header-cell:hover {
    cursor: pointer;
  }

  .htAutocompleteArrow {
    color: gray;
  }

  table {
    padding-right: 16px;
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
  padding: 0.5rem;
}

.HandsontableCopyPaste {
  display: none;
}

.sidebar-toggle {
  z-index: 200;
  position: absolute;
  top: 0;
  right: 0;
}

.sidebar-toggle-close {
  transform: rotate(180deg);
}

.htDimmed {
  cursor: not-allowed;
}

.z-above-data-harmonizer {
  z-index: 200 !important;
}

.z-above-sidebar {
  z-index: 201 !important;
}
</style>
