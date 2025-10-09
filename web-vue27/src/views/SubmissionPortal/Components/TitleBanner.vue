<script lang="ts">
import {
  defineComponent,
} from 'vue';

export default defineComponent({
  components: {},
  setup() {
    return {};
  },
});
</script>

<template>
  <v-container>
    <v-row :style="{ backgroundImage: 'url(' + require('@/assets/submission-portal-hero.png') + ')', backgroundSize: 'cover' }">
      <v-col class="text-center py-16">
        <h1 class="white--text">
          Submission Portal
        </h1>
        <span class="d-block white--text mt-4">
          Ready to submit data?
        </span>
      </v-col>
    </v-row>
  </v-container>
</template>
