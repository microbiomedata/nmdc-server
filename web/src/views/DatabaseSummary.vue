<script>
import { mapState } from 'vuex';
import { api } from '@/data/api';
import Welcome from '@/components/Presentation/Welcome.vue';

export default {
  components: { Welcome },

  computed: {
    ...mapState(['dbsummary', 'allSamples']),

    dbStats() {
      return this.dbsummary ? [
        {
          value: this.dbsummary.study.total,
          label: 'Studies',
        },
        {
          value: this.dbsummary.project.total,
          label: 'Locations',
        },
        {
          value: this.dbsummary.biosample.total,
          label: 'Habitats',
        },
      ] : [];
    },

    samples() {
      return this.allSamples ? this.allSamples.results : [];
    },

    stats() {
      return [this.dbStats, this.omicsStats];
    },
  },

  asyncComputed: {
    omicsStats: {
      async get() {
        const summaries = await api.getFacetSummary('project', 'omics_type', []);
        return summaries.map((fsm) => ({
          label: fsm.facet,
          value: fsm.count,
        }));
      },
      default: [],
    },
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
