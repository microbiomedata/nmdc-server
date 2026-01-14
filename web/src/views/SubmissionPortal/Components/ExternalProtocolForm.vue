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
    <v-expansion-panel>
      <v-expansion-panel-title>
        <template #actions>
          <v-icon>
            mdi-chevron-down
          </v-icon>
        </template>
        <div>
          Sample Preparation Protocol
          <v-tooltip
            right
            class="x-2"
            max-width="500"
          >
            <template #activator="{ props }">
              <v-icon
                v-bind="props"
                class="ml-1 mb-1"
                small
              >
                mdi-help-circle
              </v-icon>
            </template>
            <span>
              This protocol should describe how samples were extracted, digested (including which proteolytic enzyme
              was used), and/or cleaned prior to analysis on an instrument. Provide a DOI, URL, or descriptive text.
            </span>
          </v-tooltip>
        </div>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-row
          no-gutters
        >
          <template
            v-if="protocolNames.length > 0 && !currentProtocol.sampleProtocol.name"
          >
            <v-checkbox
              v-model="currentProtocol.sampleProtocol.sharedData"
              label="Protocol shared across data types"
              class="mx-2"
              color="primary"
            >
              <template #append>
                <v-tooltip
                  right
                  class="x-2"
                  max-width="500"
                >
                  <template #activator="{ props }">
                    <v-icon
                      v-bind="props"
                    >
                      mdi-help-circle
                    </v-icon>
                  </template>
                  <span>
                    If a previously described protocol was also followed for these analyses, include the shared protocol name provided in the previous step.
                  </span>
                </v-tooltip>
              </template>
            </v-checkbox>
          </template>
          <template
            v-if="currentProtocol.sampleProtocol.sharedData && protocolNames.length > 0"
          >
            <v-col
              cols="1"
            />
            <v-col
              cols="4"
            >
              <v-select
                v-model="currentProtocol.sampleProtocol.sharedDataName"
                :items="protocolNames"
                label="Select Protocol Name"
                variant="outlined"
                class="mx-2"
                @change="updateMultiOmicsForm()"
              />
            </v-col>
          </template>
        </v-row>
        <template
          v-if="!currentProtocol.sampleProtocol.sharedData"
        >
          <v-row
            class="mx-8 "
            no-gutters
          >
            <v-col
              cols="5"
            >
              <v-text-field
                v-model="currentProtocol.sampleProtocol.doi"
                label="DOI"
                variant="outlined"
                :rules="doiValueRules()"
                @blur="updateMultiOmicsForm()"
              >
                <template #append>
                  <v-tooltip
                    right
                    class="x-2"
                    max-width="500"
                  >
                    <template #activator="{ props }">
                      <v-icon
                        v-bind="props"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a DOI for the protocol. This is a DOI for publicly available documentation that describes the experimental protocol in detail, not for the research study publication. Multiple DOIs can be provided.              </span>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
            <v-col
              cols="5"
              class="ml-4"
            >
              <v-text-field
                v-model="currentProtocol.sampleProtocol.url"
                label="URL"
                variant="outlined"
                :rules="urlValueRules()"
                @blur="updateMultiOmicsForm()"
              >
                <template #append>
                  <v-tooltip
                    right
                    class="x-2"
                    max-width="500"
                  >
                    <template #activator="{ props }">
                      <v-icon
                        v-bind="props"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a URL for the protocol. This is a URL for publicly available documentation that describes the experimental protocol in detail, not for the research study publication. Multiple URLs can be provided.
                    </span>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
          </v-row>
          <div
            class="v-label theme--light my-2 mx-8 d-flex align-center"
          >
            If a published protocol is unavailable, enter the sample preparation protocol(s) here.
          </div>
          <v-row
            class="mx-8"
            no-gutters
          >
            <v-col
              cols="5"
            >
              <v-text-field
                v-model="currentProtocol.sampleProtocol.name"
                label="Protocol Name"
                variant="outlined"
                @blur="updateMultiOmicsForm()"
              >
                <template #append>
                  <v-tooltip
                    right
                    max-width="500"
                  >
                    <template #activator="{ props }">
                      <v-icon
                        v-bind="props"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a name for this protocol. If this protocol is used for other data types, this name will be
                      used as reference.
                    </span>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
          </v-row>
          <v-row
            class="mx-8"
            no-gutters
          >
            <v-textarea
              v-model="currentProtocol.sampleProtocol.description"
              label="Protocol Description"
              variant="outlined"
              rows="3"
              @blur="updateMultiOmicsForm()"
            />
          </v-row>
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
    <v-expansion-panel>
      <v-expansion-panel-title>
        <div>
          Data Access
          <v-tooltip
            right
            class="x-2"
            max-width="500"
          >
            <template #activator="{ props }">
              <v-icon
                v-bind="props"
                class="ml-1 mb-1"
                small
              >
                mdi-help-circle
              </v-icon>
            </template>
            <span>
              Provide the location of the publicly available data. This can be a direct URL or a DOI.
            </span>
          </v-tooltip>
        </div>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <div>
          <v-row
            class="mx-8 "
            no-gutters
          >
            <v-col
              cols="5"
            >
              <v-text-field
                v-model="currentProtocol.dataProtocol.doi"
                label="DOI"
                variant="outlined"
                :rules="doiValueRules()"
                @blur="updateMultiOmicsForm()"
              >
                <template #append>
                  <v-tooltip
                    right
                    class="x-2"
                    max-width="500"
                  >
                    <template #activator="{ props }">
                      <v-icon
                        v-bind="props"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a DOI to raw instrument data.
                    </span>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
            <v-col
              cols="5"
              class="ml-4"
            >
              <v-text-field
                v-model="currentProtocol.dataProtocol.url"
                label="URL"
                variant="outlined"
                :rules="urlValueRules()"
                @blur="updateMultiOmicsForm()"
              >
                <template #append>
                  <v-tooltip
                    right
                    class="x-2"
                    max-width="500"
                  >
                    <template #activator="{ props }">
                      <v-icon
                        v-bind="props"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a URL to raw instrument data.
                    </span>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
          </v-row>
        </div>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>
