<script setup lang="ts">
import { computed, ref, useTemplateRef, watch, } from 'vue';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';
import { BiosafetyLevels } from '@/views/SubmissionPortal/types';
import SubmissionContextShippingSummary from './SubmissionContextShippingSummary.vue';
import { ValidationResult } from 'vuetify/lib/composables/validation.mjs';
import { formatShippingDate } from '../utils';
import SubmissionForm from '@/views/SubmissionPortal/Components/SubmissionForm.vue';
import { useSubmissionStore } from '../store';

const store = useSubmissionStore();
const senderShippingInfoForm = computed(() => store.sampleSet.forms.senderShippingInfoForm);

const senderShippingInfoFormRef = useTemplateRef<InstanceType<typeof SubmissionForm>>('senderShippingInfoFormRef');
const senderShippingInfoFormValid = computed(() => store.sampleSet.forms.senderShippingInfoForm.validation?.length === 0);
const showSenderShippingInfoForm = ref(false);
const datePicker = ref(false);
const sampleEnumValues = Object.keys(NmdcSchema.enums.SampleTypeEnum.permissible_values);
const biosafetyLevelValues = Object.values(BiosafetyLevels);
const shippingConditionsItems = [
  'Store frozen: transported within a cold chain and stored at -70°C to -80°C upon delivery.',
  'Store frozen: transported within a cold chain and stored at -20°C (4°F).',
  'Store Refrigerated: at 2°-8°C (36°-46°F): for heat sensitive products that must not be frozen.',
  'Room temperature: Store at 15°-25°C (59°-77°F).',
];

const expectedShippingDate = computed({
  get: () => {
    return store.sampleSet.forms.senderShippingInfoForm.expectedShippingDate
      ? new Date(store.sampleSet.forms.senderShippingInfoForm.expectedShippingDate)
      : null;
  },
  set: (newValue: Date | null) => {
    store.sampleSet.forms.senderShippingInfoForm.expectedShippingDate = newValue ? newValue.toISOString() : null;
  },
});

function requiredRules(msg: string, otherRules: ((_v: string) => ValidationResult)[]) {
  return [
    (v: string) => !!v || msg,
    ...otherRules,
  ];
}

watch(showSenderShippingInfoForm, () => {
  senderShippingInfoFormRef.value?.validate();
});

function handleExpectedShippingDateClear() {
  expectedShippingDate.value = null;
}
</script>

