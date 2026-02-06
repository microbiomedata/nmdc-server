<script setup lang="ts">
import { computed, ref, useTemplateRef, watch } from 'vue';
import moment from 'moment';
import { jwtDecode } from 'jwt-decode';
import AppBanner from '@/components/AppBanner.vue';
import OrcidId from '@/components/Presentation/OrcidId.vue';
import { stateRefs } from '@/store';
import { getRefreshToken } from '@/store/localStorage';
import { api } from '@/data/api';
import { ValidationResult } from 'vuetify/lib/composables/validation.mjs';
import useRequest from '@/use/useRequest.ts';

const refreshTokenInput = ref();
const profileFormRef = useTemplateRef('profileFormRef');

const refreshToken = getRefreshToken();
let refreshTokenExpirationDate: string;
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
function requiredRules(msg: string, otherRules: ((_v: string) => ValidationResult)[] = []) {
  return [
    (v: string) => !!v || msg,
    ...otherRules,
  ];
}

const userEmail = ref('');
watch(user, () => {
  if (user.value) {
    userEmail.value = user.value.email ?? '';
  }
}, { immediate: true });
const profileFormTouched = computed(() => userEmail.value !== user.value?.email);
const userUpdateRequest = useRequest()
const handleProfileFormSubmit = async () => {
  if (!user.value) {
    return
  }
  const update = {
    ...user.value,
    email: userEmail.value.trim(),
  }
  user.value = await userUpdateRequest.request(() => api.updateUser(user.value!.id, update));
};
</script>

<template>
  <v-main>
    <AppBanner />
    <v-container>
      <div v-if="userLoading">
        Loading...
      </div>
      <div v-else-if="user">
        <PageTitle :title="user.name">
          <template #help>
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
          </template>
          <template #subtitle>
            <orcid-id
              :orcid-id="user.orcid"
              :authenticated="false"
              :width="24"
            />
          </template>
        </PageTitle>

        <PageSection heading="Profile Information">
          <v-form
            ref="profileFormRef"
            @submit.prevent="handleProfileFormSubmit"
          >
            <v-text-field
              v-model="userEmail"
              label="Email"
              variant="outlined"
              :rules="requiredRules('E-mail is required', [
                v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
              ])"
            />
            <v-btn
              class="mt-2"
              type="submit"
              color="primary"
              :loading="userUpdateRequest.loading.value"
              :disabled="userUpdateRequest.loading.value || !profileFormTouched || !profileFormRef?.isValid"
            >
              Save
            </v-btn>
            <v-alert
              v-if="userUpdateRequest.error.value"
              class="mt-2"
              type="error"
            >
              <p>Something went wrong</p>
              {{ userUpdateRequest.error.value }}
            </v-alert>
          </v-form>
        </PageSection>

        <PageSection heading="Developer Tools">
          <p>
            To access authenticated endpoints in the <a href="/api/docs">NMDC Data and Submission Portal API</a> you
            must provide an <b>Access Token</b> in the <code>Authorization</code> header of the request. An
            <b>Access Token</b> is valid for 24 hours and can be obtained by providing your <b>Refresh Token</b> to the
            <code>/auth/refresh</code> endpoint. Your <b>Refresh Token</b> and its expiration date can be found below.
            <b>Treat this Refresh Token as securely as you would treat a password!</b>
          </p>

          <v-row>
            <v-col>
              <v-text-field
                ref="refreshTokenInput"
                v-model="refreshToken"
                label="Refresh Token"
                readonly
                variant="filled"
                :type="isTokenVisible ? 'text' : 'password'"
              >
                <template #append-inner>
                  <v-tooltip
                    bottom
                    open-delay="600"
                  >
                    <template #activator="{ props }">
                      <v-icon
                        right
                        v-bind="props"
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
                    <template #activator="{ props }">
                      <v-icon
                        right
                        v-bind="props"
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
            <v-col>
              <v-text-field
                v-model="refreshTokenExpirationDate"
                label="Expiration Date"
                readonly
                variant="filled"
                type="text"
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
        </PageSection>
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
