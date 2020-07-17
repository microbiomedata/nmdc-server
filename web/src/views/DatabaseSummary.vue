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
          value: this.dbsummary.biosample.attributes.latitude,
          label: 'Locations',
        },
        {
          value: this.dbsummary.biosample.attributes.ecosystem_path_id,
          label: 'Habitats',
        },
        {
          value: -1,
          label: 'Data',
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
        const omicsSummary = await api.getFacetSummary('project', 'omics_type', []);
        return [
          {
            value: omicsSummary.Metagenome,
            label: 'Metagenomes',
          },
          {
            value: omicsSummary.Metatranscriptome,
            label: 'Metatranscriptomes',
          },
          {
            value: omicsSummary.Proteomics,
            label: 'Proteomics',
          },
          {
            value: omicsSummary.Metabolomics,
            label: 'Metabolomics',
          },
          {
            value: omicsSummary.Lipidomics,
            label: 'Lipidomics',
          },
          {
            value: omicsSummary['Organic Matter Characterization'],
            label: 'Organic Matter Characterization',
          },
        ];
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
