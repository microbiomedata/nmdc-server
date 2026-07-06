<script setup lang="ts">
import { SubmissionEditorRole, SubmissionStatusEnum, SubmissionStatusKey } from '@/views/SubmissionPortal/types.ts';
import { computed } from 'vue';
import { useSubmissionStore } from '../store';

const {
  allowedRoles,
  inSampleSetContext = false,
  edgeToEdge = false,
} = defineProps<{
  /**
   * The user roles that are allowed to make edits to the data entry components on the page where this banner is used.
   */
  allowedRoles: SubmissionEditorRole[];
  /**
   * Whether this banner is being used in the context of a sample set. This is needed because the sample set's status
   * can affect whether the sample set forms are editable.
   */
  inSampleSetContext?: boolean;
  /**
   * Whether the banner should extend edge-to-edge by offsetting parent container padding.
   * Use this when rendering inside a `v-container`.
   */
   edgeToEdge?: boolean;
}>();

const store = useSubmissionStore();
const submissionLockedBy = computed(() => store.submission.record?.locked_by);
const { getUneditableReason } = store;

const reason = computed(() => getUneditableReason(allowedRoles, inSampleSetContext));
const statusDisplay = computed(() => {
  const statusEnumValue = inSampleSetContext ? store.sampleSet.record?.status ?? null : null;
  if (statusEnumValue === null) {
    return 'unknown status';
  }
  return `status '${SubmissionStatusEnum[statusEnumValue as SubmissionStatusKey].title}'`
});
</script>

<template>
  <v-alert
    v-if="reason !== undefined"
    type="info"
    tile
    :class="{
      'overflow-visible': true,
      'mx-n4': edgeToEdge,
      'mt-n4': edgeToEdge,
      'mb-4': edgeToEdge,
    }"
  >
    <div
      v-if="reason === 'locked_by_other'"
    >
      This submission cannot be edited because it is currently being edited by:
      <orcid-id
        v-if="submissionLockedBy"
        class="d-inline-block"
        :orcid-id="submissionLockedBy.orcid || ''"
        :name="submissionLockedBy.name"
        :authenticated="true"
      />
      <span v-else>
        another user.
      </span>
    </div>
    <div
      v-if="reason === 'insufficient_permissions'"
    >
      Your current permission level for this submission does not allow editing of this page. Contact the submission author to request a change in permission level.
    </div>
    <div
      v-if="reason === 'already_submitted'"
    >
      This submission cannot be edited because it is already represented on the Data Portal.
    </div>
    <div
      v-if="reason === 'uneditable_status'"
    >
      This sample set cannot be edited because it has {{ statusDisplay }}. If you need to edit this sample set, please contact
      <a
        style="color: inherit"
        href="mailto:support@microbiomedata.org"
      >support@microbiomedata.org</a>.
    </div>
  </v-alert>
</template>
