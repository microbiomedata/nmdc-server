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
              NMDC is collecting your ORCID ID so we can turn on features
              like file downloads and the ability to create and manage metadata submissions through
              our Submission Portal.
            </p>
            <p>
              When you click the "Login" button, we will ask you to share your
              ID using an authenticated process, either by registering for an ORCID ID or, if you
              already have one, to sign into your ORCID account, then granting permission to get your
              ORCID ID. We do this to ensure that you are correctly identified and securely connected to
              your ORCID ID.
            </p>

            <p>Learn more about <a href="https://orcid.org/blog/2017/02/20/whats-so-special-about-signing">what's so special about signing in?</a></p>

            <p>
              Additionally, we will use information from your ORCID record, like your name, to connect you with your NMDC submissions.
            </p>
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
