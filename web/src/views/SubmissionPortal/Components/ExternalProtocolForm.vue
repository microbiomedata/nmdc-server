<script lang="ts">
import { defineComponent, computed, ref } from '@vue/composition-api';
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

    const currentProtocol = ref({
      name: '',
      description: '',
      doi: '',
      url: '',
      sharedData: false,
      sharedDataName: '',
    });

    function updateMultiOmicsForm(protocolType: string) {
      (multiOmicsForm as Record<'mpProtocols' | 'mbProtocols' | 'nomProtocols' | 'lipProtocols', any>)[props.dataType][protocolType] = currentProtocol.value;
    }

    const doiValueRules = () => (
      [
        (value: string) => {
          if (!value) return true;

          const isValidDoi = checkDoiFormat(value);

          return isValidDoi || 'Must be a valid DOI';
        },
      ]
    );

    const urlValueRules = () => (
      [
        (value: string) => {
          if (!value) return true;

          const urlRegex = /^https?:\/\//i;
          const isValidUrl = urlRegex.test(value);

          return isValidUrl || 'Must be a valid URL';
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
      <v-expansion-panel-header>
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
            <template #activator="{ on, attrs }">
              <v-icon
                v-bind="attrs"
                class="ml-1 mb-1"
                small
                v-on="on"
              >
                mdi-help-circle
              </v-icon>
            </template>
            <span>
              For samples with metaproteomics data, this protocol should describe how those samples were extracted, digested (including which proteolytic enzyme was used), and/or cleaned prior to analysis on an instrument.
            </span>
          </v-tooltip>
        </div>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <v-row
          no-gutters
        >
          <template
            v-if="protocolNames.length > 0 && multiOmicsForm[`${dataType}`].sampleProtocol.name === ''"
          >
            <v-checkbox
              v-model="multiOmicsForm[`${dataType}`].sampleProtocol.sharedData"
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
                  <template #activator="{ on, attrs }">
                    <v-icon
                      v-bind="attrs"
                      dense
                      v-on="on"
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
            v-if="multiOmicsForm[`${dataType}`].sampleProtocol.sharedData && protocolNames.length > 0"
          >
            <v-col
              cols="1"
            />
            <v-col
              cols="4"
            >
              <v-select
                v-model="currentProtocol.sharedDataName"
                :items="protocolNames"
                label="Select Protocol Name"
                outlined
                dense
                class="mx-2"
                @change="updateMultiOmicsForm('sampleProtocol')"
              />
            </v-col>
          </template>
        </v-row>
        <template
          v-if="!multiOmicsForm[`${dataType}`].sampleProtocol.sharedData"
        >
          <v-row
            class="mx-8 "
            no-gutters
          >
            <v-col
              cols="5"
            >
              <v-text-field
                v-model="currentProtocol.doi"
                label="DOI"
                outlined
                dense
                :rules="doiValueRules()"
                @blur="updateMultiOmicsForm('sampleProtocol')"
              >
                <template #append-outer>
                  <v-tooltip
                    right
                    class="x-2"
                    max-width="500"
                  >
                    <template #activator="{ on, attrs }">
                      <v-icon
                        v-bind="attrs"
                        dense
                        v-on="on"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a DOI for the protocol. This is not for the study publication, but a public protocol that explains the protocol in detail. Multiple DOIs can be provided.              </span>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
            <v-col
              cols="5"
            >
              <v-text-field
                v-model="currentProtocol.url"
                label="URL"
                outlined
                dense
                :rules="urlValueRules()"
                @blur="updateMultiOmicsForm('sampleProtocol')"
              >
                <template #append-outer>
                  <v-tooltip
                    right
                    class="x-2"
                    max-width="500"
                  >
                    <template #activator="{ on, attrs }">
                      <v-icon
                        v-bind="attrs"
                        dense
                        v-on="on"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a URL for the protocol. This is not for the study publication, but a public protocol that explains the protocol in detail. Multiple URLs can be provided.
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
                v-model="currentProtocol.name"
                label="Protocol Name"
                outlined
                dense
                @blur="updateMultiOmicsForm('sampleProtocol')"
              >
                <template #append-outer>
                  <v-tooltip
                    right
                    max-width="500"
                  >
                    <template #activator="{ on, attrs }">
                      <v-icon
                        v-bind="attrs"
                        dense
                        v-on="on"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a name for this protocol. If multiple protocols are used, this name will be required for later steps.
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
              v-model="currentProtocol.description"
              label="Protocol Description"
              outlined
              dense
              rows="3"
              @blur="updateMultiOmicsForm('sampleProtocol')"
            />
          </v-row>
        </template>
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel>
      <v-expansion-panel-header>
        <div>
          Data Acquisition Protocol
          <v-tooltip
            right
            class="x-2"
            max-width="500"
          >
            <template #activator="{ on, attrs }">
              <v-icon
                v-bind="attrs"
                class="ml-1 mb-1"
                small
                v-on="on"
              >
                mdi-help-circle
              </v-icon>
            </template>
            <span>
              This protocol should describe the chromatography and mass spectrometry methods used for data acquisition.
            </span>
          </v-tooltip>
        </div>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <v-row
          class="mx-8 "
          no-gutters
        >
          <v-col
            cols="5"
          >
            <v-text-field
              v-model="currentProtocol.doi"
              label="DOI"
              outlined
              dense
              :rules="doiValueRules()"
              @blur="updateMultiOmicsForm('acquisitionProtocol')"
            >
              <template #append-outer>
                <v-tooltip
                  right
                  class="x-2"
                  max-width="500"
                >
                  <template #activator="{ on, attrs }">
                    <v-icon
                      v-bind="attrs"
                      dense
                      v-on="on"
                    >
                      mdi-help-circle
                    </v-icon>
                  </template>
                  <span>
                    Provide a DOI for the protocol. This is not for the study publication, but a public protocol that explains the protocol in detail. Multiple DOIs can be provided.
                  </span>
                </v-tooltip>
              </template>
            </v-text-field>
          </v-col>
          <v-col
            cols="5"
          >
            <v-text-field
              v-model="currentProtocol.url"
              label="URL"
              outlined
              dense
              :rules="urlValueRules()"
              @blur="updateMultiOmicsForm('acquisitionProtocol')"
            >
              <template #append-outer>
                <v-tooltip
                  right
                  class="x-2"
                  max-width="500"
                >
                  <template #activator="{ on, attrs }">
                    <v-icon
                      v-bind="attrs"
                      dense
                      v-on="on"
                    >
                      mdi-help-circle
                    </v-icon>
                  </template>
                  <span>
                    Provide a URL for the protocol. This is not for the study publication, but a public protocol that explains the protocol in detail. Multiple URLs can be provided.
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
              v-model="currentProtocol.name"
              label="Protocol Name"
              outlined
              dense
              @blur="updateMultiOmicsForm('acquisitionProtocol')"
            >
              <template #append-outer>
                <v-tooltip
                  right
                  max-width="500"
                >
                  <template #activator="{ on, attrs }">
                    <v-icon
                      v-bind="attrs"
                      dense
                      v-on="on"
                    >
                      mdi-help-circle
                    </v-icon>
                  </template>
                  <span>
                    Provide a name for this protocol. If multiple protocols are used, this name will be required for later steps.
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
            v-model="currentProtocol.description"
            label="Protocol Description"
            outlined
            dense
            rows="3"
            @blur="updateMultiOmicsForm('acquisitionProtocol')"
          />
        </v-row>
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel>
      <v-expansion-panel-header>
        <div>
          Data Access
          <v-tooltip
            right
            class="x-2"
            max-width="500"
          >
            <template #activator="{ on, attrs }">
              <v-icon
                v-bind="attrs"
                class="ml-1 mb-1"
                small
                v-on="on"
              >
                mdi-help-circle
              </v-icon>
            </template>
            <span>
              Provide the location of the publically available proteomics data. This can be a direct URL or a DOI or an identifier.
            </span>
          </v-tooltip>
        </div>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <div>
          <v-row
            class="mx-8 "
            no-gutters
          >
            <v-col
              cols="5"
            >
              <v-text-field
                v-model="currentProtocol.doi"
                label="DOI"
                outlined
                dense
                :rules="doiValueRules()"
                @blur="updateMultiOmicsForm('dataProtocol')"
              >
                <template #append-outer>
                  <v-tooltip
                    right
                    class="x-2"
                    max-width="500"
                  >
                    <template #activator="{ on, attrs }">
                      <v-icon
                        v-bind="attrs"
                        dense
                        v-on="on"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a DOI for the protocol. This is not for the study publication, but a public protocol that explains the protocol in detail. Multiple DOIs can be provided.              </span>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
            <v-col
              cols="5"
            >
              <v-text-field
                v-model="currentProtocol.url"
                label="URL"
                outlined
                dense
                :rules="urlValueRules()"
                @blur="updateMultiOmicsForm('dataProtocol')"
              >
                <template #append-outer>
                  <v-tooltip
                    right
                    class="x-2"
                    max-width="500"
                  >
                    <template #activator="{ on, attrs }">
                      <v-icon
                        v-bind="attrs"
                        dense
                        v-on="on"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>
                      Provide a URL for the protocol. This is not for the study publication, but a public protocol that explains the protocol in detail. Multiple URLs can be provided.
                    </span>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
          </v-row>
        </div>
      </v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
</template>
