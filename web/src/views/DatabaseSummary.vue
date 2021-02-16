<script lang="ts">
import Vue from 'vue';
import { api } from '@/data/api';
import Welcome from '@/components/Presentation/Welcome.vue';

interface Stats {
  value: number;
  label: string;
}

export default Vue.extend({
  components: { Welcome },

  computed: {

    stats(): Stats[][] {
      // TODO: typescript hates asyncComputed.
      // refactor to watchEffect in vue 3 later
      // @ts-ignore
      const { dbstats } = this;
      return dbstats ? [[
        {
          value: dbstats.studies,
          label: 'Studies',
        },
        {
          value: dbstats.locations,
          label: 'Locations',
        },
        {
          value: dbstats.habitats,
          label: 'Environments',
        },
        {
          value: `${(dbstats.data_size / 1024 / 1024 / 1024 / 1024).toFixed(1)}TB`,
          label: 'Data',
        },
      ], [
        {
          value: dbstats.metagenomes,
          label: 'Metagenomes',
        },
        {
          value: dbstats.metatranscriptomes,
          label: 'Metatranscriptomes',
        },
        {
          value: dbstats.proteomics,
          label: 'Proteomics',
        },
        {
          value: dbstats.metabolomics,
          label: 'Metabolomics',
        },
        {
          value: dbstats.lipodomics,
          label: 'Lipodomics',
        },
        {
          value: dbstats.organic_matter_characterization,
          label: 'Organic Matter',
        },
      ]] : [[], []];
    },
  },

  asyncComputed: {
    dbstats: {
      get() { return api.getDatabaseStats(); },
      default: [],
    },
  },
});
</script>

<template>
  <v-main>
    <Welcome
      :stats="stats"
      @set-type="$store.dispatch('route', { name: 'Search', type: $event, conditions: [] })"
    />
  </v-main>
</template>
