<script lang="ts">
import {
  computed,
  defineComponent,
  PropType,
  ref,
} from 'vue';
// WARNING: The useForm composable is not part of the Vuetify public API yet
//          https://github.com/vuetifyjs/vuetify/issues/19315
// @ts-ignore
import { useForm } from 'vuetify/lib/composables/form';
import useRequest from '@/use/useRequest';
import { SubmissionImageType } from '@/views/SubmissionPortal/types';
import { useSubmissionStore } from '../store';

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
  setup(props) {
    const fileInputRef = ref();
    const fileRef = ref<File | null>(null);
    const form = useForm();
    const store = useSubmissionStore();
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
      await store.uploadSubmissionImage(fileRef.value, props.imageType);
    });

    const { request: deleteRequest, loading: deleting, error: deleteError } = useRequest();
    const handleDelete = () => deleteRequest(() => store.deleteSubmissionImage(props.imageType));

    const handleChangeClick = () => {
      if (fileInputRef.value) {
        fileInputRef.value.$el.querySelector('input')?.click();
      }
    };

    return {
      disabled: form.isDisabled,
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
      :disabled="uploading || disabled"
      persistent-hint
      variant="outlined"
      truncate-length="100"
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
            <v-img
              :src="filePreview"
              :alt="inputLabel + ' preview'"
            />
          </v-avatar>
          <img
            v-else
            :src="filePreview"
            :alt="inputLabel + ' preview'"
            :style="{ maxHeight: '250px', maxWidth: '100%', display: 'block' }"
            class="my-2 elevation-2"
          >
        </div>
        <div v-if="!disabled && imageUrl && !fileRef">
          <v-btn-grey
            class="mr-2"
            small
            @click="handleChangeClick"
          >
            <v-icon left>
              mdi-pencil-outline
            </v-icon>
            Change
          </v-btn-grey>
          <v-btn-grey
            :loading="deleting"
            :disabled="deleting"
            small
            @click="handleDelete"
          >
            <v-icon left>
              mdi-trash-can-outline
            </v-icon>
            Remove
          </v-btn-grey>
        </div>
        <div v-else-if="fileRef">
          <v-btn
            class="mr-2"
            color="primary"
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
          <v-btn-grey
            small
            :disabled="uploading"
            @click="fileRef = null"
          >
            Cancel
          </v-btn-grey>
        </div>
      </div>

      <v-alert
        v-if="uploadError"
        type="error"
        outlined
        class="mt-2"
      >
        Error uploading image: {{ uploadError }}
      </v-alert>
      <v-alert
        v-if="deleteError"
        type="error"
        outlined
        class="mt-2"
      >
        Error deleting image: {{ deleteError }}
      </v-alert>
    </div>
  </div>
</template>
