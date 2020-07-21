<script>
import { mapState } from 'vuex';

import Welcome from '@/components/Presentation/Welcome.vue';

export default {
  components: { Welcome },

  computed: {
    ...mapState(['dbstats', 'allSamples']),

    stats() {
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
          label: 'Organic Matter Characterization',
        },
      ]] : [[], []];
    },

    samples() {
      return this.allSamples ? this.allSamples.results : [];
    },
  },

  created() {
    this.$store.dispatch('fetchDBStats');
  },
};
</script>

<template>
  <v-main>
    <Welcome
      :samples="samples"
      :stats="stats"
      @set-type="$store.dispatch('route', { name: 'Search', type: $event, conditions: [] })"
    />
  </v-main>
</template>
