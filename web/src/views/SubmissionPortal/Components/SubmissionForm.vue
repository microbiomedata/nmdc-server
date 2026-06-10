<script setup lang="ts">
import { computed, nextTick, onMounted, useTemplateRef, watch } from 'vue';
import { isEqual } from 'lodash';
import { SubmissionEditorRole } from '@/views/SubmissionPortal/types.ts';
import { useSubmissionStore } from '../store';

const {
  allowedRoles = ['owner', 'editor']
} = defineProps<{
  allowedRoles?: SubmissionEditorRole[]
}>()

const emit = defineEmits<{
  validStateChanged: [state: null | string[]];
}>();

const store = useSubmissionStore();

const formRef = useTemplateRef('formRef');
const isDisabled = computed(() => store.getSubmissionUneditableReason(allowedRoles) !== undefined);
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
</template>
