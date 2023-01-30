<script lang="ts">
import { computed, defineComponent } from '@vue/composition-api';
import { addressForm } from '../store';
import { addressToString } from '../store/api';

export default defineComponent({
  setup() {
    const shipperAddressString = computed(() => addressToString(addressForm.shipper));
    const shipperSummary = computed(() => {
      let result = '';
      result += shipperAddressString.value;
      if (addressForm.shippingConditions) {
        result += `\nShipping Conditions: ${addressForm.shippingConditions}`;
      }
      if (addressForm.expectedShippingDate) {
        result += `\nExpected Shipping Date: ${addressForm.expectedShippingDate}`;
      }

      return result.trim();
    });

    return {
      shipperAddressString,
      shipperSummary,
    };
  },
});
</script>

<template>
  <v-expansion-panels
    accordion
    flat
  >
    <v-expansion-panel>
      <v-expansion-panel-header class="pl-0">
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
        <span
          style="white-space: pre-line;"
        >
          {{ shipperAddressString }}
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
        <span class="header">Institutional Review Board (IRB) Information</span>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <span
          style="white-space: pre-line;"
        >
          {{ shipperAddressString }}
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
          {{ shipperAddressString }}
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
</style>
