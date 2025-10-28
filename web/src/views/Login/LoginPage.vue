<script lang="ts">

import { defineComponent, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '@/data/api';
import { init } from '@/store';

/**
 * This component is responsible for handling the authorization code exchange process. It is the
 * target of the redirect URI after the user has authenticated with ORCID. The code that is passed
 * in the query string is exchanged for an access token and refresh token. Then the user is
 * redirected to the home page (via the init() function).
 */
export default defineComponent({
  name: 'LoginPage',
  setup() {
    const router = useRouter();

    const error = ref<boolean>(false);

    onMounted(async () => {
      if (!router) {
        error.value = true;
        return;
      }

      // If there is no code in the query string, stop here
      const { query } = router.currentRoute.value;
      if (!('code' in query)) {
        error.value = true;
        return;
      }

      // Attempt to exchange the code for an access token
      try {
        await api.exchangeAuthCode(query.code as string);
      } catch (e) {
        error.value = true;
        return;
      }

      // If the exchange was successful, call the init() function to load the user's data and
      // redirect to the home page. The init() function can handle the state URL query param
      // that has been persisted through the login process.
      await init(router, true, query.state as string | undefined);
    });

    return {
      error,
    };
  },
});
</script>

<template>
  <v-main>
    <v-container>
      <div v-if="error === false">
        Logging in...
      </div>
      <div v-else>
        Something went wrong. <a href="/">Go home</a>.
      </div>
    </v-container>
  </v-main>
</template>
