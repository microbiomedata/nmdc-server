<script lang="ts">
// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';
import {
  computed, defineComponent, PropType, reactive,
} from '@vue/composition-api';
import { flattenDeep } from 'lodash';

import { DataTableHeader } from 'vuetify';
import { humanFileSize } from '@/data/utils';
import { client, BiosampleSearchResult, OmicsProcessingResult } from '@/data/api';
import { stateRefs, acceptTerms } from '@/store';
import { metaproteomicCategoryEnumToDisplay } from '@/encoding';

import DownloadDialog from './DownloadDialog.vue';

const descriptionMap: Record<string, string> = {
  'fastq.gz': 'Raw output file',
  'filterStats.txt': 'Reads QC summary statistics',
  'filtered.fastq.gz': 'Reads QC result fastq (clean data)',
  'mapping_stats.txt': 'Assembled contigs coverage information',
  'assembly_contigs.fna': 'Final assembly contigs fasta',
  'assembly_scaffolds.fna': 'Final assembly scaffolds fasta',
  'assembly.agp': 'An AGP format file describes the assembly',
  'pairedMapped_sorted.bam': 'Sorted bam file of reads mapping back to the final assembly',
  'KO TSV': 'Tab delimited file for KO annotation.',
  'EC TSV': 'Tab delimited file for EC annotation.',
  'Protein FAA': 'FASTA amino acid file for annotated proteins.',
};

export default defineComponent({
  components: { DownloadDialog },

  props: {
    omicsProcessing: {
      type: Array as PropType<OmicsProcessingResult[]>,
      required: true,
    },
    omicsType: {
      type: String,
      required: true,
    },
    loggedInUser: {
      type: Boolean,
      default: false,
    },
    biosample: {
      type: Object as PropType<BiosampleSearchResult>,
      required: true,
    },
  },

  setup(props) {
    const headers: DataTableHeader[] = [
      {
        text: '',
        value: 'group_name',
        sortable: false,
      },
      {
        text: 'Data Object Type',
        value: 'object_type',
        sortable: false,
      },
      {
        text: 'Data Object Description',
        value: 'object_description',
        sortable: false,
      },
      {
        text: 'File Size',
        value: 'file_size_bytes',
        width: 100,
        sortable: false,
      },
      {
        text: 'Downloads',
        value: 'downloads',
        width: 80,
        sortable: false,
      },
      {
        text: 'Download',
        value: 'action',
        width: 80,
        sortable: false,
      },
    ];

    const termsDialog = reactive({
      item: null as null | OmicsProcessingResult,
      value: false,
    });

    function nomMetadataString(item: {
      massSpecPolarityMode: string,
      eluentIntroductionCategory: string,
      sampledPortions: string,
    }): string {
      return [item.eluentIntroductionCategory, item.sampledPortions, item.massSpecPolarityMode].filter((value) => !!value).join(', ');
    }

    function getOmicsDataWithInputIds(omicsProcessing: OmicsProcessingResult) {
      const biosampleInputIds = (omicsProcessing.biosample_inputs as BiosampleSearchResult[]).map((input) => input.id);
      const annotations = omicsProcessing.annotations as Record<string, string | string[]>;
      return omicsProcessing.omics_data.map((omics) => {
        const { EluentIntroductionCategoryEnum, PolarityModeEnum, SamplePortionEnum } = NmdcSchema.enums;
        const omicsCopy = { ...omics };
        omicsCopy.inputIds = biosampleInputIds;
        if (annotations.mass_spectrometry_configuration_id) {
          omicsCopy.massSpecConfigId = annotations.mass_spectrometry_configuration_id || '';
          omicsCopy.massSpecConfigName = annotations.mass_spectrometry_configuration_name || '';
          const polarityMode = annotations.mass_spectrometry_config_polarity_mode
            ? `${PolarityModeEnum.permissible_values[annotations.mass_spectrometry_config_polarity_mode].text} mode`
            : '';
          omicsCopy.massSpecPolarityMode = polarityMode;
        }
        if (annotations.chromatography_configuration_id) {
          omicsCopy.chromConfigId = annotations.chromatography_configuration_id || '';
          omicsCopy.chromConfigName = annotations.chromatography_configuration_name || '';
        }
        if (annotations.eluent_introduction_category) {
          omicsCopy.eluentIntroductionCategory = EluentIntroductionCategoryEnum.permissible_values[annotations.eluent_introduction_category].title;
        }
        if (annotations.sampled_portions?.length) {
          const displaySampledPortions = (annotations.sampled_portions as string[]).map((sampledPortion: string) => (
            SamplePortionEnum.permissible_values[sampledPortion].title
            || SamplePortionEnum.permissible_values[sampledPortion].text
          ));
          omicsCopy.sampledPortions = displaySampledPortions.join(', ');
        }
        return omicsCopy;
      });
    }

    function getGroupName(omicsData: {id: string, name: string}): string {
      if (omicsData.name) {
        return omicsData.name.replace('Metagenome', props.omicsType) || omicsData.id;
      }
      return `${props.omicsType} Analysis ${omicsData.id}`;
    }

    const items = computed(() => flattenDeep(
      flattenDeep(props.omicsProcessing.map((p) => (getOmicsDataWithInputIds(p))))
        .map((omics_data) => omics_data.outputs
          .filter((data) => data.file_type && data.file_type_description)
          .map((data_object, i) => ({
            ...data_object,
            omics_data,
            /* TODO Hack to replace metagenome with omics type name */
            group_name: getGroupName(omics_data),
            newgroup: i === 0,
          }))),
    ));

    function getRelatedBiosampleIds(omicsData: any) {
      if (!omicsData || !omicsData.inputIds) {
        return [];
      }
      return omicsData.inputIds.filter((id: string) => id !== props.biosample.id);
    }

    async function getDownloadUrlAndOpen(item: OmicsProcessingResult) {
      if (typeof item.url === 'string') {
        const { data } = await client.get(item.url, { baseURL: '' });
        window.open(data.url, '_blank', 'noopener,noreferrer');
      }
    }

    async function handleDownload(item: OmicsProcessingResult) {
      if (typeof item.url === 'string') {
        if (stateRefs.hasAcceptedTerms.value) {
          getDownloadUrlAndOpen(item);
        } else {
          termsDialog.item = item;
          termsDialog.value = true;
        }
      }
    }

    function onAcceptTerms() {
      termsDialog.value = false;
      acceptTerms();
      getDownloadUrlAndOpen(termsDialog.item!);
      termsDialog.item = null;
    }

    return {
      onAcceptTerms,
      handleDownload,
      descriptionMap,
      headers,
      items,
      humanFileSize,
      termsDialog,
      getRelatedBiosampleIds,
      metaproteomicCategoryEnumToDisplay,
      nomMetadataString,
    };
  },
});
</script>

