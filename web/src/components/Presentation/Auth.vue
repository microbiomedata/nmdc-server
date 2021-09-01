<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import { stateRefs } from '@/store';

export default defineComponent({
  setup() {
    return {
      me: stateRefs.user,
    };
  },
});
</script>

<template>
  <div>
    <template v-if="me">
      <v-btn
        text
        color="grey darken-2"
      >
        <v-icon left>
          mdi-account-circle
        </v-icon>
        {{ me }}
      </v-btn>
      <v-btn
        icon
        color="grey darken-2"
        href="/logout"
      >
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </template>
    <template v-else>
      <v-btn
        text
        color="grey darken-2"
        href="/login"
      >
        <img
          width="28px"
          class="mr-2"
          src="https://orcid.org/assets/vectors/orcid.logo.icon.svg"
        >
        OrcID Login
      </v-btn>
    </template>
  </div>
</template>
