<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import {
  multiOmicsForm, templateHasData,
} from '../store';
import { HARMONIZER_TEMPLATES } from '@/views/SubmissionPortal/types';

export default defineComponent({
  props: {
    legend: {
      type: String,
      default: 'Data Types',
    },
    showDataCompatibilityQuestions: {
      type: Boolean,
      default: true,
    },
  },
  setup(_, { emit }) {
    const dataCaveat = 'You may proceed with your submission for sample metadata capture. However, there will not be place to provide information about your existing sequencing data as the methods are not supported by NMDC Workflows';

    const handleMetagenomeChange = (value: string[]) => {
      if (!value.includes('mg')) {
        multiOmicsForm.mgCompatible = undefined;
        multiOmicsForm.mgInterleaved = undefined;
      }
      emit('revalidate');
    };

    const handleMgCompatibleChange = (value: boolean) => {
      if (!value) {
        multiOmicsForm.mgInterleaved = undefined;
      }
      emit('revalidate');
    };

    const handleMetatranscriptomeChange = (value: string[]) => {
      if (!value.includes('mt')) {
        multiOmicsForm.mtCompatible = undefined;
        multiOmicsForm.mtInterleaved = undefined;
      }
      emit('revalidate');
    };

    const handleMtCompatibleChange = (value: boolean) => {
      if (!value) {
        multiOmicsForm.mtInterleaved = undefined;
      }
      emit('revalidate');
    };

    return {
      dataCaveat,
      multiOmicsForm,
      HARMONIZER_TEMPLATES,
      templateHasData,
      handleMetagenomeChange,
      handleMgCompatibleChange,
      handleMetatranscriptomeChange,
      handleMtCompatibleChange,
    };
  },

});

</script>

