<script lang="ts">
import {
  computed, defineComponent, ref, nextTick, watch, onMounted,
} from '@vue/composition-api';
import { clamp, flattenDeep } from 'lodash';
import { writeFile, utils } from 'xlsx';
import { urlify } from '@/data/utils';
import useRequest from '@/use/useRequest';

import { HarmonizerApi } from './harmonizerApi';
import {
  packageName, samplesValid, sampleData, submit, incrementalSaveRecord, templateChoice,
} from './store';
import FindReplace from './Components/FindReplace.vue';
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
  components: { FindReplace, SubmissionStepper },

  setup(_, { root }) {
    const harmonizerElement = ref();
    const harmonizerApi = new HarmonizerApi();
    const jumpToModel = ref();
    const highlightedValidationError = ref(0);
    const validationActiveCategory = ref('All Errors');
    const columnVisibility = ref('all');
    const sidebarOpen = ref(true);

    onMounted(async () => {
      const r = document.getElementById('harmonizer-root');
      if (r) {
        await harmonizerApi.init(r, templateChoice.value);
        await nextTick();
        harmonizerApi.loadData(sampleData.value.slice(2));
        harmonizerApi.addChangeHook(() => {
          const data = harmonizerApi.exportJson();
          sampleData.value = data;
          incrementalSaveRecord(root.$route.params.id);
        });
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
      const currentSeries = harmonizerApi.validationErrors.value[validationActiveCategory.value];
      highlightedValidationError.value = clamp(index, 0, currentSeries.length - 1);
      const currentError = currentSeries[highlightedValidationError.value];
      harmonizerApi.jumpToRowCol(currentError[0], currentError[1]);
    }

    async function validate() {
      const data = harmonizerApi.exportJson();
      sampleData.value = data;
      samplesValid.value = await harmonizerApi.validate();
      sidebarOpen.value = !samplesValid.value;
      incrementalSaveRecord(root.$route.params.id);
      if (samplesValid.value === false) {
        errorClick(0);
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

    function openFile() {
      document.getElementById('tsv-file-select')?.click();
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
      sidebarOpen,
      validationItems,
      validationActiveCategory,
      /* methods */
      doSubmit,
      downloadSamples,
      errorClick,
      openFile,
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
      <div class="d-flex align-center">
        <label
          for="tsv-file-select"
        >
          <input
            id="tsv-file-select"
            type="file"
            style="position: fixed; top: -100em"
            @change="(evt) => harmonizerApi.openFile(evt.target.files[0])"
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
            @click="openFile"
          >
            1. Import TSV file
            <v-icon class="pl-2">
              mdi-file-table
            </v-icon>
          </v-btn>
        </label>
        <v-btn
          v-if="harmonizerApi.validationErrorGroups.value.length == 0"
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
          v-if="harmonizerApi.validationErrorGroups.value.length"
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
              ({{ highlightedValidationError + 1 }}/{{ harmonizerApi.validationErrors.value[validationActiveCategory].length }})
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
          'height': 'calc(100vh - 340px)'
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
            <v-btn
              color="grey"
              outlined
              small
              block
              @click="harmonizerApi.launchReference()"
            >
              Full {{ packageName }} Reference
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
          3. Submit
        </span>
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
  height: calc(100vh - 340px) !important;
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
