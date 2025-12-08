<script setup lang="ts">
const props = defineProps<{
  json: any;
  filename: string;
}>();

function download() {
  console.log('Downloading JSON', props.json);
  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(props.json, null, 2));
  const downloadAnchorNode = document.createElement('a');
  downloadAnchorNode.setAttribute('href', dataStr);
  downloadAnchorNode.setAttribute('download', props.filename);
  document.body.appendChild(downloadAnchorNode);
  downloadAnchorNode.click();
  downloadAnchorNode.remove();
}
</script>

<template>
  <v-btn 
    color="primary" 
    @click="download"
  >
    <v-icon class="mr-2">
      mdi-download
    </v-icon>
    Download Sample Data
  </v-btn>
</template>