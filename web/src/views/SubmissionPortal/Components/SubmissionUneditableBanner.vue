<script setup lang="ts">
import { SubmissionEditorRole } from '@/views/SubmissionPortal/types.ts';
import { getSubmissionUneditableReason, submissionLockedBy, statusDisplay } from '@/views/SubmissionPortal/store';

const { minimumPermissionLevel } = defineProps<{
  minimumPermissionLevel: SubmissionEditorRole;
}>();

const reason = getSubmissionUneditableReason(minimumPermissionLevel);
</script>

<template>
  <v-alert
    v-if="reason !== undefined"
    type="info"
    tile
    class="overflow-visible"
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
      v-if="reason === 'uneditable_status'"
    >
      This submission cannot be edited because it has status '{{ statusDisplay }}'. If you need to edit this submission, please contact
      <a
        style="color: inherit"
        href="mailto:support@microbiomedata.org"
      >support@microbiomedata.org</a>.
    </div>
  </v-alert>
</template>