<template>
  <div

    class="text-h6 my-4"
  >
    <legend
      class="v-label theme--light mb-2"
      style="font-size: 14px;"
    >
      {{ legend }}
    </legend>
    <v-checkbox
      v-model="multiOmicsForm.omicsProcessingTypes"
      label="Metagenome"
      value="mg"
      :disabled="templateHasData(HARMONIZER_TEMPLATES.data_mg.sampleDataSlot) || templateHasData(HARMONIZER_TEMPLATES.data_mg_interleaved.sampleDataSlot)"
      hide-details
      @change="handleMetagenomeChange"
    />
    <div
      v-if="showDataCompatibilityQuestions && multiOmicsForm.omicsProcessingTypes.includes('mg')"
      class="v-label theme--light my-2 mx-8"
      style="font-size: 14px;"
    >
      NMDC currently supports external sequencing data that is comparable to data generated by the Joint Genome Institute (JGI):
      <ul
        class="my-2"
      >
        <li
          class="my-2"
        >
          Kapa Biosystems HyperPrep library preparation kit (Roche)
        </li>
        <li
          class="my-2"
        >
          Illumina NovaSeq X with a 2x150 run mode
        </li>
      </ul>
      Additional details about <a href="https://doi.org/10.1128/msystems.00804-20">metagenome processing</a> are available.
      If you have questions please contact <a href="mailto:support@microbiomedata.org">support@microbiomedata.org</a>
      <v-radio-group
        v-model="multiOmicsForm.mgCompatible"
        label="Is the generated data compatible? *"
        :rules="[v => v !== undefined || 'This field is required']"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.data_mg.sampleDataSlot) || templateHasData(HARMONIZER_TEMPLATES.data_mg_interleaved.sampleDataSlot)"
        @change="handleMgCompatibleChange"
      >
        <v-radio
          :value="false"
        >
          <template #label>
            <span>
              No
            </span>
            <v-tooltip
              right
              class="x-2"
              max-width="500"
            >
              <template #activator="{ on }">
                <v-icon
                  class="ml-2"
                  dense
                  v-on="on"
                >
                  mdi-help-circle
                </v-icon>
              </template>
              <span>
                {{ dataCaveat }}
              </span>
            </v-tooltip>
          </template>
        </v-radio>
        <v-radio
          label="Yes"
          :value="true"
        />
      </v-radio-group>
      <v-radio-group
        v-if="multiOmicsForm.mgCompatible"
        v-model="multiOmicsForm.mgInterleaved"
        label="Is the data in interleaved format? *"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.data_mg.sampleDataSlot) || templateHasData(HARMONIZER_TEMPLATES.data_mg_interleaved.sampleDataSlot)"
        :rules="[v => v !== undefined || 'This field is required']"
      >
        <v-radio
          label="No"
          :value="false"
        />
        <v-radio
          label="Yes"
          :value="true"
        />
      </v-radio-group>
    </div>
    <v-checkbox
      v-model="multiOmicsForm.omicsProcessingTypes"
      label="Metatranscriptome"
      value="mt"
      :disabled="templateHasData(HARMONIZER_TEMPLATES.data_mt.sampleDataSlot) || templateHasData(HARMONIZER_TEMPLATES.data_mt_interleaved.sampleDataSlot)"
      hide-details
      @change="handleMetatranscriptomeChange"
    />
    <div
      v-if="showDataCompatibilityQuestions && multiOmicsForm.omicsProcessingTypes.includes('mt')"
      class="v-label theme--light my-2 mx-8"
      style="font-size: 14px;"
    >
      NMDC currently supports external sequencing data that is comparable to data generated by the Joint Genome Institute (JGI):
      <ul
        class="my-2"
      >
        <li
          class="my-2"
        >
          Qiagen FastSelect 5S/16S/23s for bacterial rRNA depletion kit
        </li>
        <li
          class="my-2"
        >
          Illumina TruSeq Stranded Total RNA HT sample prep kit
        </li>
        <li
          class="my-2"
        >
          Illumina NovaSeq X with a 2x150 run mode
        </li>
      </ul>
      Additional details about <a href="https://jgi.doe.gov/wp-content/uploads/2022/03/20220125_metatranscriptome_planning_overview-FINAL.pdf">metatranscriptomes processing</a> are available.
      If you have questions please contact <a href="mailto:support@microbiomedata.org">support@microbiomedata.org</a>
      <v-radio-group
        v-model="multiOmicsForm.mtCompatible"
        label="Is the generated data compatible? *"
        :rules="[v => v !== undefined || 'This field is required']"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.data_mt.sampleDataSlot) || templateHasData(HARMONIZER_TEMPLATES.data_mt_interleaved.sampleDataSlot)"
        @change="handleMtCompatibleChange"
      >
        <v-radio
          :value="false"
        >
          <template #label>
            <span>
              No
            </span>
            <v-tooltip
              right
              class="x-2"
              max-width="500"
            >
              <template #activator="{ on }">
                <v-icon
                  class="ml-2"
                  dense
                  v-on="on"
                >
                  mdi-help-circle
                </v-icon>
              </template>
              <span>
                {{ dataCaveat }}
              </span>
            </v-tooltip>
          </template>
        </v-radio>
        <v-radio
          label="Yes"
          :value="true"
        />
      </v-radio-group>
      <v-radio-group
        v-if="multiOmicsForm.mtCompatible"
        v-model="multiOmicsForm.mtInterleaved"
        label="Is the data in interleaved format? *"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.data_mt.sampleDataSlot) || templateHasData(HARMONIZER_TEMPLATES.data_mt_interleaved.sampleDataSlot)"
        :rules="[v => v !== undefined || 'This field is required']"
      >
        <v-radio
          label="No"
          :value="false"
        />
        <v-radio
          label="Yes"
          :value="true"
        />
      </v-radio-group>
    </div>

    <v-checkbox
      v-model="multiOmicsForm.omicsProcessingTypes"
      label="Metaproteome"
      value="mp"
      hide-details
    />
    <v-checkbox
      v-model="multiOmicsForm.omicsProcessingTypes"
      label="Metabolome"
      value="mb"
      hide-details
    />
    <v-checkbox
      v-model="multiOmicsForm.omicsProcessingTypes"
      label="Natural Organic Matter (FT-ICR MS)"
      value="nom"
      hide-details
    />
  </div>
</template>