<template>
  <v-card outlined>
    <v-dialog
      v-if="termsDialog.item"
      v-model="termsDialog.value"
      :width="400"
    >
      <DownloadDialog
        @clicked="onAcceptTerms"
      />
    </v-dialog>
    <v-data-table
      :headers="headers"
      :items="items"
      dense
    >
      <template #item="{ item, index }">
        <tr
          v-if="(item.newgroup || index == 0) && item.group_name"
          :style="{ 'background-color': '#e0e0e0' }"
        >
          <td colspan="6">
            <b>Workflow Activity:</b> {{ item.group_name }}
            <span
              v-if="
                (omicsType === 'Metabolomics' || omicsType === 'Lipidomics')
                  && (item.omics_data.massSpecConfigId || item.omics_data.chromConfigId)
              "
            >
              <br>
              <b>Data Generation Configurations</b>
              <span v-if="item.omics_data.massSpecConfigId">
                {{ item.omics_data.massSpecConfigName }}:
                {{ item.omics_data.massSpecConfigId }};
              </span>
              <span v-if="item.omics_data.chromConfigId">
                {{ item.omics_data.chromConfigName }}:
                {{ ' ' + item.omics_data.chromConfigId }}
              </span>
            </span>
            <span v-if="omicsType === 'Proteomics'">
              <br>
              <b>{{ metaproteomicCategoryEnumToDisplay[item.omics_data.metaproteomics_analysis_category] }}</b>
            </span>
            <span v-if="omicsType === 'Organic Matter Characterization' && nomMetadataString(item.omics_data)">
              <br>
              <b>Data Generation: </b> NOM via
              {{ nomMetadataString(item.omics_data) }}
            </span>
            <br>
            <div v-if="getRelatedBiosampleIds(item.omics_data).length">
              <v-icon>
                mdi-flask-outline
              </v-icon>
              <span class="text-subtitle-2 grey--text text--darken-3"><b>Associated biosample inputs:</b></span>
              <router-link
                v-for="biosampleId in getRelatedBiosampleIds(item.omics_data)"
                :key="biosampleId"
                :to="{name: 'Sample', params: { id: biosampleId }}"
                class="ml-2 grey--text text--darken-3"
              >
                {{ biosampleId }}
              </router-link>
            </div>
          </td>
        </tr>
        <tr>
          <td>
            <v-tooltip right>
              <template #activator="{on, attrs }">
                <v-icon
                  v-bind="attrs"
                  :style="{ visibility: item.selected ? 'visible' : 'hidden'}"
                  v-on="on"
                >
                  mdi-checkbox-marked-circle-outline
                </v-icon>
              </template>
              <span>This file is included in the currently selected bulk download</span>
            </v-tooltip>
          </td>
          <td>{{ item.file_type }}</td>
          <td>{{ item.file_type_description }}</td>
          <td>{{ humanFileSize(item.file_size_bytes) }}</td>
          <td>{{ item.downloads }}</td>
          <td>
            <v-tooltip
              :disabled="!!(loggedInUser && item.url)"
              bottom
            >
              <template #activator="{ on, attrs }">
                <span v-on="on">
                  <v-btn
                    v-if="item.url"
                    icon
                    :disabled="!loggedInUser"
                    v-bind="attrs"
                    color="primary"
                    @click="handleDownload(item)"
                  >
                    <v-icon>mdi-download</v-icon>
                  </v-btn>
                  <v-btn
                    v-else
                    icon
                    disabled
                  >
                    <v-icon>
                      mdi-file-hidden
                    </v-icon>
                  </v-btn>
                </span>
              </template>
              <span v-if="item.url">
                You must be logged in
              </span>
              <span v-else>
                File unavailable
              </span>
            </v-tooltip>
          </td>
        </tr>
      </template>
    </v-data-table>
  </v-card>
</template>
