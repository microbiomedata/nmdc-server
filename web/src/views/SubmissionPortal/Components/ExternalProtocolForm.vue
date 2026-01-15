<script lang="ts">
import { defineComponent, computed, ref } from 'vue';
import { multiOmicsForm, checkDoiFormat } from '../store';

export default defineComponent({
  name: 'ExternalProtocolForm',
  props: {
    dataType: {
      type: String as () => 'mpProtocols' | 'mbProtocols' | 'nomProtocols' | 'lipProtocols',
      required: true,
    },
  },
  setup(props) {
    const protocolNames = computed(() => {
      const names = new Set<string>();
      if (multiOmicsForm.mpProtocols?.sampleProtocol.name) {
        names.add(multiOmicsForm.mpProtocols.sampleProtocol.name);
      }
      if (multiOmicsForm.mbProtocols?.sampleProtocol.name) {
        names.add(multiOmicsForm.mbProtocols.sampleProtocol.name);
      }
      if (multiOmicsForm.nomProtocols?.sampleProtocol.name) {
        names.add(multiOmicsForm.nomProtocols.sampleProtocol.name);
      }
      if (multiOmicsForm.lipProtocols?.sampleProtocol.name) {
        names.add(multiOmicsForm.lipProtocols.sampleProtocol.name);
      }
      return Array.from(names);
    });

    const existingProtocols = computed(() => (multiOmicsForm as Record<'mpProtocols' | 'mbProtocols' | 'nomProtocols' | 'lipProtocols', any>)[props.dataType]);

    const currentProtocol = ref({
      sampleProtocol: {
        name: existingProtocols.value?.sampleProtocol.name || '',
        description: existingProtocols.value?.sampleProtocol.description || '',
        doi: existingProtocols.value?.sampleProtocol.doi || '',
        url: existingProtocols.value?.sampleProtocol.url || '',
        sharedData: existingProtocols.value?.sampleProtocol.sharedData || false,
        sharedDataName: existingProtocols.value?.sampleProtocol.sharedDataName || '',
      },
      acquisitionProtocol: {
        doi: existingProtocols.value?.acquisitionProtocol.doi || '',
        url: existingProtocols.value?.acquisitionProtocol.url || '',
        name: existingProtocols.value?.acquisitionProtocol.name || '',
        description: existingProtocols.value?.acquisitionProtocol.description || '',
      },
      dataProtocol: {
        doi: existingProtocols.value?.dataProtocol.doi || '',
        url: existingProtocols.value?.dataProtocol.url || '',
      },
    });

    function updateMultiOmicsForm() {
      (multiOmicsForm as Record<'mpProtocols' | 'mbProtocols' | 'nomProtocols' | 'lipProtocols', any>)[props.dataType] = currentProtocol.value;
    }

    const doiValueRules = () => (
      [
        (value: string) => {
          if (!value) return true;

          // Split by comma and validate each DOI
          const dois = value.split(',').map((doi) => doi.trim());
          const allValid = dois.every((doi) => checkDoiFormat(doi));

          return allValid || 'All DOIs must be valid (comma-separated if multiple)';
        },
      ]
    );

    const urlValueRules = () => (
      [
        (value: string) => {
          if (!value) return true;

          // Split by comma and validate each URL
          const urls = value.split(',').map((url) => url.trim());
          const urlRegex = /^https?:\/\//i;
          const allValid = urls.every((url) => urlRegex.test(url));

          return allValid || 'All URLs must be valid (comma-separated if multiple)';
        },
      ]
    );

    return {
      currentProtocol,
      multiOmicsForm,
      protocolNames,
      doiValueRules,
      urlValueRules,
      updateMultiOmicsForm,
    };
  },
});
</script>

