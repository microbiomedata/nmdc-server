<script lang="ts">
import { computed, defineComponent } from 'vue';
import { senderShippingInfoForm } from '../store';
import { addressToString } from '../store/api';
import { formatShippingDate } from '../utils';

export default defineComponent({
  setup() {
    const shipperAddressOneLiner = computed(() => {
      const shipperData = [
        senderShippingInfoForm.shipper.name,
        senderShippingInfoForm.shipper.line1,
        senderShippingInfoForm.shipper.line2,
        senderShippingInfoForm.shipper.city,
        senderShippingInfoForm.shipper.state,
        senderShippingInfoForm.shipper.postalCode,
        senderShippingInfoForm.shipper.country,
      ];
      const existingShipperData = shipperData.filter((shipperDatum) => !!shipperDatum.trim());
      return existingShipperData.join(', ');
    });

    const shipperAddressString = computed(() => addressToString(senderShippingInfoForm.shipper));
    const shipperSummary = computed(() => {
      let result = '';
      result += shipperAddressString.value.trim();
      if (senderShippingInfoForm.shippingConditions) {
        result += `\nShipping Conditions: ${senderShippingInfoForm.shippingConditions}`;
      }
      if (senderShippingInfoForm.expectedShippingDate) {
        const date = new Date(senderShippingInfoForm.expectedShippingDate);
        result += `\nExpected Shipping Date: ${formatShippingDate(date)}`;
      }

      return result.trim();
    });

    const sampleProperties = computed(() => [
      {
        title: 'Sample Name',
        value: senderShippingInfoForm.sample,
      },
      {
        title: 'Sample Description',
        value: senderShippingInfoForm.description,
      },
      {
        title: 'Experiment Goals',
        value: senderShippingInfoForm.experimentalGoals,
      },
      {
        title: 'Randomization',
        value: senderShippingInfoForm.randomization,
      },
      {
        title: 'USDA Regulated',
        value: senderShippingInfoForm.usdaRegulated,
      },
      {
        title: 'Permit Number',
        value: senderShippingInfoForm.permitNumber,
      },
      {
        title: 'Biosafety Level',
        value: senderShippingInfoForm.biosafetyLevel,
      },
      {
        title: 'IRB/HIPAA Compliance?',
        value: (senderShippingInfoForm.irbOrHipaa ? 'Yes' : 'No'),
      },
    ]);

    return {
      shipperAddressOneLiner,
      shipperSummary,
      senderShippingInfoForm,
      sampleProperties,
      formatShippingDate,
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
          {{ senderShippingInfoForm.comments }}
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
