<script lang="ts">
import {
  defineComponent,
  onMounted,
  onUnmounted,
  // watch,
  computed,
} from '@vue/composition-api';
// import { VDialog } from 'vuetify/lib';
import AppHeader from '@/components/Presentation/AppHeader.vue';
import UserEmailModal from './views/SubmissionPortal/Components/UserEmailModal.vue';
import { stateRefs, init } from '@/store/';
import { useRouter } from '@/use/useRouter';
import { api, REFRESH_TOKEN_EXPIRED_EVENT, RefreshTokenExchangeError } from '@/data/api';
// import {
//   showEmailModal,
// } from './views/SubmissionPortal/store/index';

export default defineComponent({
  name: 'App',
  components: { AppHeader, UserEmailModal },
  setup() {
    const router = useRouter();

    const handleRefreshTokenExpired = () => {
      stateRefs.user.value = null;
      if (router) {
        init(router, false);
      }
    };

    const { user } = stateRefs;

    const showEmailModal = computed(() => !!user && !user.value?.email?.trim());

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
      showEmailModal,
    };
  },
});
</script>

<template>
  <v-app>
    <app-header />
    <!-- <v-dialog v-model="isModalOpen" max-width="400">
      <v-card>
        <v-card-title class="headline">Notice</v-card-title>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" text @click="isModalOpen = false">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog> -->
    <keep-alive>
      <router-view />
    </keep-alive>
    <!-- <user-email-modal v-model="showEmailModal" /> -->
    <user-email-modal
      v-if="showEmailModal"
      @close="showEmailModal = false"
    />
  </v-app>
</template>
