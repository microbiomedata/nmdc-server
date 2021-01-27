<script lang="ts">
import { BiosampleSearchResult } from '@/data/api';
import { defineComponent, PropType, reactive } from '@vue/composition-api';
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
      type: Object as PropType<{ id: string | null; type: string | null; }>,
      required: true,
    },
  },

  components: {
    DataObjectTable,
  },

  setup() {
    const data = reactive({
      open: null as string | null,
    });

    return { data };
  },
});
</script>

<template>
  <div class="d-flex flex-column mt-2">
    <div class="flex-row">
      <v-btn
        v-for="item in result.omics_data"
        :key="item.id"
        small
        :outlined="!(expanded.id === result.id && expanded.type === item.type)"
        :color="expanded.id === result.id && expanded.type === item.type ? 'primary' : 'default'"
        class="mr-2"
        @click="() => $emit('open-details', item.type)"
      >
        {{ item.type }} ({{ item.outputs.length }})
        <v-icon>mdi-chevron-down</v-icon>
      </v-btn>
    </div>
    <template v-for="item in result.omics_data">
      <div
        v-if="expanded.id === result.id && expanded.type === item.type"
        :key="item.id"
        class="flex-row mt-2"
      >
        <DataObjectTable
          :data="item"
        />
      </div>
    </template>
  </div>
</template>
