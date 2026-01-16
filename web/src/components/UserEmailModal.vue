<script lang="ts">
import {
  computed,
  defineComponent,
  onMounted,
  ref,
  watch,
} from 'vue';
import type { ValidationRule } from 'vuetify';
import Definitions from '@/definitions';
import {
  studyForm,
  studyFormValid,
  canEditSubmissionMetadata,
} from '../views/SubmissionPortal/store';
import { stateRefs } from '@/store';
import { api } from '@/data/api';
import { User } from '@/types';

export default defineComponent({
  name: 'UserEmailModal',
  props: {
    value: {
      type: Boolean,
      required: true,
    },
  },
  emits: ['update:value'],
  setup(props, { emit }) {
    const formRef = ref();
    const currentUserOrcid = computed(() => stateRefs.user.value?.orcid);

    function requiredRules(
      msg: string,
      otherRules: ValidationRule[] = []
    ): ValidationRule[] {
      return [
        (v: string) => !!v || msg,
        ...otherRules,
      ];
    }

    onMounted(async () => {
      if (formRef.value) {
        formRef.value.validate();
      }
    });

    const { user } = stateRefs;

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

    const submitterEmail = ref(user.value?.email || '');
    studyForm.submitterEmail = submitterEmail.value;

    watch(submitterEmail, async (newEmail) => {
      if (newEmail && /.+@.+\..+/.test(newEmail)) {
        isEmailValid.value = true;
      }
    }, { immediate: true });

    const dialog = computed({
      get: () => props.value,
      set: (v: boolean) => emit('update:value', v),
    });

    const updateEmail = async () => {
      const email = submitterEmail.value?.trim();
      if (!email || !/.+@.+\..+/.test(email)) {
        isEmailValid.value = false;
        if (formRef.value) {
          formRef.value.validate();
        }
        return;
      }
      await updateUser(email);
      studyForm.submitterEmail = email;
      dialog.value = false;
    };

    return {
      formRef,
      studyForm,
      studyFormValid,
      Definitions,
      requiredRules,
      canEditSubmissionMetadata,
      currentUserOrcid,
      editEmail,
      isEmailValid,
      submitterEmail,
      user,
      updateUser,
      updateEmail,
      dialog,
    };
  },
});
</script>

<template>
  <teleport to="body">
    <v-dialog
      v-model="dialog"
      persistent
      max-width="600"
    >
      <v-card>
        <v-card-title class="headline">
          Please add your email
        </v-card-title>
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
          <strong>* indicates required field</strong>
        </v-card-text>
        <v-card-actions>
          <v-spacer>
            <v-btn
              color="primary"
              :disabled="!isEmailValid"
              @click="updateEmail"
            >
              Save
            </v-btn>
          </v-spacer>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </teleport>
</template>
