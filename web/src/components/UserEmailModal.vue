<script setup lang="ts">
import { computed, onMounted, ref, useTemplateRef, } from 'vue';
import type { ValidationRule } from 'vuetify';
import { stateRefs } from '@/store';
import { api } from '@/data/api';
import { User } from '@/types';

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

const updateUser = async (value:string) => {
  if (!user.value) {
    return
  }
  const update: User = {
    ...user.value,
    email: value,
  };
  user.value = await api.updateUser(user.value.id, update);
};

const submitterEmail = ref(user.value?.email ?? '');

// dialog is bound to the modal to determine whether to display or not
const dialog = computed({
  get: () => props.value,
  set: (v: boolean) => emit('update:value', v),
});

const updateEmail = async () => {
  const email = submitterEmail.value?.trim();
  await updateUser(email);
  dialog.value = false;
};
</script>

<template>
  <v-dialog
    v-model="dialog"
    persistent
    max-width="600"
  >
    <v-card title="Update Email Address">
      <v-card-text>
        We were unable to obtain your email address from ORCID. Please provide your email address below to continue.
      </v-card-text>
      <v-card-text>
        <v-form
          ref="formRef"
          class="my-6"
        >
          <v-text-field
            v-model="submitterEmail"
            :rules="requiredRules('Email is required', [
              v => /.+@.+\..+/.test(v) || 'Email must be valid',
            ])"
            validate-on-blur
            label="User Email *"
            hint="User email is required to complete your user profile."
            persistent-hint
            outlined
            dense
            class="my-2"
          />
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer class="text-center">
          <v-btn
            color="primary"
            :disabled="!formRef?.isValid"
            @click="updateEmail"
          >
            Save
          </v-btn>
        </v-spacer>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
