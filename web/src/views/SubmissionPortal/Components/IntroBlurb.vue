<script lang="ts">
import {
  defineComponent,
} from '@vue/composition-api';

export default defineComponent({
  components: {},
  setup() {
    return {};
  },
});
</script>

<template>
  <v-container>
    <v-row>
      <v-col class="px-0">
        <h2 class="blue--text text-h6">
          Making it easy to follow standards
        </h2>
        <p class="text-justify mb-0 text-body-1">
          The Submission Portal is a flexible, template-driven tool designed to lower the barrier to collecting and reporting cohesive, standardized metadata about studies, samples, and assays. The standards we leverage include:
        </p>
      </v-col>
    </v-row>
    <v-row>
      <v-col class="px-0">
        <h2 class="blue--text text-h6">
          Supporting FAIR data
        </h2>
        <p class="text-justify mb-0 text-body-1">
          The Submission Portal leverages validation functions of the
          <a
            href="https://github.com/cidgoh/DataHarmonizer"
            target="_blank"
            title="View cidgoh/DataHarmonizer on GitHub"
          >DataHarmonizer</a>
          tool to check entered metadata values against the standards in the
          <a
            href="https://github.com/microbiomedata/nmdc-schema"
            target="_blank"
            title="View microbiomedata/nmdc-schema on GitHub"
          >NMDC schema</a>.
          By following existing community standards like the Minimum Information about any (x) Sequence (MIxS) standard from the Genomic Standards Consortium (GSC), the Submission Portal advances FAIR microbiome data.
        </p>
      </v-col>
    </v-row>
    <v-row>
      <v-col class="px-0">
        <h2 class="blue--text text-h6">
          Interoperability with DOE User Facilities
        </h2>
        <p class="text-justify mb-0 text-body-1">
          We collaborate closely with the JGI and EMSL to support integration of multi-omics data generated across these Facilities. The Submission Portal has been designed to be compliant with both JGI and EMSL sample submission requirements, ensuring study and biosample information is consistently collected to support interoperability and reuse.
        </p>
      </v-col>
    </v-row>
  </v-container>
</template>
