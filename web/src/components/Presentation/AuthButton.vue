<script lang="ts">
import { defineComponent } from 'vue';
import { useRouter } from 'vue-router';
import { init, stateRefs } from '@/store';
import { api } from '@/data/api';

export default defineComponent({
  props: {
    nav: {
      type: Boolean,
      default: false,
    },
  },
  setup() {
    const router = useRouter();

    function handleLogin() {
      if (!router) {
        api.initiateOrcidLogin();
        return;
      }

      const submissionState = 'submission';
      const submissionRegex = new RegExp(submissionState);
      let state = '';
      if (submissionRegex.test(router.currentRoute.value.path)) {
        state += submissionState;
      }
      api.initiateOrcidLogin(state);
    }

    async function handleLogout() {
      try {
        await api.logout();
      } catch (e) {
        // This can happen if the user attempts to log out after their access token has expired
        // and that's okay to silently ignore
      } finally {
        stateRefs.user.value = null;
        if (router) {
          await init(router, false);
        }
      }
    }

    return {
      handleLogin,
      handleLogout,
      me: stateRefs.user,
      loading: stateRefs.userLoading,
    };
  },
});
</script>

<template>
  <div>
    <template v-if="loading">
      <div class="d-flex align-center user-loading">
        <img
          width="24px"
          class="mx-2"
          alt="ORCID logo"
          src="https://orcid.org/assets/vectors/orcid.logo.icon.svg"
        >
        <v-skeleton-loader
          type="text"
          min-width="100"
          class="m-0"
        />
      </div>
    </template>
    <template v-else-if="me">
      <v-btn
        :text="!nav"
        :plain="nav"
        :small="nav"
        :ripple="!nav"
        :to="{ name: 'User' }"
      >
        <v-icon left>
          mdi-account-circle
        </v-icon>
        {{ me.name }}
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
        @click="handleLogout"
      >
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </template>
    <template v-else>
      <v-menu
        bottom
        max-width="500"
        :open-on-hover="true"
        transition="fade-transition"
        offset-y
        content-class="login-btn-orcid-help"
        class="login-btn-orcid-help"
      >
        <template #activator="{ on, attrs }">
          <v-btn
            :text="!nav"
            :plain="nav"
            :small="nav"
            v-bind="attrs"
            v-on="on"
            @click="handleLogin"
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
        <v-card>
          <v-card-title>ORCID Account Integration</v-card-title>
          <v-card-text>
            <p>
              NMDC requires an ORCID iD to log in. When logged in you have access to features such as downloading
              files and the ability to create and manage metadata submissions through
              our Submission Portal.
            </p>
            <p>
              Click the "ORCID Login" button, to either register for an ORCID iD or, if you
              already have one, to sign into your ORCID account, then grant permission for NMDC to access your
              ORCID iD. This allows us to verify your identity and securely connect to
              your ORCID iD. Additionally, we may use information, such as your name and email, to associate your
              ORCID record with your NMDC submissions.
            </p>
            <p>Learn more about <a href="https://orcid.org/blog/2017/02/20/whats-so-special-about-signing">what's so special about signing in.</a></p>
          </v-card-text>
        </v-card>
      </v-menu>
    </template>
  </div>
</template>

<style scoped>
.login-btn-orcid-help {
  background-color: white;
}
</style>
<style>
.v-skeleton-loader__text {
  margin: 0;
}
</style>
