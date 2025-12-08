<script lang="ts">
import { defineComponent } from 'vue';
import { api } from '@/data/api';

export default defineComponent({
  setup() {
    function handleLoginClick() {
      api.initiateOrcidLogin('submission');
    }
    return {
      handleLoginClick,
    };
  },
});
</script>

<template>
  <v-alert
    class="mt-6 mb-0"
    variant="tonal"
    type="warning"
    color="primary"
    prominent
  >
    <div class="d-flex align-center">
      <span class="text-h6 font-weight-bold flex-grow-1">
        Login to submit data
      </span>
      <v-btn
        variant="plain"
        depressed
        text
        right
        absolute
        class="mr-4"
        @click="handleLoginClick"
      >
        <img
          width="28px"
          class="mr-2"
          alt="Login with ORCiD"
          src="https://orcid.org/assets/vectors/orcid.logo.icon.svg"
        >
        OrcID Login
      </v-btn>
      <a
        href="https://support.orcid.org/hc/en-us/articles/360006973953"
        rel="noreferrer noopener"
        target="_blank"
        title="Learn about registering an ORCiD"
      >
        <v-icon>
          mdi-help-circle
        </v-icon>
      </a>
    </div>
  </v-alert>
</template>
