<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import moment from 'moment';
import { jwtDecode } from 'jwt-decode';
import AppBanner from '@/components/AppBanner.vue';
import { api } from '@/data/api';
import OrcidId from '@/components/Presentation/OrcidId.vue';
import { stateRefs } from '@/store';

export default defineComponent({
  name: 'UserDetailPage',
  components: { OrcidId, AppBanner },

  setup() {
    const refreshToken = api.getRefreshToken();
    let tokenExpiration;
    if (refreshToken != null) {
      const decodedToken = jwtDecode(refreshToken);
      if (decodedToken.exp != null) {
        tokenExpiration = moment.unix(decodedToken.exp).format('YYYY-MM-DD HH:mm:ss');
      }
    }
    const showToken = ref(false);
    const showCopyRefreshTokenSnackbar = ref(false);

    const copyRefreshTokenToClipboard = async () => {
      if (refreshToken != null) {
        await navigator.clipboard.writeText(refreshToken);
        showCopyRefreshTokenSnackbar.value = true;
      }
    };

    const toggleTokenVisibility = () => {
      showToken.value = !showToken.value;
    };

    const handleRefreshTokenInputClick = (event: MouseEvent) => {
      event.preventDefault();
      if (showToken.value) {
        (event.target as HTMLInputElement).select();
      }
    };

    return {
      user: stateRefs.user,
      userLoading: stateRefs.userLoading,
      // loading,
      // error,
      base: window.location.origin,
      refreshToken,
      tokenExpiration,
      showCopyRefreshTokenSnackbar,
      showToken,
      toggleTokenVisibility,
      handleRefreshTokenInputClick,
      copyRefreshTokenToClipboard,
    };
  },
});
</script>

<template>
  <v-main>
    <AppBanner v-if="false" />
    <v-container>
      <div v-if="userLoading">
        Loading...
      </div>
      <div v-else-if="user">
        <div class="mb-8">
          <div class="py-2">
            <span class="text-h4">{{ user.name }}</span>
            <v-chip
              v-if="user.is_admin"
              class="mx-2"
              style="vertical-align: baseline"
              color="primary"
            >
              <v-icon
                left
              >
                mdi-shield-account
              </v-icon>
              Admin
            </v-chip>
          </div>
          <orcid-id
            :orcid-id="user.orcid"
            :authenticated="false"
            :width="24"
          />
        </div>

        <div class="mb-8">
          <div class="text-h5 py-2">
            Developer Tools
          </div>
          <p>
            To access authenticated endpoints in the <a href="/api/docs">NMDC Data and Submission Portal API</a> you
            must provide an <b>Access Token</b> in the <code>Authorization</code> header of the request. An
            <b>Access Token</b> is valid for 24 hours and can be obtained by providing your <b>Refresh Token</b> to the
            <code>/auth/refresh</code> endpoint. Your <b>Refresh Token</b> and its expiration date can be found below.
            <b>Treat this Refresh Token as securely as you would treat a password!</b>
          </p>

          <v-row>
            <v-col
              cols="auto"
            >
              <v-text-field
                label="Refresh Token"
                readonly
                filled
                :type="showToken ? 'text' : 'password'"
                :value="refreshToken"
                @click="handleRefreshTokenInputClick"
              >
                <template #append>
                  <v-icon
                    right
                    @click="toggleTokenVisibility"
                  >
                    {{ showToken ? 'mdi-eye' : 'mdi-eye-off' }}
                  </v-icon>
                  <v-icon
                    right
                    @click="copyRefreshTokenToClipboard"
                  >
                    mdi-content-copy
                  </v-icon>
                </template>
              </v-text-field>
            </v-col>
            <v-col
              cols="auto"
            >
              <v-text-field
                label="Expiration Date"
                readonly
                filled
                type="text"
                :value="tokenExpiration"
              />
            </v-col>
          </v-row>

          <div class="text-h6 py-2">
            Example
          </div>
          <ol class="mb-4">
            <li>
              In your project, store your Refresh Token in a variable named <code>REFRESH_TOKEN</code>.
            </li>
            <li>
              Exchange your Refresh Token for an Access Token which will be valid for 24 hours.
              <pre>
curl \
  -H "content-type: application/json" \
  -d "{ \"refresh_token\": \"$REFRESH_TOKEN\"}" \
  {{ base }}/auth/refresh
              </pre>
            </li>
            <li>
              Store the value returned in the <code>access_token</code> in your program and use it when making
              authenticated API requests.
              <pre>
curl \
  -H "content-type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  {{ base }}/api/me
              </pre>
            </li>
            <li>
              If your program runs for more than 24 hours. Step 2 will need to be repeated once the Access Token
              expires.
            </li>
            <li>
              When your Refresh Token expires (one year after your last login), visit this page again to get a new one.
            </li>
          </ol>
        </div>
      </div>
      <div v-else>
        You must log in to view this page.
      </div>

      <v-snackbar
        v-model="showCopyRefreshTokenSnackbar"
        timeout="3000"
      >
        Refresh Token Copied to Clipboard
      </v-snackbar>
    </v-container>
  </v-main>
</template>
