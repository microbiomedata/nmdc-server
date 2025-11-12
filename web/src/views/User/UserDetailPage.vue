<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import moment from 'moment';
import { jwtDecode } from 'jwt-decode';
import AppBanner from '@/components/AppBanner.vue';
import OrcidId from '@/components/Presentation/OrcidId.vue';
import { stateRefs } from '@/store';
import { getRefreshToken } from '@/store/localStorage';
import { User } from '@/types';
import { api } from '@/data/api';

export default defineComponent({
  name: 'UserDetailPage',
  components: { OrcidId, AppBanner },

  setup() {
    const refreshTokenInput = ref();

    const refreshToken = getRefreshToken();
    let refreshTokenExpirationDate;
    if (refreshToken != null) {
      const decodedToken = jwtDecode(refreshToken);
      if (decodedToken.exp != null) {
        refreshTokenExpirationDate = moment.unix(decodedToken.exp).format('YYYY-MM-DD HH:mm:ss');
      }
    }
    const isTokenVisible = ref(false);
    const isCopyRefreshTokenSnackbarVisible = ref(false);

    const handleRefreshTokenCopyButtonClick = async () => {
      if (refreshToken != null) {
        await navigator.clipboard.writeText(refreshToken);
        isCopyRefreshTokenSnackbarVisible.value = true;
      }
    };
    const { user, userLoading } = stateRefs;
    const handleRefreshTokenVisibilityButtonClick = async () => {
      isTokenVisible.value = !isTokenVisible.value;
      if (isTokenVisible.value) {
        // Wait for the type of the input to change before selecting the text.
        // For some reason, nextTick isn't enough in this case.
        setTimeout(() => {
          refreshTokenInput.value.$refs.input.select();
        }, 50);
      }
    };
    function requiredRules(msg: string, otherRules: ((v: string) => unknown)[] = []) {
      return [
        (v: string) => !!v || msg,
        ...otherRules,
      ];
    }
    const updateUser = async (value:string) => {
      const update: User = {
        id: user.value?.id as string,
        orcid: user.value?.orcid as string,
        name: user.value?.name as string,
        email: value,
        is_admin: user.value?.is_admin as boolean,
      };
      await api.updateUser(user.value?.id as string, update);
    };
    const editEmail = ref(false);

    const isEmailValid = ref(false);

    const updateEmail = (email: string | undefined) => {
      if (editEmail.value) {
        if (email == null) {
          return;
        }
        // isEmailValid.value = /.+@.+\..+/.test(email);
        // if (isEmailValid.value) {
        //   updateUser(email);
        //   editEmail.value = !editEmail.value;
        // }
        isEmailValid.value = email === '' || /.+@.+\..+/.test(email);
        if (isEmailValid.value) {
          updateUser(email || '');
          if (user.value) {
            user.value.email = email || '';
          }
          editEmail.value = !editEmail.value;
        }
      } else {
        editEmail.value = !editEmail.value;
      }
    };

    return {
      editEmail,
      updateEmail,
      isEmailValid,
      user,
      userLoading,
      origin: window.location.origin,
      refreshToken,
      refreshTokenExpirationDate,
      refreshTokenInput,
      isCopyRefreshTokenSnackbarVisible,
      isTokenVisible,
      handleRefreshTokenVisibilityButtonClick,
      handleRefreshTokenCopyButtonClick,
      updateUser,
      requiredRules,
    };
  },
});
</script>

<template>
  <v-main>
    <AppBanner />
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
          <v-row>
            <v-col
              cols="3"
              class="pt-6"
            >
              <v-text-field
                v-model="user.email"
                label="Email"
                dense
                :readonly="!editEmail"
                filled
              >
                <template
                  #append
                >
                  <v-btn
                    icon
                    @click="updateEmail(user.email)"
                  >
                    <v-icon
                      v-text="!editEmail ? 'mdi-pencil' : 'mdi-content-save'"
                    />
                  </v-btn>
                </template>
                <template
                  v-if="!user.email"
                  #append-outer
                >
                  <v-tooltip
                    right
                  >
                    <template #activator="{ on, attrs }">
                      <v-icon
                        right
                        color="red"
                        v-bind="attrs"
                        v-on="on"
                      >
                        mdi-alert-circle
                      </v-icon>
                    </template>
                    <span>Email is required</span>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
          </v-row>
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
                ref="refreshTokenInput"
                label="Refresh Token"
                readonly
                filled
                :type="isTokenVisible ? 'text' : 'password'"
                :value="refreshToken"
              >
                <template #append>
                  <v-tooltip
                    bottom
                    open-delay="600"
                  >
                    <template #activator="{ on, attrs }">
                      <v-icon
                        right
                        v-bind="attrs"
                        v-on="on"
                        @click="handleRefreshTokenVisibilityButtonClick"
                      >
                        {{ isTokenVisible ? 'mdi-eye' : 'mdi-eye-off' }}
                      </v-icon>
                    </template>
                    <span v-if="isTokenVisible">Hide Token</span>
                    <span v-else>Show Token</span>
                  </v-tooltip>
                  <v-tooltip
                    bottom
                    open-delay="600"
                  >
                    <template #activator="{ on, attrs }">
                      <v-icon
                        right
                        v-bind="attrs"
                        v-on="on"
                        @click="handleRefreshTokenCopyButtonClick"
                      >
                        mdi-content-copy
                      </v-icon>
                    </template>
                    <span>Copy Token</span>
                  </v-tooltip>
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
                :value="refreshTokenExpirationDate"
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
              <pre class="grey lighten-4 my-2 pa-2">
curl \
  -H "content-type: application/json" \
  -d "{ \"refresh_token\": \"$REFRESH_TOKEN\"}" \
  {{ origin }}/auth/refresh</pre>
            </li>
            <li>
              Store the value returned in the <code>access_token</code> in your program and use it when making
              authenticated API requests.
              <pre class="grey lighten-4 my-2 pa-2">
curl \
  -H "content-type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  {{ origin }}/api/me</pre>
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
        v-model="isCopyRefreshTokenSnackbarVisible"
        timeout="3000"
      >
        Refresh Token Copied to Clipboard
      </v-snackbar>
    </v-container>
  </v-main>
</template>
