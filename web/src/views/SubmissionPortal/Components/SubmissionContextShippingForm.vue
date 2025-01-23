<script lang="ts">
import {
  computed,
  defineComponent,
  nextTick,
  onMounted,
  ref,
  watch,
} from '@vue/composition-api';
// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';
import {
  addressForm,
  addressFormValid,
  canEditSubmissionMetadata,
} from '../store';
import { BiosafetyLevels } from '@/views/SubmissionPortal/types';
import { addressToString } from '../store/api';
import SubmissionContextShippingSummary from './SubmissionContextShippingSummary.vue';

export default defineComponent({
  components: { SubmissionContextShippingSummary },
  setup() {
    const addressFormRef = ref();
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

    const reformatDate = (dateString: string | Date) => new Date(dateString).toISOString().substring(0, 10);

    const expectedShippingDateString = ref('');

    watch(expectedShippingDateString, (newValue: string) => {
      addressForm.expectedShippingDate = newValue.length ? new Date(newValue) : undefined;
    });

    function requiredRules(msg: string, otherRules: ((v: string) => unknown)[]) {
      return [
        (v: string) => !!v || msg,
        ...otherRules,
      ];
    }

    watch(showAddressForm, () => {
      nextTick(() => addressFormRef.value.validate());
    });

    onMounted(() => {
      expectedShippingDateString.value = addressForm.expectedShippingDate
        ? reformatDate(addressForm.expectedShippingDate)
        : '';
    });

    return {
      addressFormRef,
      addressForm,
      addressFormValid,
      showAddressForm,
      datePicker,
      expectedShippingDateString,
      sampleItems,
      biosafetyLevelValues,
      BiosafetyLevels,
      addressSummary,
      sampleEnumValues,
      shippingConditionsItems,
      canEditSubmissionMetadata,
      requiredRules,
    };
  },
});
</script>

<template>
  <v-card
    class="mt-4 pa-0"
    outlined
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
        Shipping information is required
      </p>
      <submission-context-shipping-summary
        class="mt-6"
      />
    </v-card-text>
    <v-dialog
      v-model="showAddressForm"
      scrollable
      width="1200"
      eager
    >
      <template
        #activator="{ on, attrs }"
      >
        <v-btn
          :disabled="!canEditSubmissionMetadata()"
          absolute
          top
          right
          color="primary"
          v-bind="attrs"
          v-on="on"
        >
          Enter shipping info
        </v-btn>
      </template>
      <v-card>
        <v-card-title>
          <v-spacer />
          <span class="text-h5">Shipping Information</span>
          <v-spacer />
        </v-card-title>
        <v-card-text>
          <v-form
            ref="addressFormRef"
            v-model="addressFormValid"
            class="ml-12"
            style="max-width: 1000px"
            :disabled="!canEditSubmissionMetadata()"
          >
            <v-subheader>
              <span class="text-h6">Shipper</span>
            </v-subheader>
            <v-divider />
            <!-- Shipper Name, E-mail address, etc. -->
            <v-text-field
              v-model="addressForm.shipper.name"
              :rules="requiredRules('Name is required', [])"
              label="Shipper Name *"
              outlined
              dense
              class="mt-2"
            />
            <v-text-field
              v-model="addressForm.shipper.email"
              :rules="requiredRules('E-mail is required', [
                v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
              ])"
              label="E-mail Address *"
              outlined
              dense
            />
            <v-text-field
              v-model="addressForm.shipper.phone"
              label="Phone Number"
              outlined
              dense
            />
            <v-text-field
              v-model="addressForm.shipper.line1"
              :rules="requiredRules('Address Line 1 is required', [])"
              label="Address Line 1 *"
              outlined
              dense
            />
            <v-text-field
              v-model="addressForm.shipper.line2"
              label="Address Line 2"
              outlined
              dense
            />
            <v-text-field
              v-model="addressForm.shipper.city"
              :rules="requiredRules('City is required', [])"
              label="City *"
              outlined
              dense
            />
            <div class="d-flex">
              <v-text-field
                v-model="addressForm.shipper.state"
                :rules="requiredRules('State is required', [])"
                label="State *"
                outlined
                dense
                class="mr-4"
              />
              <v-text-field
                v-model="addressForm.shipper.postalCode"
                :rules="requiredRules('Zip code is required', [])"
                label="Zip Code *"
                outlined
                dense
              />
            </div>
            <v-combobox
              v-model="addressForm.shippingConditions"
              label="Shipping Conditions *"
              :items="shippingConditionsItems"
              :rules="requiredRules('Shipping conditions are required', [])"
              outlined
              dense
            />
            <v-menu
              ref="datePickerEl"
              v-model="datePicker"
              :close-on-content-click="false"
              transition="scale-transition"
              offset-y
              min-width="auto"
            >
              <template #activator="{ on, attrs }">
                <v-text-field
                  v-model="expectedShippingDateString"
                  :rules="requiredRules('Expected Shipping Date is required', [])"
                  label="Expected Shipping Date *"
                  prepend-icon="mdi-calendar"
                  clearable
                  readonly
                  outlined
                  dense
                  v-bind="attrs"
                  v-on="on"
                  @click.clear="addressForm.expectedShippingDate = undefined"
                />
              </template>
              <v-date-picker
                v-model="expectedShippingDateString"
                no-title
                scrollable
                @input="datePicker = false"
              />
            </v-menu>
            <v-subheader>
              <span class="text-h6">Sample Type/Species</span>
            </v-subheader>
            <v-divider />
            <v-select
              v-model="addressForm.sample"
              :rules="requiredRules('Sample Type/Species is required', [])"
              class="mt-2"
              :items="sampleEnumValues"
              label="Sample Type/Species"
              dense
              outlined
            />
            <v-textarea
              v-model="addressForm.description"
              label="Sample Description"
              hint="Number of samples, sample container type..."
              outlined
              dense
              rows="2"
            />
            <v-textarea
              v-model="addressForm.experimentalGoals"
              label="Experiment Goals"
              :rules="requiredRules('Experiment Goals are required', [])"
              hint="Briefly describe the goal for your experiment"
              outlined
              dense
              rows="2"
            />
            <v-textarea
              v-model="addressForm.randomization"
              label="Randomization"
              hint="What experimental conditions will be used for"
              outlined
              dense
              rows="1"
            />
            <div class="d-flex">
              <v-checkbox
                v-model="addressForm.usdaRegulated"
                class="mr-4 mt-0"
                label="USDA Regulated?"
                hide-details
              />
              <v-text-field
                v-model="addressForm.permitNumber"
                label="Permit Number"
                outlined
                dense
              />
              <v-spacer />
            </div>
            <div class="d-flex">
              <v-select
                v-model="addressForm.biosafetyLevel"
                :rules="requiredRules('Biosafety level is required', [])"
                class="mr-4"
                :items="biosafetyLevelValues"
                label="Biosafety Level *"
                dense
                outlined
              />
              <v-checkbox
                v-model="addressForm.irbOrHipaa"
                class="mt-0"
                label="IRB/HIPAA Compliance?"
              />
              <v-spacer />
            </div>
            <v-subheader>
              <span class="text-h6">Additional Comments</span>
            </v-subheader>
            <v-divider class="mb-2" />
            <v-textarea
              v-model="addressForm.comments"
              label="Comments"
              outlined
              dense
              lines="4"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="primary"
            @click="showAddressForm = false"
          >
            Save
          </v-btn>
          <v-spacer />
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>
