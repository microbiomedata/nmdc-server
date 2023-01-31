<script lang="ts">
import { computed, defineComponent } from '@vue/composition-api';
import { addressForm } from '../store';
import { addressToString } from '../store/api';

export default defineComponent({
  setup() {
    const shipperAddressString = computed(() => addressToString(addressForm.shipper));
    const shipperSummary = computed(() => {
      let result = '';
      result += shipperAddressString.value.trim();
      if (addressForm.shippingConditions) {
        result += `\nShipping Conditions: ${addressForm.shippingConditions}`;
      }
      if (addressForm.expectedShippingDate) {
        result += `\nExpected Shipping Date: ${addressForm.expectedShippingDate}`;
      }

      return result.trim();
    });

    const irbAddressString = computed(() => addressToString(addressForm.irbAddress));
    const irbSummary = computed(() => {
      let result = '';
      if (addressForm.irbNumber) {
        result += `${addressForm.irbNumber}\n`;
      }
      result += irbAddressString.value.trim();
      return result;
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
        title: 'IRP/HIPAA',
        value: addressForm.irpOrHipaa,
      },
    ]);

    return {
      shipperSummary,
      addressForm,
      irbSummary,
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
        <span class="header">Shipper</span>
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
        <span class="header">Institutional Review Board (IRB) Information</span>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <span
          style="white-space: pre-line;"
        >
          {{ irbSummary }}
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
}

.label {
  display: inline-block;
  width: 150px;
  text-align: right;
}
</style>
