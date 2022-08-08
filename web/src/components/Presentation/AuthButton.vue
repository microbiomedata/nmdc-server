<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import { stateRefs } from '@/store';

export default defineComponent({
  setup() {
    const showToast = ref(false);
    async function copyToClipboard(token : string) {
      await navigator.clipboard.writeText(token);
      showToast.value = true;
    }
    return {
      me: stateRefs.user,
      showToast,
      token: '123', // todo- get the actual token
      copyToClipboard,
    };
  },
});
</script>

<template>
  <div>
    <template v-if="me">
      <v-menu
        :close-on-content-click="false"
        :nudge-width="100"
        left
        offset-x
      >
        <template #activator="{ on, attrs }">
          <v-btn
            text
            color="grey darken-2"
            v-bind="attrs"
            v-on="on"
          >
            <v-icon left>
              mdi-account-circle
            </v-icon>
            {{ me }}
          </v-btn>
        </template>

        <v-card>
          <v-list>
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title>NMDC API Token</v-list-item-title>
                <v-list-item-subtitle><a href="https://github.com/microbiomedata/nmdc-server/wiki/Search-API-Docs">Know more</a></v-list-item-subtitle>
              </v-list-item-content>

              <v-list-item-action>
                <v-btn
                  icon
                  @click="copyToClipboard(token)"
                >
                  <v-icon>mdi-clipboard-text-multiple-outline</v-icon>
                </v-btn>
              </v-list-item-action>
            </v-list-item>
          </v-list>
        </v-card>
      </v-menu>
      <v-btn
        icon
        color="grey darken-2"
        href="/logout"
      >
        <v-icon>mdi-logout</v-icon>
      </v-btn>
      <v-snackbar
        v-model="showToast"
        :timeout="1000"
        :value="true"
        absolute
        bottom
        color="primary"
      >
        Copied!
      </v-snackbar>
    </template>
    <template v-else>
      <v-btn
        text
        color="grey darken-2"
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