<template>
  <v-expansion-panels
    class="mx-8"
    flat
    multiple
  >
    <v-expansion-panel title="Sample Preparation Protocol">
      <v-expansion-panel-text class="text-body-2 px-8">
        <div class="mb-4">
          Use these fields to describe how samples were extracted, digested (including which proteolytic enzyme was
          used), and/or cleaned prior to analysis on an instrument.
        </div>
        <v-checkbox
          v-if="protocolNames.length > 0 && !currentProtocol.sampleProtocol.name"
          v-model="currentProtocol.sampleProtocol.sharedData"
        >
          <template #label>
            <div>
              <div>Use protocol described for other data types</div>
              <div class="text-caption">
                Select this option to reuse a protocol name already provided for another data type in this submission.
              </div>
            </div>
          </template>
        </v-checkbox>
        <v-select
          v-if="currentProtocol.sampleProtocol.sharedData && protocolNames.length > 0"
          v-model="currentProtocol.sampleProtocol.sharedDataName"
          :items="protocolNames"
          label="Select Protocol Name"
          variant="outlined"
          @change="updateMultiOmicsForm()"
        />
        <template v-if="!currentProtocol.sampleProtocol.sharedData">
          <div class="mb-2">
            <b>If a published protocol is available</b>, provide the DOI or URL here. The DOI or URL should link to publicly available documentation that describes the experimental protocol in detail, not for the research study publication.
          </div>
          <v-row class="mb-4">
            <v-col>
              <v-text-field
                v-model="currentProtocol.sampleProtocol.doi"
                label="DOI"
                variant="outlined"
                :rules="doiValueRules()"
                persistent-hint
                hint="A DOI for the protocol"
                @blur="updateMultiOmicsForm()"
              />
            </v-col>
            <v-col>
              <v-text-field
                v-model="currentProtocol.sampleProtocol.url"
                label="URL"
                variant="outlined"
                :rules="urlValueRules()"
                persistent-hint
                hint="A URL for the protocol"
                @blur="updateMultiOmicsForm()"
              />
            </v-col>
          </v-row>
          <div class="mb-2">
            <b>If a published protocol is unavailable</b>, enter the data acquisition protocol here.
          </div>
          <v-text-field
            v-model="currentProtocol.sampleProtocol.name"
            label="Protocol Name"
            class="mb-4"
            variant="outlined"
            hint="If this protocol is used for other data types, this name will be used as reference."
            persistent-hint
            @blur="updateMultiOmicsForm()"
          />
          <v-textarea
            v-model="currentProtocol.sampleProtocol.description"
            label="Protocol Description"
            variant="outlined"
            rows="3"
            @blur="updateMultiOmicsForm()"
          />
        </template>
      </v-expansion-panel-text>
    </v-expansion-panel>

    <v-expansion-panel title="Data Acquisition Protocol">
      <v-expansion-panel-text class="text-body-2 px-8">
        <div class="mb-4">
          Use these fields to describe the chromatography and mass spectrometry methods used for data acquisition.
        </div>
        <div class="mb-2">
          <b>If a published protocol is available</b>, provide the DOI or URL here. The DOI or URL should link to publicly available documentation that describes the experimental protocol in detail, not for the research study publication.
        </div>
        <v-row class="mb-4">
          <v-col>
            <v-text-field
              v-model="currentProtocol.acquisitionProtocol.doi"
              label="DOI"
              variant="outlined"
              :rules="doiValueRules()"
              persistent-hint
              hint="A DOI for the protocol"
              @blur="updateMultiOmicsForm()"
            />
          </v-col>
          <v-col>
            <v-text-field
              v-model="currentProtocol.acquisitionProtocol.url"
              label="URL"
              variant="outlined"
              :rules="urlValueRules()"
              persistent-hint
              hint="A URL for the protocol"
              @blur="updateMultiOmicsForm()"
            />
          </v-col>
        </v-row>
        <div class="mb-2">
          <b>If a published protocol is unavailable</b>, enter the data acquisition protocol here.
        </div>
        <v-text-field
          v-model="currentProtocol.acquisitionProtocol.name"
          label="Protocol Name"
          variant="outlined"
          @blur="updateMultiOmicsForm()"
        />
        <v-textarea
          v-model="currentProtocol.acquisitionProtocol.description"
          label="Protocol Description"
          variant="outlined"
          hide-details="auto"
          rows="3"
          @blur="updateMultiOmicsForm()"
        />
      </v-expansion-panel-text>
    </v-expansion-panel>

    <v-expansion-panel title="Data Access">
      <v-expansion-panel-text class="text-body-2 px-8">
        <div class="mb-2">
          Use these fields to provide the location of the publicly available data. The DOI or URL should link to raw instrument data in a public repository.
        </div>
        <v-row class="mb-4">
          <v-col>
            <v-text-field
              v-model="currentProtocol.dataProtocol.doi"
              label="DOI"
              variant="outlined"
              :rules="doiValueRules()"
              @blur="updateMultiOmicsForm()"
            />
          </v-col>
          <v-col>
            <v-text-field
              v-model="currentProtocol.dataProtocol.url"
              label="URL"
              variant="outlined"
              :rules="urlValueRules()"
              @blur="updateMultiOmicsForm()"
            />
          </v-col>
        </v-row>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>
