<script lang="ts">
import { humanFileSize } from '@/data/utils';
import { ProjectSearchResult } from '@/data/api';
import { defineComponent, PropType } from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import { flattenDeep, flatten } from 'lodash';

const descriptionMap: Record<string, string> = {
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
  props: {
    projects: {
      type: Array as PropType<ProjectSearchResult[]>,
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
        text: 'Workflow Activity',
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
        sortable: false,
      },
      {
        text: 'Download',
        value: 'action',
        width: 80,
        sortable: false,
      },
    ];

    const items = flattenDeep(
      flatten(props.projects.map((p) => p.omics_data))
        .map((omics_data) => omics_data.outputs.map((data_object, i) => {
          const object_type = data_object.name
            .replace(`${omics_data.project_id}_`, '')
            .replace(/file/ig, '')
            .replace(/(\d+_?)+\.?/ig, '')
            .replace(/(^\s+|\s+$)/g, '');
          return {
            ...data_object,
            omics_data,
            /* TODO Hack to replace metagenome with omics type name */
            group_name: i === 0 ? omics_data.name
              .replace('Metagenome', props.omicsType) : '',
            object_type,
            object_description: descriptionMap[object_type] || '',
          };
        })),
    );

    return {
      descriptionMap,
      headers,
      items,
      humanFileSize,
    };
  },
});
</script>

<template>
  <v-card outlined>
    <v-data-table
      :headers="headers"
      :items="items"
      dense
    >
      <template #[`item.file_size_bytes`]="{ item }">
        {{ humanFileSize(item.file_size_bytes ) }}
      </template>
      <template #[`item.action`]="{ item }">
        <v-tooltip
          :disabled="loggedInUser"
          bottom
        >
          <template #activator="{ on, attrs }">
            <span v-on="on">
              <v-btn
                v-if="item.url"
                icon
                v-bind="attrs"
                :href="item.url"
                :disabled="!loggedInUser"
                target="_blank"
                rel="noopener"
              >
                <v-icon>mdi-download</v-icon>
              </v-btn>
            </span>
          </template>
          <span>You must be logged in</span>
        </v-tooltip>
      </template>
    </v-data-table>
  </v-card>
</template>
