<script setup lang="ts">
import { computed, nextTick, onMounted, useTemplateRef, watch, ref } from 'vue';
import { isEqual } from 'lodash';
import { SubmissionEditorRole } from '@/views/SubmissionPortal/types.ts';
import { useSubmissionStore } from '../store';
import { onBeforeRouteLeave } from 'vue-router';

const {
  allowedRoles = ['owner', 'editor'],
  inSampleSetContext = false,
} = defineProps<{
  allowedRoles?: SubmissionEditorRole[];
  inSampleSetContext?: boolean;
}>()

const emit = defineEmits<{
  validStateChanged: [state: null | string[]];
}>();

const store = useSubmissionStore();
const leaveDialogOpen = ref(false);
let leaveDialogPromise: Promise<boolean> | null = null;
let leaveDialogResolve: ((value: boolean) => void) | null = null;

const formRef = useTemplateRef('formRef');
const isDisabled = computed(() => store.getUneditableReason(allowedRoles, inSampleSetContext) !== undefined);
const currentErrors = computed<string[]>(() => (
  formRef.value?.errors.flatMap((err) => err.errorMessages) ?? []
));

let prevErrors: null | string[] = null;
const emitValidationState = (currErrors: string[]) => {
  if (!isEqual(currErrors, prevErrors)) {
    prevErrors = currErrors;
    emit('validStateChanged', currErrors);
  }
};

watch(currentErrors, (errors) => {
  emitValidationState(errors);
}, { flush: 'post' });

const syncValidationState = async () => {
  await nextTick();
  emitValidationState(currentErrors.value);
};

const validate = async () => {
  const result = await formRef.value?.validate();
  await syncValidationState();
  return result;
};

onMounted(() => {
  void validate();
});

function confirmLeave() {
  if (leaveDialogPromise) {
    return leaveDialogPromise;
  }
  leaveDialogOpen.value = true;

  leaveDialogPromise = new Promise<boolean>((resolve) => {
    // Stash the resolve function for use in handleLeaveDialog
    leaveDialogResolve = resolve;
  }).finally(() => {
    // Tidy up whenever the promise settles
    leaveDialogOpen.value = false;
    leaveDialogPromise = null;
    leaveDialogResolve = null;
  });
  return leaveDialogPromise;
}

onBeforeRouteLeave(async () => {
  if (!store.hasPendingImageUploads) {
    // No pending uploads, allow navigation
    return true;
  }
  // There are pending uploads, show dialog and proceed based on user choice
  return await confirmLeave();
});

function handleLeaveDialog(leave: boolean) {
  if (leaveDialogResolve === null) {
    return;
  }
  leaveDialogResolve(leave);
}

defineExpose({
  validate,
  isDisabled,
});
</script>

<template>
  <v-form
    ref="formRef"
    validate-on="eager invalid-input"
    :disabled="isDisabled"
  >
    <slot />
  </v-form>
  <v-dialog
    v-model="leaveDialogOpen"
    persistent
    max-width="500"
  >
    <v-card
      title="Unsaved Image"
      text="You have an image selected that hasn't been uploaded yet. If you leave now, it will be lost."
    >
      <v-card-actions>
        <v-btn
          color="grey"
          text
          @click="handleLeaveDialog(false)"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          text
          @click="handleLeaveDialog(true)"
        >
          Leave
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
