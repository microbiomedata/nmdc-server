<script lang="ts">
import { defineComponent, onMounted, onUnmounted } from 'vue';
import AppHeader from '@/components/Presentation/AppHeader.vue';
import { stateRefs, init } from '@/store/';
import { useRouter } from '@/use/useRouter';
import { api, REFRESH_TOKEN_EXPIRED_EVENT, RefreshTokenExchangeError } from '@/data/api';

export default defineComponent({
  name: 'App',
  components: { AppHeader },
  setup() {
    const router = useRouter();

    const handleRefreshTokenExpired = () => {
      stateRefs.user.value = null;
      if (router) {
        init(router, false);
      }
    };

    onMounted(async () => {
      window.addEventListener(REFRESH_TOKEN_EXPIRED_EVENT, handleRefreshTokenExpired);

      if (!router) {
        return;
      }
      if (router.currentRoute.path === '/login') {
        // init() will be called in the LoginPage component in this case
        return;
      }
      // The first time the app is loaded, there will not yet be an access token configured on
      // the API client. There *may* be a refresh token in storage, so attempt to exchange it
      // before calling the init() function. The exchangeRefreshToken function will throw a
      // RefreshTokenExchangeError if the refresh token is invalid or expired. If that or any other
      // exception is thrown during the exchange, we still want to call init() to finish setting up
      // the app, but we don't want to re-throw the error.
      try {
        await api.exchangeRefreshToken();
      } catch (error) {
        if (!(error instanceof RefreshTokenExchangeError)) {
          throw error;
        }
      } finally {
        await init(router);
      }
    });

    onUnmounted(() => {
      window.removeEventListener(REFRESH_TOKEN_EXPIRED_EVENT, handleRefreshTokenExpired);
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
