<script lang="ts">
import {
  computed,
  defineComponent,
  ref,
} from '@vue/composition-api';
import NmdcSchema from 'nmdc-schema/jsonschema/nmdc.schema.json';
import { addressForm, addressFormValid, BiosafetyLevels } from '../store';
import { addressToString } from '../store/api';
import SubmissionContextShippingSummary from './SubmissionContextShippingSummary.vue';

export default defineComponent({
  components: { SubmissionContextShippingSummary },
  setup() {
    const addressFormRef = ref();
    const showAddressForm = ref(false);
    const datePicker = ref(false);
    const sampleItems = ref(['water_extract_soil']);
    const sampleEnumValues = NmdcSchema.$defs.SampleTypeEnum.enum;
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

    return {
      addressFormRef,
      addressForm,
      addressFormValid,
      showAddressForm,
      datePicker,
      sampleItems,
      biosafetyLevelValues,
      BiosafetyLevels,
      addressSummary,
      sampleEnumValues,
      shippingConditionsItems,
    };
  },
});
</script>

<template>
  <v-card
    class="mt-4 pa-0"
    outlined
  >
    <v-card-text
      class="pt-2"
      style="min-height: 100px;"
    >
      <span>EMSL Shipping Info</span>
      <submission-context-shipping-summary
        class="mt-6"
      />
    </v-card-text>
    <v-dialog
      v-model="showAddressForm"
      scrollable
      width="1200"
    >
      <template
        #activator="{ on, attrs }"
      >
        <v-btn
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
            class="ml-12"
            style="max-width: 1000px"
          >
            <v-subheader>
              <span class="text-h6">Shipper</span>
            </v-subheader>
            <v-divider />
            <!-- Shipper Name, E-mail address, etc. -->
            <v-text-field
              v-model="addressForm.shipper.name"
              label="Shipper Name"
              outlined
              dense
              class="mt-2"
            />
            <v-text-field
              v-model="addressForm.shipper.email"
              label="E-mail Address"
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
              label="Address Line 1"
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
              label="City"
              outlined
              dense
            />
            <div class="d-flex">
              <v-text-field
                v-model="addressForm.shipper.state"
                label="State"
                outlined
                dense
                class="mr-4"
              />
              <v-text-field
                v-model="addressForm.shipper.postalCode"
                label="Zip Code"
                outlined
                dense
              />
            </div>
            <v-combobox
              v-model="addressForm.shippingConditions"
              label="Shipping Conditions"
              :items="shippingConditionsItems"
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
                  v-model="addressForm.expectedShippingDate"
                  label="Expected Shipping Date"
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
                v-model="addressForm.expectedShippingDate"
                no-title
                scrollable
                @input="datePicker = false"
              />
            </v-menu>
            <v-subheader>
              <span class="text-h6">Sample type/Species</span>
            </v-subheader>
            <v-divider />
            <v-select
              v-model="addressForm.sample"
              class="mt-2"
              :items="sampleEnumValues"
              label="Sample type/Species"
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
                class="mr-4"
                :items="biosafetyLevelValues"
                label="Biosafety Level"
                dense
                outlined
              />
              <v-checkbox
                v-model="addressForm.irpOrHippa"
                class="mt-0"
                label="IRP/HIPAA?"
              />
              <v-spacer />
            </div>
            <div v-if="addressForm.biosafetyLevel === BiosafetyLevels.BSL2">
              <v-subheader>
                <span class="text-h6">Institutional Review Board (IRB) Information</span>
              </v-subheader>
              <v-divider class="mb-2" />
              <v-text-field
                v-model="addressForm.irbNumber"
                label="IRB Number"
                outlined
                dense
              />
              <v-text-field
                v-model="addressForm.irbAddress.name"
                label="IRB Contact Name"
                outlined
                dense
              />
              <v-text-field
                v-model="addressForm.irbAddress.email"
                label="E-mail Address"
                outlined
                dense
              />
              <v-text-field
                v-model="addressForm.irbAddress.phone"
                label="Phone Number"
                outlined
                dense
              />
              <v-text-field
                v-model="addressForm.irbAddress.line1"
                label="Address Line 1"
                outlined
                dense
              />
              <v-text-field
                v-model="addressForm.irbAddress.line2"
                label="Address Line 2"
                outlined
                dense
              />
              <v-text-field
                v-model="addressForm.irbAddress.city"
                label="City"
                outlined
                dense
              />
              <div class="d-flex">
                <v-text-field
                  v-model="addressForm.irbAddress.state"
                  label="State"
                  outlined
                  dense
                  class="mr-4"
                />
                <v-text-field
                  v-model="addressForm.irbAddress.postalCode"
                  label="Zip Code"
                  outlined
                  dense
                />
              </div>
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
