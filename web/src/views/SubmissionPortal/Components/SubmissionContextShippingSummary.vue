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
    <v-expansion-panel>
      <v-expansion-panel-header class="pa-0 ma-0">
        <template #actions>
          <v-icon class="icon">
            $expand
          </v-icon>
        </template>
        <div class="header">
          <span class="mr-2">Shipper</span>
          <span class="expansion-panel-preview">{{ shipperAddressOneLiner }}</span>
        </div>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <span
          style="white-space: pre-line;"
        >
          {{ shipperSummary }}
        </span>
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel>
      <v-expansion-panel-header class="pl-0">
        <template #actions>
          <v-icon class="icon">
            $expand
          </v-icon>
        </template>
        <span class="header">Sample</span>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
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
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel>
      <v-expansion-panel-header class="pl-0">
        <template #actions>
          <v-icon class="icon">
            $expand
          </v-icon>
        </template>
        <span class="header">Additional Comments</span>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <span
          style="white-space: pre-line;"
        >
          {{ addressForm.comments }}
        </span>
      </v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<style scoped>
.icon {
  order: 0;
}

.header {
  order: 1;
  justify-content: flex-start;
}

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
