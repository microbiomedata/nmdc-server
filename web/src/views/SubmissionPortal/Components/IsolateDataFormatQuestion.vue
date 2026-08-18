<script setup lang="ts">
import { IsolateDataFormat } from '@/views/SubmissionPortal/types.ts';

const model = defineModel<IsolateDataFormat | null>({ required: true });
defineProps<{
  disabled?: boolean
}>();
const options: { value: IsolateDataFormat, label: string }[] = [
  {
    value: 'interleaved',
    label: 'My sequencing data is in interleaved format',
  },
  {
    value: 'non-interleaved',
    label: 'My sequencing data is in non-interleaved format',
  },
  {
    value: 'insdc-repository',
    label: "I have INSDC run identifiers from submitting to NCBI's SRA or other INSDC repository",
  },
]
</script>

<template>
  <v-select
    v-model="model"
    :items="options"
    item-title="label"
    item-value="value"
    label="Select one of the following options"
    :rules="[(v) => !!v || 'Please select an option']"
    :disabled="disabled"
  />
</template>
