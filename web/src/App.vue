<script lang="ts">
import { defineComponent, onMounted } from '@vue/composition-api';
import AppHeader from '@/components/Presentation/AppHeader.vue';
import { stateRefs, init } from '@/store/';
import { useRouter } from '@/use/useRouter';
import { api, RefreshTokenExchangeError } from '@/data/api';

export default defineComponent({
  name: 'App',
  components: { AppHeader },
  setup() {
    const router = useRouter();

    onMounted(async () => {
      if (!router) {
        return;
      }
      if (router.currentRoute.path === '/login') {
        // init() will be called in the LoginPage component in this case
        return;
      }
      // The first time the app is loaded, there will not yet be an access token configured on
      // the API client. There *may* be a refresh token in storage, so attempt to exchange it
      // before calling the init() function.
      try {
        await api.exchangeRefreshToken();
      } catch (error) {
        if (error instanceof RefreshTokenExchangeError) {
          // The refresh failed, carry on with a logged-out state
        } else {
          throw error;
        }
      }
      await init(router);
    });

    return {
      stateRefs,
    };
  },
});
</script>

<template>
  <v-app>
    <app-header />
    <keep-alive>
      <router-view />
    </keep-alive>
  </v-app>
</template>
