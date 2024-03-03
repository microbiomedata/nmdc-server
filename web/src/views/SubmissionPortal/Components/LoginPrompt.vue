<script lang="ts">
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  props: {},
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
    text="text"
  >
    <v-container>
      <v-row align="center">
        <v-col class="justify-content-center">
          <p class="body-1">
            Login with your ORCiD
            to access the Submission Portal.
          </p>
          <p class="body-2 mb-0 text--disabled">
            Don't have an ORCiD? Individuals can
            <a
              href="https://support.orcid.org/hc/en-us/articles/360006973953"
              target="_blank"
              title="Learn about registering an ORCiD"
              class="text--disabled"
            >get one for free</a>.
          </p>
        </v-col>
        <v-col class="flex-grow-0">
          <!-- Note: This button is a simplified version of: `web/src/components/Presentation/AuthButton.vue` -->
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
