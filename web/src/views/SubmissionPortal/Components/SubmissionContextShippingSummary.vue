<script lang="ts">
import { computed, defineComponent } from '@vue/composition-api';
import { addressForm } from '../store';
import { addressToString } from '../store/api';

export default defineComponent({
  setup() {
    const shipperAddressOneLiner = computed(() => {
      const shipperData = [
        addressForm.shipper.name,
        addressForm.shipper.line1,
        addressForm.shipper.line2,
        addressForm.shipper.city,
        addressForm.shipper.state,
        addressForm.shipper.postalCode,
        addressForm.shipper.country,
      ];
      const existingShipperData = shipperData.filter((shipperDatum) => !!shipperDatum.trim());
      return existingShipperData.join(', ');
    });
    const shipperAddressString = computed(() => addressToString(addressForm.shipper));
    const shipperSummary = computed(() => {
      let result = '';
      result += shipperAddressString.value.trim();
      if (addressForm.shippingConditions) {
        result += `\nShipping Conditions: ${addressForm.shippingConditions}`;
      }
      if (addressForm.expectedShippingDate) {
        const date = new Date(addressForm.expectedShippingDate);
        result += `\nExpected Shipping Date: ${date.toLocaleDateString()}`;
      }

      return result.trim();
    });

    const sampleProperties = computed(() => [
      {
        title: 'Sample Name',
        value: addressForm.sample,
      },
      {
        title: 'Sample Description',
        value: addressForm.description,
      },
      {
        title: 'Experiment Goals',
        value: addressForm.experimentalGoals,
      },
      {
        title: 'Randomization',
        value: addressForm.randomization,
      },
      {
        title: 'USDA Regulated',
        value: addressForm.usdaRegulated,
      },
      {
        title: 'Permit Number',
        value: addressForm.permitNumber,
      },
      {
        title: 'Biosafety Level',
        value: addressForm.biosafetyLevel,
      },
      {
        title: 'IRB/HIPAA Compliance?',
        value: (addressForm.irbOrHipaa ? 'Yes' : 'No'),
      },
    ]);

    return {
      shipperAddressOneLiner,
      shipperSummary,
      addressForm,
      sampleProperties,
    };
  },
});
</script>

<template>
  <v-expansion-panels
    accordion
    flat
    multiple
  >
    <v-expansion-panel hide-actions>
      <v-expansion-panel-title class="pl-2">
        <template #default="{ expanded, expandIcon, collapseIcon }">
          <div>
            <v-icon>{{ expanded ? collapseIcon : expandIcon }}</v-icon>
            <span class="mr-2">Sender</span>
            <span class="expansion-panel-preview">{{ shipperAddressOneLiner }}</span>
          </div>
        </template>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <span
          style="white-space: pre-line;"
        >
          {{ shipperSummary }}
        </span>
      </v-expansion-panel-text>
    </v-expansion-panel>

    <v-expansion-panel hide-actions>
      <v-expansion-panel-title class="pl-2">
        <template #default="{ expanded, expandIcon, collapseIcon }">
          <div>
            <v-icon>{{ expanded ? collapseIcon : expandIcon }}</v-icon>
            Sample
          </div>
        </template>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <div
          style="white-space: pre-line;"
        >
          <span
            v-for="sampleProp in sampleProperties"
            :key="sampleProp.title"
          >
            <p
              v-if="sampleProp.value"
              class="mb-0"
            >
              <strong class="label">{{ sampleProp.title }}:</strong> {{ sampleProp.value }}
            </p>
          </span>
        </div>
      </v-expansion-panel-text>
    </v-expansion-panel>

    <v-expansion-panel hide-actions>
      <v-expansion-panel-title class="pl-2">
        <template #default="{ expanded, expandIcon, collapseIcon }">
          <div>
            <v-icon>{{ expanded ? collapseIcon : expandIcon }}</v-icon>
            Additional Comments
          </div>
        </template>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <span
          style="white-space: pre-line;"
        >
          {{ addressForm.comments }}
        </span>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<style scoped>
.expansion-panel-preview {
  color: gray;
  font-style: italic;
}

.label {
  display: inline-block;
  width: 150px;
  text-align: right;
}
</style>
