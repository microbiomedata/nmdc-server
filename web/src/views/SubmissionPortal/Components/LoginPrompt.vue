<script lang="ts">
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  setup() {
    return {
      loginHref: '/login',
    };
  },
});
</script>

<template>
  <v-alert
    class="mb-0"
    text
  >
    <v-container>
      <v-row align="center">
        <v-col class="justify-content-center">
          <p class="body-1">
            Login with your ORCID iD
            to access the Submission Portal.
          </p>
          <p class="body-2 mb-0">
            Don't have an ORCID iD? Individuals can
            <a
              href="https://support.orcid.org/hc/en-us/articles/360006973953"
              rel="noreferrer noopener"
              target="_blank"
              title="Learn about registering an ORCiD"
            >get one for free</a>.
          </p>
        </v-col>
        <v-col class="flex-grow-0">
          <v-btn
            :href="loginHref"
            variant="plain"
            elevation="0"
            style="background: transparent"
          >
            <img
              width="28px"
              class="mr-2"
              alt="Login with ORCiD"
              src="https://orcid.org/assets/vectors/orcid.logo.icon.svg"
            >
            OrcID Login
          </v-btn>
        </v-col>
      </v-row>
    </v-container>
  </v-alert>
</template>
