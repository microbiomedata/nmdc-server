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
const leaveDialog = ref(false);
const pendingNext = ref<(() => void) | null>(null);

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

onBeforeRouteLeave((to, from, next) => {
  if (store.hasPendingImageUploads) {
    leaveDialog.value = true;
    pendingNext.value = next;
  } else {
    next();
  }
});

function handleLeaveDialog(leave: boolean) {
  leaveDialog.value = false;
  if (leave) {
    pendingNext.value?.();
    pendingNext.value = null;
  } else {
    pendingNext.value = null;
  }
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
    v-model="leaveDialog"
    persistent
    max-width="500"
  >
    <v-card>
      <v-card-title class="text-h5">
        Unsaved Image
      </v-card-title>
      <v-card-text>
        You have an image selected that hasn't been uploaded yet. If you leave now, it will be lost.
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
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
