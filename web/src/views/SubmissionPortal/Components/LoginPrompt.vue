<script lang="ts">
import { defineComponent } from '@vue/composition-api';
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
    outlined
    text
    type="warning"
    color="primary"
    prominent
  >
    <span class="text-h6 font-weight-bold mb-3">
      Login to submit data
    </span>
    <v-btn
      :href="loginHref"
      plain
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
    <template #append>
      <a
        href="https://support.orcid.org/hc/en-us/articles/360006973953"
        rel="noreferrer noopener"
        target="_blank"
        title="Learn about registering an ORCiD"
      >
        <v-icon
          v-on="on"
        >
          mdi-help-circle
        </v-icon>
      </a>
    </template>
  </v-alert>
</template>
