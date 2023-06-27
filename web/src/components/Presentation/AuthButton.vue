<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import { stateRefs } from '@/store';

export default defineComponent({
  props: {
    nav: {
      type: Boolean,
      default: false,
    },
  },
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
        :text="!nav"
        :plain="nav"
        :small="nav"
        :ripple="!nav"
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
        :icon="!nav"
        :plain="nav"
        :small="nav"
        :ripple="!nav"
        href="/logout"
      >
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </template>
    <template v-else>
      <v-btn
        :text="!nav"
        :plain="nav"
        :small="nav"
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
