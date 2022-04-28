<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import AuthButton from '@/components/Presentation/AuthButton.vue';
import { stateRefs } from '@/store';
import { loadRecord } from './store';

export default defineComponent({
  components: { AuthButton },
  setup(_, { root }) {
    if (root.$route.params.id) {
      loadRecord(root.$route.params.id);
    }

    return { stateRefs };
  },
});
</script>

<template>
  <v-main>
    <v-container v-if="!stateRefs.user.value">
      <h1>NMDC Submission Portal</h1>
      <p>
        This system requires authentication.
        <a href="https://support.orcid.org/hc/en-us/articles/360006973953">ORCID registration is free for individuals.</a>
      </p>
      <AuthButton />
    </v-container>
    <keep-alive v-else>
      <router-view />
    </keep-alive>
  </v-main>
</template>
