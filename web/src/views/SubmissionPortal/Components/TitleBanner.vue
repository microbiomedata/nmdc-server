<script lang="ts">
import {
  defineComponent,
} from 'vue';
import heroImage from '@/assets/submission-portal-hero.png';

export default defineComponent({
  components: {},
  setup() {
    return {
      heroImage,
    };
  },
});
</script>

<template>
  <v-container>
    <v-row :style="{ backgroundImage: `url(${heroImage})`, backgroundSize: 'cover' }">
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
