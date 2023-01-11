<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import { stateRefs } from '@/store';

export default defineComponent({
  setup() {
    return {
      me: stateRefs.user,
      orcid: stateRefs.orcid,
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
        :href="orcid ? `https://orcid.org/${orcid}` : ''"
      >
        <v-icon left>
          mdi-account-circle
        </v-icon>
        {{ me }}
        <img
          width="24px"
          class="ml-2"
          alt="ORCID logo"
          src="https://orcid.org/assets/vectors/orcid.logo.icon.svg"
        >
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
          alt="OrcId login"
          src="https://orcid.org/assets/vectors/orcid.logo.icon.svg"
        >
        OrcID Login
      </v-btn>
    </template>
  </div>
</template>
