<script setup lang="ts">
import { computed, useTemplateRef, watch } from 'vue';
import { isEqual } from 'lodash';
import { getSubmissionUneditableReason } from '@/views/SubmissionPortal/store';
import { SubmissionEditorRole } from '@/views/SubmissionPortal/types.ts';

const {
  minimumPermissionLevel = 'editor'
} = defineProps<{
  minimumPermissionLevel?: SubmissionEditorRole
}>()

const emit = defineEmits<{
  validStateChanged: [state: null | string[]];
}>();

const formRef = useTemplateRef('formRef');
const isDisabled = computed(() => getSubmissionUneditableReason(minimumPermissionLevel) !== undefined);

let prevErrors: null | string[] = null;
const handleValidStateChanged = () => {
  if (formRef.value === null) {
    return;
  }
  const currErrors = formRef.value.errors.flatMap(err => err.errorMessages);
  if (!isEqual(currErrors, prevErrors)) {
    prevErrors = currErrors;
    emit('validStateChanged', currErrors);
  }
};

watch(() => formRef.value?.errors, () => {
  handleValidStateChanged();
});

const validate = () => {
  formRef.value?.validate();
};

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
