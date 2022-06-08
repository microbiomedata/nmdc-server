<script lang="ts">
import {
  computed, defineComponent, ref, nextTick, watch, onMounted,
} from '@vue/composition-api';
import { clamp, flattenDeep } from 'lodash';
import { writeFile, utils } from 'xlsx';
import 'handsontable/dist/handsontable.full.css';
import { urlify } from '@/data/utils';
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
    const highlightedValidationError = ref(0);
    const validationActiveCategory = ref('All Errors');
    const columnVisibility = ref('all');

    onMounted(async () => {
      const r = document.getElementById('harmonizer-root');
      if (r) {
        await harmonizerApi.init(r, templateChoice.value);
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

    function errorClick(index: number) {
      const currentSeries = harmonizerApi.validationErrors.value[validationActiveCategory.value];
      highlightedValidationError.value = clamp(index, 0, currentSeries.length - 1);
      const currentError = currentSeries[highlightedValidationError.value];
      harmonizerApi.jumpToRowCol(currentError[0], currentError[1]);
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

    const validationItems = computed(() => harmonizerApi.validationErrorGroups.value.map((v) => {
      const errors = harmonizerApi.validationErrors.value[v];
      return {
        text: `${v} (${errors.length})`,
        value: v,
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
      selectedHelpDict,
      packageName,
      templateChoice,
      fields,
      highlightedValidationError,
      validationItems,
      validationActiveCategory,
      /* methods */
      doSubmit,
      downloadSamples,
      errorClick,
      focus,
      jumpTo,
      validate,
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
    <div
      class="harmonizer-container d-flex flex-row"
      style="max-width: 100%;"
    >
      <v-navigation-drawer
        width="300"
        permanent
      >
        <template v-if="harmonizerApi.validationErrorGroups.value.length">
          <v-divider />
          <div class="text-h6 mx-2 mt-3 font-weight-bold">
            <v-icon color="error">
              mdi-alert
            </v-icon>
            Validation Errors
          </div>
          <v-select
            v-model="validationActiveCategory"
            :items="validationItems"
            outlined
            color="error"
            dense
            class="mx-2 mb-2"
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
          <div class="d-flex mx-2 mb-3 text-h6">
            <v-icon
              large
              @click="errorClick(highlightedValidationError - 1)"
            >
              mdi-arrow-left-circle
            </v-icon>
            <v-spacer />
            (
            {{ highlightedValidationError + 1 }}
            /
            {{ harmonizerApi.validationErrors.value[validationActiveCategory].length }}
            )
            <v-spacer />
            <v-icon
              large
              @click="errorClick(highlightedValidationError + 1)"
            >
              mdi-arrow-right-circle
            </v-icon>
          </div>
        </template>
        <div class="ma-2 grow">
          <v-btn
            color="primary"
            small
            block
            @click="validate"
          >
            <v-icon class="pr-2">
              mdi-refresh
            </v-icon>
            Validate
          </v-btn>
        </div>
        <v-divider />
        <div
          v-if="selectedHelpDict"
          class="ml-2"
          style="font-size: 14px; overflow-x: auto; max-height: 50%;"
        >
          <div class="text-h6 mt-3 font-weight-bold">
            <v-icon color="info">
              mdi-information
            </v-icon>
            Column Help
          </div>
          <div class="my-2">
            <span class="font-weight-bold pr-2">Column:</span>
            <span v-html="selectedHelpDict.title" />
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
        </div>
      </v-navigation-drawer>
      <div
        id="harmonizer-root"
        class="harmonizer-root grow"
        :style="{ 'max-width': 'calc(100vw - 300px)' }"
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
.harmonizer-container {
  height: calc(100vh - 260px) !important;
}

.harmonizer-root {
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
  // This stylesheet was unfortunately copy-pasted. In order to interpolate the content here,
  // an SCSS file is required (css will only be referenced).  There is no handsontable scss available,
  // so the CSS was renamed SCSS and copied into the project.  SCSS and CSS are treated differently
  // when imported within a parent scope (harmonizer-root class in this case)
  // @import './library/handsontable.min.scss';
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
