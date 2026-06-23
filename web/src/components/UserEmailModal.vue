<script setup lang="ts">
import { computed, onMounted, ref, useTemplateRef, } from 'vue';
import type { ValidationRule } from 'vuetify';
import { stateRefs } from '@/store';
import { api } from '@/data/api';
import { User } from '@/types';
import useRequest from '@/use/useRequest.ts';

const props = defineProps<{
  value: boolean;
}>();

const emit = defineEmits<{
  'update:value': [value: boolean];
}>();

const formRef = useTemplateRef('formRef');

function requiredRules(
  msg: string,
  otherRules: ValidationRule[] = []
): ValidationRule[] {
  return [
    (v: string) => !!v || msg,
    ...otherRules,
  ];
}

onMounted(() => {
  if (formRef.value) {
    formRef.value.validate();
  }
});

const { user } = stateRefs;

const updateUserRequest = useRequest();
const updateUser = async (value:string) => {
  if (!user.value) {
    return
  }
  const update: User = {
    ...user.value,
    email: value,
  };
  user.value = await updateUserRequest.request(() => api.updateUser(user.value!.id, update));
};

/**
 * Returns `true` if the specified string resembles an email address.
 * 
 * Note: This basic check still accepts things like ` u s e r @ example . com `.
 *
 * Reference: https://en.wikipedia.org/wiki/Email_address#Validation_and_verification
 */
const validateEmailAddr = (s: string) => /.+@.+\..+/.test(s);

const submitterEmail = ref(user.value?.email ?? '');

// dialog is bound to the modal to determine whether to display or not
const dialog = computed({
  get: () => props.value,
  set: (v: boolean) => emit('update:value', v),
});

/**
 * Updates the user's email address to be the one in the form (trimmed), if the latter is valid.
 */
const updateEmail = async () => {
  const trimmedEmailAddr = submitterEmail.value.trim();
  if (validateEmailAddr(trimmedEmailAddr)) {
    await updateUser(trimmedEmailAddr);
    dialog.value = false;
  }
};
</script>

<template>
  <v-dialog
    v-model="dialog"
    persistent
    max-width="600"
  >
    <v-card title="Update Email Address">
      <v-form
        ref="formRef"
        class="my-6"
        @submit.prevent="updateEmail"
      >
        <v-card-text>
          We were unable to obtain your email address from ORCID. Please provide your email address below to continue.
        </v-card-text>
        <v-card-text>
          <v-text-field
            v-model="submitterEmail"
            :rules="requiredRules('Email is required', [
              v => validateEmailAddr(v.trim()) || 'Email must be valid',
            ])"
            validate-on-blur
            label="User Email *"
            hint="User email is required to complete your user profile."
            persistent-hint
            outlined
            dense
            class="my-2"
          />
          <v-alert
            v-if="updateUserRequest.error.value"
            type="error"
            class="mt-4"
          >
            Something went wrong while updating your email address. Please try again, and if the problem persists, contact us for assistance.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer class="text-center">
            <v-btn
              color="primary"
              :disabled="!formRef?.isValid || updateUserRequest.loading.value"
              :loading="updateUserRequest.loading.value"
              type="submit"
            >
              Save
            </v-btn>
          </v-spacer>
        </v-card-actions>
      </v-form>
    </v-card>
  </v-dialog>
</template>
