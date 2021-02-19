<script lang="ts">
import { groupBy } from 'lodash';
import { fieldDisplayName } from '@/util';
import { BiosampleSearchResult } from '@/data/api';
import { computed, defineComponent, PropType } from '@vue/composition-api';
import DataObjectTable from './DataObjectTable.vue';

const hiddenOmicsTypes = [
  'lipidomics',
];

const buttonOrder = [
  'metagenome',
  'metatranscriptome',
  'proteomics',
  'metabolomics',
  'organic matter characterization',
];

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
    loggedInUser: {
      type: Boolean,
      default: false,
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

    const filteredProjects = computed(() => Object.entries(groupBy(
      props.result.projects
        .filter((p) => hiddenOmicsTypes.indexOf(p.annotations.omics_type.toLowerCase()) === -1),
      (p) => p.annotations.omics_type,
    )).sort(([agroup], [bgroup]) => {
      const ai = buttonOrder.indexOf(agroup.toLowerCase());
      const bi = buttonOrder.indexOf(bgroup.toLowerCase());
      return ai - bi;
    }));

    return {
      isOpen,
      filteredProjects,
      fieldDisplayName,
    };
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
        v-for="[omicsType, projects] in filteredProjects"
        :key="projects[0].id"
        x-small
        :outlined="!isOpen(projects[0].id)"
        :color="isOpen(projects[0].id) ? 'primary' : 'default'"
        class="mr-2 mt-2"
        @click="() => $emit('open-details', projects[0].id)"
      >
        {{ fieldDisplayName(omicsType) }}
        <v-icon>mdi-chevron-down</v-icon>
      </v-btn>
    </div>
    <template v-for="[omicsType, projects] in filteredProjects">
      <DataObjectTable
        v-if="isOpen(projects[0].id)"
        :key="projects[0].id"
        class="flex-row mt-2"
        :projects="projects"
        :omics-type="omicsType"
        :logged-in-user="loggedInUser"
      />
    </template>
  </div>
</template>
