<script lang="ts">
import {
  computed,
  defineComponent,
  PropType,
  ref,
} from 'vue';
import { deleteSubmissionImage, generateSignedUploadUrl, setSubmissionImage } from '@/views/SubmissionPortal/store/api';
import useRequest from '@/use/useRequest';
import { SubmissionImageType } from '@/views/SubmissionPortal/types';

export default defineComponent({
  props: {
    /**
     * Label for the file input.
     */
    inputLabel: {
      type: String,
      required: true,
    },
    /**
     * Hint text for the file input.
     */
    inputHint: {
      type: String,
      required: false,
      default: '',
    },
    /**
     * Icon prepended to the file input.
     */
    inputIcon: {
      type: String,
      required: false,
      default: 'mdi-image',
    },
    /**
     * Current image URL, or null if no image is set.
     */
    imageUrl: {
      // See: https://github.com/vuejs/core/issues/3948#issuecomment-860466204
      type: null as unknown as PropType<string | null>,
      validator: (val: unknown) => typeof val === 'string' || val === null,
      required: true,
    },
    /**
     * The type of image being uploaded (e.g., 'pi_image' or 'primary_study_image').
     */
    imageType: {
      type: String as PropType<SubmissionImageType>,
      required: true,
    },
    /**
     * Whether to display the preview image as an avatar (circular) or not (show original aspect ratio).
     */
    isAvatar: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: [
    /**
     * Emitted when the upload request completes successfully. Will be called with the updated MetadataSubmissionRecord.
     */
    'on-upload-success',
    /**
     * Emitted when the delete request completes successfully.
     */
    'on-delete-success',
  ],
  setup(props, { root, emit }) {
    const fileInputRef = ref();
    const fileRef = ref<File | null>(null);
    const filePreview = computed(() => {
      if (fileRef.value) {
        return URL.createObjectURL(fileRef.value);
      }
      return props.imageUrl;
    });

    const { request: uploadRequest, loading: uploading, error: uploadError } = useRequest();
    const handleUpload = () => uploadRequest(async () => {
      if (!fileRef.value) {
        return;
      }
      const submissionId = root.$route.params.id;
      // First, get a signed URL from the backend
      const signedUrlResponse = await generateSignedUploadUrl(submissionId, fileRef.value);

      // Next, upload the file to the signed URL
      const uploadResponse = await fetch(signedUrlResponse.url, {
        method: 'PUT',
        headers: {
          'Content-Type': fileRef.value.type,
        },
        body: fileRef.value,
      });

      // If the upload was successful, update the submission record with the new image reference and emit a success
      // event with the updated record
      if (uploadResponse.ok) {
        const updatedSubmission = await setSubmissionImage(submissionId, fileRef.value, signedUrlResponse.object_name, props.imageType);
        fileRef.value = null;
        emit('on-upload-success', updatedSubmission);
      } else {
        throw new Error('File upload failed');
      }
    });

    const { request: deleteRequest, loading: deleting, error: deleteError } = useRequest();
    const handleDelete = () => deleteRequest(async () => {
      const submissionId = root.$route.params.id;
      await deleteSubmissionImage(submissionId, props.imageType);
      emit('on-delete-success');
    });

    const handleChangeClick = () => {
      if (fileInputRef.value) {
        fileInputRef.value.$el.querySelector('input')?.click();
      }
    };

    return {
      fileInputRef,
      fileRef,
      filePreview,
      uploading,
      uploadError,
      handleUpload,
      deleting,
      deleteError,
      handleDelete,
      handleChangeClick,
    };
  },
});
</script>

<template>
  <div>
    <v-file-input
      ref="fileInputRef"
      v-model="fileRef"
      accept="image/*"
      :label="inputLabel"
      :hint="inputHint"
      :prepend-icon="inputIcon"
      :disabled="uploading"
      persistent-hint
      outlined
      dense
      truncate-length="100"
      class="my-2"
    />

    <div class="ml-8">
      <div class="d-inline-flex flex-column align-center">
        <div
          v-if="filePreview"
          class="my-2"
        >
          <v-avatar
            v-if="isAvatar"
            :size="100"
            class="my-2 elevation-2"
          >
            <img
              :src="filePreview"
              :alt="inputLabel + ' preview'"
            >
          </v-avatar>
          <img
            v-else
            :src="filePreview"
            :alt="inputLabel + ' preview'"
            :style="{ maxHeight: '250px', maxWidth: '100%', display: 'block' }"
            class="my-2 elevation-2"
          >
        </div>
        <div v-if="imageUrl && !fileRef">
          <v-btn
            class="mr-2"
            depressed
            small
            @click="handleChangeClick"
          >
            <v-icon left>
              mdi-pencil-outline
            </v-icon>
            Change
          </v-btn>
          <v-btn
            :loading="deleting"
            :disabled="deleting"
            depressed
            small
            @click="handleDelete"
          >
            <v-icon left>
              mdi-trash-can-outline
            </v-icon>
            Remove
          </v-btn>
        </div>
        <div v-else-if="fileRef">
          <v-btn
            class="mr-2"
            color="primary"
            depressed
            small
            :loading="uploading"
            :disabled="uploading"
            @click="handleUpload"
          >
            <v-icon left>
              mdi-cloud-upload-outline
            </v-icon>
            Upload
          </v-btn>
          <v-btn
            depressed
            small
            :disabled="uploading"
            @click="fileRef = null"
          >
            Cancel
          </v-btn>
        </div>
      </div>

      <v-alert
        v-if="uploadError"
        type="error"
        outlined
        class="mt-2"
      >
        Error uploading image: {{ uploadError.message }}
      </v-alert>
      <v-alert
        v-if="deleteError"
        type="error"
        outlined
        class="mt-2"
      >
        Error deleting image: {{ deleteError.message }}
      </v-alert>
    </div>
  </div>
</template>
