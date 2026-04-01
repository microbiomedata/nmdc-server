<script setup lang="ts">
import { ref } from 'vue';

interface ImportExportButtonsProps {
  /**
   * Whether the import button should be disabled.
   */
  importDisabled?: boolean;
}

withDefaults(defineProps<ImportExportButtonsProps>(), {
  importDisabled: false,
});

const emit = defineEmits<{
  export: [],
  import: [file: File],
}>();

const xlsxFileInput = ref();

function showOpenFileDialog() {
  xlsxFileInput.value.click();
}

function handleFileInputChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (!target || !target.files) {
    return;
  }
  const firstFile = target.files[0];
  if (firstFile) {
    emit('import', firstFile);
  }

  // Reset the file input so that the same filename can be loaded multiple times
  target.value = '';
}
</script>

<template>
  <v-card elevation="0">
    <v-card-title>
      Import & Export
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col>
          <v-btn
            color="primary"
            block
            variant="outlined"
            @click="$emit('export')"
          >
            <v-icon class="pr-2">
              mdi-file-download
            </v-icon>
            Export to XLSX
          </v-btn>
        </v-col>
      </v-row>

      <v-row>
        <v-col>
          <label for="tsv-file-select">
            <input
              ref="xlsxFileInput"
              type="file"
              style="position: fixed; top: -100em"
              accept=".xls,.xlsx"
              @change="handleFileInputChange"
            >
            <v-btn
              color="primary"
              block
              variant="outlined"
              :disabled="importDisabled"
              @click="showOpenFileDialog"
            >
              <v-icon class="pr-2">
                mdi-file-upload
              </v-icon>
              Import from XLSX
            </v-btn>
          </label>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>
