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
            href="/login"
            v-bind="attrs"
            v-on="on"
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
              NMDC requires an ORCID ID to log in. When logged in you have access to features such as downloading
              files and the ability to create and manage metadata submissions through
              our Submission Portal.
            </p>
            <p>
              Click the "ORCID Login" button, to either register for an ORCID ID or, if you
              already have one, to sign into your ORCID account, then grant permission for NMDC to access your
              ORCID ID. This allows us to verify your identity and securely connect to
              your ORCID ID. Additionally, we may use information, such as your name and email, to associate your
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
