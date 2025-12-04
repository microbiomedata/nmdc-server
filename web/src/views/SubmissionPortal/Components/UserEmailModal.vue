<script lang="ts">
import {
  computed,
  defineComponent,
  onMounted,
  ref,
  watch,
} from '@vue/composition-api';
import Definitions from '@/definitions';
import {
  studyForm,
  studyFormValid,
  canEditSubmissionMetadata,
} from '../store';
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
  emits: ['input'],
  setup(props, { emit }) {
    const formRef = ref();
    const currentUserOrcid = computed(() => stateRefs.user.value?.orcid);

    function requiredRules(msg: string, otherRules: ((v: string) => unknown)[] = []) {
      return [
        (v: string) => !!v || msg,
        ...otherRules,
      ];
    }

    onMounted(async () => {
      formRef.value.validate();
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

    const updateEmail = (email: string | undefined) => {
      if (editEmail.value) {
        if (email == null) {
          return;
        }
        isEmailValid.value = /.+@.+\..+/.test(email);
        if (isEmailValid.value) {
          updateUser(email);
          editEmail.value = !editEmail.value;
        }
      } else {
        editEmail.value = !editEmail.value;
      }
    };

    const submitterEmail = ref(user.value?.email || '');

    studyForm.submitterEmail = submitterEmail.value;

    watch(submitterEmail, async (newEmail) => {
      if (newEmail && /.+@.+\..+/.test(newEmail)) {
        await updateUser(newEmail);
        studyForm.submitterEmail = newEmail;
      }
    });

    return {
      formRef,
      studyForm,
      studyFormValid,
      Definitions,
      requiredRules,
      canEditSubmissionMetadata,
      currentUserOrcid,
      editEmail,
      updateEmail,
      isEmailValid,
      submitterEmail,
      user,
      updateUser,
      dialog: computed({
        get: () => props.value,
        set: (v: boolean) => emit('input', v),
      }),
    };
  },
});
</script>

<template>
  <teleport to="body">
    <div>
      <v-form
        ref="formRef"
        class="my-6"
        style="max-width: 1000px;"
        :disabled="!canEditSubmissionMetadata()"
      >
        <v-text-field
          v-model="studyForm.submitterEmail"
          :rules="requiredRules('E-mail is required',[
            v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
          ])"
          validate-on-blur
          label="Submitter E-mail *"
          :hint="Definitions.submitterEmail"
          persistent-hint
          outlined
          dense
          class="my-2"
        />
      </v-form>
      <strong>* indicates required field</strong>
    </div>
  </teleport>
</template>

<!-- <template>
  <teleport to="body">
    <div
      class="modal-backdrop"
      style="position: fixed;
      background: rgba(0, 0, 0, 0.45);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;"
      @click.self="close"
    >
      <v-card
        elevation="24"
        width="420"
      >
        <v-card-title class="headline">
          <span class="title-text">Please add your e‑mail</span>
        </v-card-title>
        <v-card-text>
          <v-form
            ref="formRef"
            class="my-6"
            :disabled="!canEditSubmissionMetadata()"
            style="max-width: 1000px;"
            @submit.prevent="save"
          >
            <v-text-field
              v-model="studyForm.submitterEmail"
              :rules="requiredRules('E-mail is required',[
                v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
              ])"
              validate-on-blur
              label="Submitter E‑mail *"
              :hint="Definitions.submitterEmail"
              persistent-hint
              outlined
              dense
              class="my-2"
            />
          </v-form>
          <strong>* indicates required field</strong>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-spacer />
          <v-btn
            text
            @click="close"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            :disabled="!isFormValid"
            @click="save"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </teleport>
</template> -->