<template>
  <div>
    <v-card
      class="mt-4 pa-0"
      variant="outlined"
      :style="senderShippingInfoFormValid ? '' : 'border: 2px solid red'"
    >
      <v-card-text
        class="pt-2"
        style="min-height: 100px;"
      >
        <span :class="{'error--text': !senderShippingInfoFormValid}">EMSL Shipping Info *</span>
        <p
          v-if="!senderShippingInfoFormValid"
          class="error--text"
        >
          Sender's shipping information is required
        </p>
        <submission-context-shipping-summary class="mt-6" />
      </v-card-text>
      <v-dialog
        v-model="showSenderShippingInfoForm"
        scrollable
        width="1200"
        eager
      >
        <template #activator="{ props }">
          <v-btn
            :disabled="senderShippingInfoFormRef?.isDisabled"
            class="topRightButton"
            color="primary"
            v-bind="props"
          >
            Enter sender info
          </v-btn>
        </template>
        <v-card>
          <v-card-title>
            <div class="text-h5">
              Shipping Information
              <v-tooltip bottom>
                <template #activator="{ props }">
                  <v-icon
                    color="primary"
                    size="x-small"
                    v-bind="props"
                  >
                    mdi-information
                  </v-icon>
                </template>
                <span>Provide the address that the samples are being shipped from. </span>
              </v-tooltip>
            </div>
          </v-card-title>
          <v-card-text>
            <SubmissionForm
              ref="senderShippingInfoFormRef"
              @valid-state-changed="(state) => senderShippingInfoForm.validation = state"
            >
              <v-list-subheader>
                <span class="text-h6">Sender</span>
              </v-list-subheader>
              <v-divider />
              <!-- Shipper Name, E-mail address, etc. -->
              <div class="stack-sm mb-4">
                <v-text-field
                  v-model="senderShippingInfoForm.shipper.name"
                  :rules="requiredRules('Name is required', [])"
                  label="Sender Name *"
                  variant="outlined"
                  density="compact"
                  class="mt-2"
                />
                <v-text-field
                  v-model="senderShippingInfoForm.shipper.email"
                  :rules="requiredRules('E-mail is required', [
                    v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
                  ])"
                  label="E-mail Address *"
                  variant="outlined"
                  density="compact"
                />
                <v-text-field
                  v-model="senderShippingInfoForm.shipper.phone"
                  label="Phone Number"
                  variant="outlined"
                  density="compact"
                />
                <v-text-field
                  v-model="senderShippingInfoForm.shipper.line1"
                  label="Address Line 1"
                  variant="outlined"
                  density="compact"
                />
                <v-text-field
                  v-model="senderShippingInfoForm.shipper.line2"
                  label="Address Line 2"
                  variant="outlined"
                  density="compact"
                />
                <v-text-field
                  v-model="senderShippingInfoForm.shipper.city"
                  label="City"
                  variant="outlined"
                  density="compact"
                />
                <div class="d-flex">
                  <v-text-field
                    v-model="senderShippingInfoForm.shipper.state"
                    label="State"
                    variant="outlined"
                    density="compact"
                    class="mr-4"
                  />
                  <v-text-field
                    v-model="senderShippingInfoForm.shipper.postalCode"
                    label="Zip Code"
                    variant="outlined"
                    density="compact"
                    class="mr-4"
                  />
                  <v-text-field
                    v-model="senderShippingInfoForm.shipper.country"
                    :rules="requiredRules('Country is required', [])"
                    label="Country *"
                    variant="outlined"
                    density="compact"
                  />
                </div>
                <v-combobox
                  v-model="senderShippingInfoForm.shippingConditions"
                  :rules="requiredRules('Shipping conditions are required', [])"
                  label="Shipping Conditions *"
                  :items="shippingConditionsItems"
                  density="compact"
                  variant="outlined"
                />
                <v-menu
                  ref="datePickerEl"
                  v-model="datePicker"
                  :close-on-content-click="false"
                  transition="scale-transition"
                  offset-y
                  min-width="auto"
                >
                  <template #activator="{ props }">
                    <v-text-field
                      :model-value="formatShippingDate(expectedShippingDate)"
                      :rules="requiredRules('Expected Shipping Date is required', [])"
                      label="Expected Shipping Date *"
                      prepend-icon="mdi-calendar"
                      clearable
                      readonly
                      variant="outlined"
                      v-bind="props"
                      @click:clear="handleExpectedShippingDateClear"
                    />
                  </template>
                  <v-date-picker
                    v-model="expectedShippingDate"
                    no-title
                    scrollable
                    @update:model-value="datePicker = false"
                  />
                </v-menu>
              </div>

              <v-list-subheader>
                <span class="text-h6">Sample Type/Species</span>
              </v-list-subheader>
              <v-divider />
              <div class="stack-sm mb-4">
                <v-select
                  v-model="senderShippingInfoForm.sample"
                  class="mt-2"
                  :rules="requiredRules('Sample Type/Species is required', [])"
                  :items="sampleEnumValues"
                  label="Sample Type/Species *"
                  variant="outlined"
                  density="compact"
                />
                <v-textarea
                  v-model="senderShippingInfoForm.description"
                  label="Sample Description"
                  :rules="requiredRules('Sample Description is required', [])"
                  hint="Number of samples, sample container type..."
                  variant="outlined"
                  density="compact"
                  rows="2"
                />
                <v-textarea
                  v-model="senderShippingInfoForm.experimentalGoals"
                  :rules="requiredRules('Experiment Goals are required', [])"
                  label="Experiment Goals *"
                  hint="Briefly describe the goal for your experiment"
                  variant="outlined"
                  density="compact"
                  rows="2"
                />
                <v-textarea
                  v-model="senderShippingInfoForm.randomization"
                  label="Randomization"
                  hint="What experimental conditions will be used for"
                  variant="outlined"
                  density="compact"
                  rows="1"
                />
                <div class="d-flex">
                  <v-checkbox
                    v-model="senderShippingInfoForm.usdaRegulated"
                    class="mr-4 mt-0"
                    label="USDA Regulated?"
                    density="compact"
                  />
                  <v-text-field
                    v-model="senderShippingInfoForm.permitNumber"
                    label="Permit Number"
                    variant="outlined"
                    density="compact"
                  />
                  <v-spacer />
                </div>
                <div class="d-flex">
                  <v-select
                    v-model="senderShippingInfoForm.biosafetyLevel as BiosafetyLevels"
                    class="mr-4"
                    :items="biosafetyLevelValues"
                    label="Biosafety Level"
                    variant="outlined"
                    density="compact"
                  />
                  <v-checkbox
                    v-model="senderShippingInfoForm.irbOrHipaa"
                    class="mt-0"
                    label="IRB/HIPAA Compliance?"
                    density="compact"
                  />
                  <v-spacer />
                </div>
              </div>
              <v-list-subheader>
                <span class="text-h6">Additional Comments</span>
              </v-list-subheader>
              <v-divider class="mb-2" />
              <v-textarea
                v-model="senderShippingInfoForm.comments"
                label="Comments"
                variant="outlined"
                density="compact"
                lines="4"
              />
            </SubmissionForm>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              variant="elevated"
              @click="showSenderShippingInfoForm = false"
            >
              Save
            </v-btn>
            <v-spacer />
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-card>
  </div>
  <div
    v-if="!senderShippingInfoFormValid"
    class="text-red text-caption px-4 pt-1"
  >
    Sender's shipping information is required.
  </div>
</template>

<style scoped>
.topRightButton {
  position: absolute;
  top: 16px;
  right: 16px;
}
</style>
