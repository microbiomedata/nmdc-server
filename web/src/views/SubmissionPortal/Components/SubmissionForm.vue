<script setup lang="ts">
import { useTemplateRef, watch } from 'vue';
import { isEqual } from 'lodash';

const emit = defineEmits<{
  validStateChanged: [state: null | string[]];
}>();

const formRef = useTemplateRef('formRef');

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
})

const validate = () => {
  formRef.value?.validate();
};

defineExpose({
  validate,
  isDisabled: false,
});
</script>

<template>
  <v-form
    ref="formRef"
    validate-on="eager invalid-input"
  >
    <slot />
  </v-form>
</template>
