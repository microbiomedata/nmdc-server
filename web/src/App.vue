<script lang="ts" setup>
import { onMounted, onUnmounted, watch, ref, defineComponent } from 'vue';
import { useRouter } from 'vue-router';
import { api, REFRESH_TOKEN_EXPIRED_EVENT, RefreshTokenExchangeError } from '@/data/api';
import { init, stateRefs } from '@/store/';

const router = useRouter();

const handleRefreshTokenExpired = () => {
  stateRefs.user.value = null;
  if (router) {
    init(router, false);
  }
};

const { user } = stateRefs;

const showEmailModal = ref(false);

watch(
  user,
  (newUser) => {
    const missingEmail = !!newUser && !newUser.email?.trim();
    showEmailModal.value = missingEmail;
  },
  { immediate: true },
);

onMounted(async () => {
  window.addEventListener(REFRESH_TOKEN_EXPIRED_EVENT, handleRefreshTokenExpired);

  if (!router) {
    return;
  }
  if (router.currentRoute.value.path === '/login') {
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
</script>

<template>
  <v-layout>
    <app-header />
    <router-view />
    <user-email-modal v-model:value="showEmailModal" />
  </v-layout>
</template>