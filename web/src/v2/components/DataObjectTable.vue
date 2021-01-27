<script lang="ts">
import { humanFileSize } from '@/data/utils';
import { OmicsProcessingResult } from '@/data/api';
import { defineComponent, PropType } from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';

// const OmicsTypeMap = {
//   'nmdc:readqcanalysisactivity': 'ReadQC',
//   'nmdc:metagenomeannotation': 'Metagenome',
//   'nmdc:'
// }

export default defineComponent({
  props: {
    data: {
      type: Object as PropType<OmicsProcessingResult>,
      required: true,
    },
  },

  setup() {
    const headers: DataTableHeader[] = [
      // {
      //   text: 'Type',
      //   value: '',
      // },
      {
        text: 'Data Object',
        value: 'name',
        sortable: true,
      },
      {
        text: 'File Size',
        value: 'file_size_bytes',
        sortable: true,
      },
      {
        text: 'Download',
        value: 'action',
        width: 80,
        sortable: false,
      },
    ];

    return { headers, humanFileSize };
  },
});
</script>

<template>
  <v-card outlined>
    <v-data-table
      :headers="headers"
      :items="data.outputs"
      hide-default-footer
      dense
    >
      <template #[`item.file_size_bytes`]="{ item }">
        {{ humanFileSize(item.file_size_bytes ) }}
      </template>
      <template #[`item.action`]="{ item }">
        <v-btn
          icon
          :href="item.name"
        >
          <v-icon>mdi-download</v-icon>
        </v-btn>
        <span>(2)</span>
      </template>
    </v-data-table>
  </v-card>
</template>
