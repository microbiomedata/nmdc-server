<script lang="ts">
import { humanFileSize } from '@/data/utils';
import { ProjectSearchResult } from '@/data/api';
import { defineComponent, PropType } from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import { flattenDeep, flatten } from 'lodash';

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
        .map((omics_data) => omics_data.outputs.map((data_object, i) => ({
          ...data_object,
          omics_data,
          /* TODO Hack to replace metagenome with omics type name */
          group_name: i === 0 ? omics_data.name
            .replace('Metagenome', props.omicsType) : '',
          object_description: data_object.name
            .replace(`${omics_data.project_id}_`, '')
            .replace(/file/ig, ''),
        }))),
    );

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
