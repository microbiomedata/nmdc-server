<template>
  <v-container>
    <v-stepper
      flat
      style="margin: 0 -24px;"
    >
      <v-stepper-header>
        <v-stepper-step step="1">
          Study Information
        </v-stepper-step>
        <v-divider />
        <v-stepper-step step="2">
          Multiomics Data
        </v-stepper-step>
        <v-divider />
        <v-stepper-step step="3">
          Environment Package
        </v-stepper-step>
        <v-divider />
        <v-stepper-step step="4">
          Customize Metadata Export
        </v-stepper-step>
        <v-divider />
        <v-stepper-step step="5">
          Validate and Submit
        </v-stepper-step>
      </v-stepper-header>
    </v-stepper>
    <v-divider class="py-2" />
    <router-view />
  </v-container>
</template>
