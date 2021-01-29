<script lang="ts">
import { humanFileSize } from '@/data/utils';
import { ProjectSearchResult } from '@/data/api';
import { defineComponent, PropType } from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import { flattenDeep } from 'lodash';

// const OmicsTypeMap = {
//   'nmdc:readqcanalysisactivity': 'ReadQC',
//   'nmdc:metagenomeannotation': 'Metagenome',
//   'nmdc:'
// }

export default defineComponent({
  props: {
    project: {
      type: Object as PropType<ProjectSearchResult>,
      required: true,
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

    const items = flattenDeep(props.project.omics_data
      .map((omics_data) => omics_data.outputs.map((data_object, i) => ({
        ...data_object,
        omics_data,
        group_name: i === 0 ? omics_data.name : '',
        object_description: data_object.name
          .replace(`${omics_data.project_id}_`, '')
          .replace(/file/ig, ''),
      }))));

    return { headers, items, humanFileSize };
  },
});
</script>

<template>
  <v-card outlined>
    <v-data-table
      :headers="headers"
      :items="items"
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
