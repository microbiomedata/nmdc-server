<script lang="ts">
import { computed, defineComponent, ref, useTemplateRef, watch, } from 'vue';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';
import { BiosafetyLevels } from '@/views/SubmissionPortal/types';
import { addressForm, canEditSubmissionMetadata, validationState, } from '../store';
import { addressToString } from '../store/api';
import SubmissionContextShippingSummary from './SubmissionContextShippingSummary.vue';
import { ValidationResult } from 'vuetify/lib/composables/validation.mjs';
import { formatShippingDate } from '../utils';
import SubmissionForm from '@/views/SubmissionPortal/Components/SubmissionForm.vue';

export default defineComponent({
  components: { SubmissionForm, SubmissionContextShippingSummary },
  setup() {
    const addressFormRef = useTemplateRef<InstanceType<typeof SubmissionForm>>('addressFormRef');
    const addressFormValid = computed(() => validationState.senderShippingInfoForm?.length === 0);
    const showAddressForm = ref(false);
    const datePicker = ref(false);
    const sampleItems = ref(['water_extract_soil']);
    const sampleEnumValues = Object.keys(NmdcSchema.enums.SampleTypeEnum.permissible_values);
    const biosafetyLevelValues = Object.values(BiosafetyLevels);
    const shippingConditionsItems = [
      'Store frozen: transported within a cold chain and stored at -70°C to -80°C upon delivery.',
      'Store frozen: transported within a cold chain and stored at -20°C (4°F).',
      'Store Refrigerated: at 2°-8°C (36°-46°F): for heat sensitive products that must not be frozen.',
      'Room temperature: Store at 15°-25°C (59°-77°F).',
    ];

    const shipperSummary = computed(() => {
      let result = '';
      result += addressToString(addressForm.shipper);

      return result;
    });

    const addressSummary = computed(() => [{
      id: 'shipper',
      name: 'Shipper',
      children: [
        { id: 'shipperSummary', name: shipperSummary.value },
      ],
    }]);

    const expectedShippingDate = computed({
      get: () => {
        return addressForm.expectedShippingDate
          ? new Date(addressForm.expectedShippingDate)
          : undefined;
      },
      set: (newValue: Date | undefined) => {
        addressForm.expectedShippingDate = newValue ? newValue.toISOString() : undefined;
      },
    })

    function requiredRules(msg: string, otherRules: ((_v: string) => ValidationResult)[]) {
      return [
        (v: string) => !!v || msg,
        ...otherRules,
      ];
    }

    watch(showAddressForm, () => {
      addressFormRef.value?.validate();
    });

    function handleExpectedShippingDateClear() {
      expectedShippingDate.value = undefined;
    }

    return {
      addressFormRef,
      addressForm,
      addressFormValid,
      validationState,
      showAddressForm,
      datePicker,
      expectedShippingDate,
      sampleItems,
      biosafetyLevelValues,
      BiosafetyLevels,
      addressSummary,
      sampleEnumValues,
      shippingConditionsItems,
      canEditSubmissionMetadata,
      requiredRules,
      handleExpectedShippingDateClear,
      formatShippingDate,
    };
  },
});
</script>

