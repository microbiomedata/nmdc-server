<template>
  <v-card
    flat
    class="ma-3"
  >
    <v-container fluid>
      <v-row
        class="headline"
        justify="center"
      >
        Explore NMDC data
      </v-row>
      <v-row
        class="my-6"
        justify="center"
      >
        <v-btn
          x-large
          color="primary"
          elevation="0"
          class="ma-4"
          @click="$emit('set-type', 'study')"
        >
          Browse studies
        </v-btn>
        <v-btn
          x-large
          color="primary"
          elevation="0"
          class="ma-4"
          @click="$emit('set-type', 'project')"
        >
          Search by omics type
        </v-btn>
        <v-btn
          x-large
          color="primary"
          elevation="0"
          class="ma-4"
          @click="$emit('set-type', 'sample')"
        >
          Explore habitats
        </v-btn>
      </v-row>
    </v-container>
    <LocationMap
      :data="samples"
      @selected="addSelected($event)"
    />
    <v-container fluid>
      <template
        v-for="(statsLine, statsLineIndex) in stats"
      >
        <v-row
          :key="statsLineIndex"
        >
          <template
            v-for="(stat) in statsLine"
          >
            <v-col
              v-if="stat.value !== 0"
              :key="stat.label"
            >
              <v-card
                height="150"
                outlined
              >
                <v-container
                  fluid
                  style="height: 100%"
                >
                  <v-row
                    align="center"
                    align-content="center"
                    style="height: 100%"
                  >
                    <v-col
                      cols="12"
                      class="display-1 text-center py-1"
                    >
                      {{ stat.value }}
                    </v-col>
                    <v-col
                      cols="12"
                      class="title text-center py-1"
                    >
                      {{ stat.label }}
                    </v-col>
                  </v-row>
                </v-container>
              </v-card>
            </v-col>
          </template>
        </v-row>
      </template>
    </v-container>
  </v-card>
</template>
<script>
import LocationMap from './LocationMap.vue';

export default {
  components: {
    LocationMap,
  },
  props: {
    samples: {
      type: Array,
      default: () => [],
    },
    stats: {
      type: Array,
      default: () => [],
    },
  },
};
</script>
