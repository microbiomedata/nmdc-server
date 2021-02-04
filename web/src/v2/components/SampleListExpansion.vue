<script lang="ts">
import { BiosampleSearchResult } from '@/data/api';
import { defineComponent, PropType } from '@vue/composition-api';
import DataObjectTable from './DataObjectTable.vue';
// const OmicsTypeMap = {
//   'nmdc:readqcanalysisactivity': 'ReadQC',
//   'nmdc:metagenomeannotation': 'Metagenome',
//   'nmdc:'
// }

export default defineComponent({
  props: {
    result: {
      type: Object as PropType<BiosampleSearchResult>,
      required: true,
    },
    expanded: {
      type: Object as PropType<{ resultId: string; projectId: string; }>,
      required: true,
    },
  },

  components: {
    DataObjectTable,
  },

  setup(props) {
    function isOpen(projectId: string) {
      return props.expanded.resultId === props.result.id
        && props.expanded.projectId === projectId;
    }
    return { isOpen };
  },
});
</script>

<template>
  <div
    v-if="result.projects.length"
    class="d-flex flex-column mb-2"
  >
    <div class="d-flex flex-row flex-wrap">
      <v-btn
        v-for="project in result.projects"
        :key="project.id"
        x-small
        :outlined="!isOpen(project.id)"
        :color="isOpen(project.id) ? 'primary' : 'default'"
        class="mr-2 mt-2"
        @click="() => $emit('open-details', project.id)"
      >
        {{ project.annotations.omics_type }}
        <v-icon>mdi-chevron-down</v-icon>
      </v-btn>
    </div>
    <template v-for="project in result.projects">
      <DataObjectTable
        v-if="isOpen(project.id)"
        :key="project.id"
        class="flex-row mt-2"
        :project="project"
      />
    </template>
  </div>
</template>