<template>
  <div>
    <v-card
      class="mt-4 pa-0"
      variant="outlined"
      :style="addressFormValid ? '' : 'border: 2px solid red'"
    >
      <v-card-text
        class="pt-2"
        style="min-height: 100px;"
      >
        <span :class="{'error--text': !addressFormValid}">EMSL Shipping Info *</span>
        <p
          v-if="!addressFormValid"
          class="error--text"
        >
          Sender's shipping information is required
        </p>
        <submission-context-shipping-summary class="mt-6" />
      </v-card-text>
      <v-dialog
        v-model="showAddressForm"
        scrollable
        width="1200"
        eager
      >
        <template #activator="{ props }">
          <v-btn
            :disabled="!canEditSubmissionMetadata()"
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
              ref="addressFormRef"
              @valid-state-changed="(state) => validationState.senderShippingInfoForm = state"
            >
              <v-list-subheader>
                <span class="text-h6">Sender</span>
              </v-list-subheader>
              <v-divider />
              <!-- Shipper Name, E-mail address, etc. -->
              <div class="stack-sm mb-4">
                <v-text-field
                  v-model="addressForm.shipper.name"
                  :rules="requiredRules('Name is required', [])"
                  label="Sender Name *"
                  variant="outlined"
                  density="compact"
                  class="mt-2"
                />
                <v-text-field
                  v-model="addressForm.shipper.email"
                  :rules="requiredRules('E-mail is required', [
                    v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
                  ])"
                  label="E-mail Address *"
                  variant="outlined"
                  density="compact"
                />
                <v-text-field
                  v-model="addressForm.shipper.phone"
                  label="Phone Number"
                  variant="outlined"
                  density="compact"
                />
                <v-text-field
                  v-model="addressForm.shipper.line1"
                  label="Address Line 1"
                  variant="outlined"
                  density="compact"
                />
                <v-text-field
                  v-model="addressForm.shipper.line2"
                  label="Address Line 2"
                  variant="outlined"
                  density="compact"
                />
                <v-text-field
                  v-model="addressForm.shipper.city"
                  label="City"
                  variant="outlined"
                  density="compact"
                />
                <div class="d-flex">
                  <v-text-field
                    v-model="addressForm.shipper.state"
                    label="State"
                    variant="outlined"
                    density="compact"
                    class="mr-4"
                  />
                  <v-text-field
                    v-model="addressForm.shipper.postalCode"
                    label="Zip Code"
                    variant="outlined"
                    density="compact"
                    class="mr-4"
                  />
                  <v-text-field
                    v-model="addressForm.shipper.country"
                    :rules="requiredRules('Country is required', [])"
                    label="Country *"
                    variant="outlined"
                    density="compact"
                  />
                </div>
                <v-combobox
                  v-model="addressForm.shippingConditions"
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
                  v-model="addressForm.sample"
                  class="mt-2"
                  :rules="requiredRules('Sample Type/Species is required', [])"
                  :items="sampleEnumValues"
                  label="Sample Type/Species *"
                  variant="outlined"
                  density="compact"
                />
                <v-textarea
                  v-model="addressForm.description"
                  label="Sample Description"
                  :rules="requiredRules('Sample Description is required', [])"
                  hint="Number of samples, sample container type..."
                  variant="outlined"
                  density="compact"
                  rows="2"
                />
                <v-textarea
                  v-model="addressForm.experimentalGoals"
                  :rules="requiredRules('Experiment Goals are required', [])"
                  label="Experiment Goals *"
                  hint="Briefly describe the goal for your experiment"
                  variant="outlined"
                  density="compact"
                  rows="2"
                />
                <v-textarea
                  v-model="addressForm.randomization"
                  label="Randomization"
                  hint="What experimental conditions will be used for"
                  variant="outlined"
                  density="compact"
                  rows="1"
                />
                <div class="d-flex">
                  <v-checkbox
                    v-model="addressForm.usdaRegulated"
                    class="mr-4 mt-0"
                    label="USDA Regulated?"
                    density="compact"
                  />
                  <v-text-field
                    v-model="addressForm.permitNumber"
                    label="Permit Number"
                    variant="outlined"
                    density="compact"
                  />
                  <v-spacer />
                </div>
                <div class="d-flex">
                  <v-select
                    v-model="addressForm.biosafetyLevel as BiosafetyLevels"
                    class="mr-4"
                    :items="biosafetyLevelValues"
                    label="Biosafety Level"
                    variant="outlined"
                    density="compact"
                  />
                  <v-checkbox
                    v-model="addressForm.irbOrHipaa"
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
                v-model="addressForm.comments"
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
              @click="showAddressForm = false"
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
    v-if="!addressFormValid"
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
