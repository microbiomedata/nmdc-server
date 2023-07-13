<script lang="ts">
import {
  computed, defineComponent, PropType, reactive,
} from '@vue/composition-api';
import { flattenDeep } from 'lodash';

import { DataTableHeader } from 'vuetify';
import { humanFileSize } from '@/data/utils';
import { BiosampleSearchResult, OmicsProcessingResult } from '@/data/api';
import { stateRefs, acceptTerms } from '@/store';

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
    biosample: {
      type: Object as PropType<BiosampleSearchResult>,
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

    const items = computed(() => flattenDeep(
      flattenDeep(props.biosample.omics_processing.filter((o) => o.omics_type.has_raw_value === props.omicsType).map(
        (omicsProcessing) => props.biosample.analysis.filter(
          (analysis) => analysis.was_informed_by === omicsProcessing.id,
        ),
      )).map(
        (analysis) => analysis.has_output.map(
          (dataObjectId) => props.biosample.data_object.find(
            (dataObject) => dataObject.id === dataObjectId,
          ),
        ).map((dataObject, index) => ({
          ...dataObject,
          analysis,
          /* TODO Hack to replace metagenome with omics type name */
          group_name: analysis.name ? analysis.name.replace('Metagenome', props.omicsType) : '',
          newgroup: index === 0,
        })),
      ),
    ));

    function download(item: OmicsProcessingResult) {
      if (typeof item.url === 'string') {
        if (stateRefs.hasAcceptedTerms.value) {
          window.open(item.url, '_blank', 'noopener,noreferrer');
        } else {
          termsDialog.item = item;
          termsDialog.value = true;
        }
      }
    }

    function onAcceptTerms() {
      termsDialog.value = false;
      acceptTerms();
    }

    return {
      onAcceptTerms,
      download,
      descriptionMap,
      headers,
      items,
      humanFileSize,
      termsDialog,
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
        :href="termsDialog.item.url"
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
          <td>{{ item.data_object_type }}</td>
          <td>TODO: lookup from schema</td>
          <td>{{ humanFileSize(item.file_size_bytes ) }}</td>
          <td>TODO</td>
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
                    @click="download(item)"
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
