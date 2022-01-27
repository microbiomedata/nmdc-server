<script lang="ts">
import {
  computed, defineComponent, ref, nextTick, watch,
} from '@vue/composition-api';
import { HARMONIZER_TEMPLATES, IFRAME_BASE, useHarmonizerApi } from './harmonizerApi';

import { templateName, samplesValid, sampleData } from './store';
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
    const harmonizerApi = useHarmonizerApi(harmonizerElement);

    const jumpToModel = ref();
    const highlightedValidationError = ref('');
    const columnVisibility = ref('all');

    async function jumpTo(columnName: string) {
      harmonizerApi.jumpTo(columnName);
      await nextTick();
      jumpToModel.value = null;
    }

    function focus() {
      window.focus();
    }

    async function validate() {
      samplesValid.value = await harmonizerApi.validate();
    }

    async function persist() {
      const data = await harmonizerApi.exportJson();
      sampleData.value = data;
      root.$router.push({ name: 'Validate And Submit' });
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

    watch(columnVisibility, () => {
      harmonizerApi.changeVisibility(columnVisibility.value);
    });

    function hydrate() {
      harmonizerApi.loadData(sampleData.value);
    }

    return {
      ColorKey,
      columnVisibility,
      harmonizerElement,
      jumpToModel,
      harmonizerApi,
      samplesValid,
      templateName,
      templateFolderName,
      fields,
      validationErrors,
      highlightedValidationError,
      IFRAME_BASE,
      /* methods */
      errorClick,
      hydrate,
      persist,
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
          @focus="focus"
          @change="jumpTo"
        />
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
    <div style="height: calc(100vh - 260px);">
      <iframe
        ref="harmonizerElement"
        title="Data Harmonizer"
        width="100%"
        height="100%"
        :src="`${IFRAME_BASE}/main.html?minified=true&template=${templateFolderName}`"
        sandbox="allow-popups allow-popups-to-escape-sandbox allow-scripts allow-modals allow-downloads allow-forms"
        @load="hydrate"
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
        depressed
        :disabled="!samplesValid"
        @click="persist"
      >
        <v-icon class="pr-1">
          mdi-arrow-right-circle
        </v-icon>
        <span v-if="samplesValid">
          Go to next step
        </span>
        <span v-else>
          Validate to proceed
        </span>
      </v-btn>
    </div>
  </div>
</template>
