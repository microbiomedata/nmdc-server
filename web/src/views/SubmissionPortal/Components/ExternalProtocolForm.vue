<script setup lang="ts">
import { defineProps, computed, ref } from 'vue';
import { multiOmicsForm, checkDoiFormat } from '../store';

type DataType = 'mpProtocols' | 'mbProtocols' | 'nomProtocols' | 'lipProtocols';

type ProtocolHelp = {
  samplePrepHint: string,
  samplePrepExample: string,
  dataAcquisitionHint: string,
  dataAcquisitionExample: string,
}

const protocolHelp: Record<DataType, ProtocolHelp> = {
  mpProtocols: {
    samplePrepHint: "The description should include details such as extractant(s), digestion enzyme(s), alklyation, and fractionation (if performed).",
    samplePrepExample: "30g of soil was bead beat in 60% MeOH for 15 min at 4°C. 12 mL of ice-cold chloroform was added " +
      "to the sample. Samples were probe sonicated at 60% amplitude for 30 seconds on ice, cooled on ice and sonicated " +
      "again. Samples were incubated for 5 min at -80°C, vortexed for 1 min and centrifuged at 4,500g for 10 min at " +
      "4°C. The upper aqueous phase was removed. The interphase was collected into a separate tube. 5mL of ice cold " +
      "100% methanol was added to the sample which was then vortexed and centrifuged at 4,500g for 5 min at 4°C. The " +
      "supernatant was decanted off and the protein dried inverted on a Kimwipe.\n\n" +
      "20 mL of SDS-TRIS buffer was added to the sample before incubation at 95°C for 5 minutes then 20 mins at 4°C. The " +
      "samples were centrifuged at 4,500g for 10 mins and the supernatants were decanted into polypropylene 50 mL tubes. " +
      "The proteins were precipitated by adding trichloroacetic acid, vortexed and stored at -20°C for 90 min. The " +
      "samples were thawed and centrifuged at 4,500g at 4°C for 10 mins. The supernatant was poured off and 2 mL of ice " +
      "cold acetone was added to the pellet, then vortexed. The sample was placed at -80°C for ~5 mins and centrifuged " +
      "for 10 mins at 4,500g at 4°C. The acetone was poured off and pellets were dried inverted on a Kimwipe for ~15 " +
      "mins. Protein interphases from the particulates and from the supernatants were combined using 100ul of SDS-Tris " +
      "buffer. Proteins were digested using 1ug/uL trypsin according to the Expedeon FASP digestion kit.",
    dataAcquisitionHint: "This description should include chromatographic and spectrometry conditions including MS2 acquisition mode and polarity.",
    dataAcquisitionExample: "Proteomics samples were separated by liquid chromatography using a 90 minute gradient " +
      "with 1% formic acid in water (A) and 0.1% formic acid in acetonitrile (B) on a C18 hand-pulled column maintained " +
      "at room temperature.\n\n" +
      "The LC system was interfaced with an Orbitrap mass spectrometer using electrospray ionization. Samples were " +
      "measured in positive ionization mode using data-dependent acquisition. The full scan was collected in profile, " +
      "MS2 was collected in centroid mode with HCD (high resolution).",
  },
  mbProtocols: {
    samplePrepHint: "The description should include details such as extractant(s), derivatization, any cleanup steps, and reconstitution solvent(s).",
    samplePrepExample: "Samples were dissolved in 1mL of 70% MeOH and homogenized in a QIAGEN tissue lyser. Tubes were " +
      "centrifuged at 15000 rpm for 15 min and the supernatant was transferred to a 96-well plate. Plates were dried " +
      "with a vacuum concentrator. Samples were resuspended in 300uL of 70% MeOH and transferred to SPE plates, washed" +
      " with water, and eluted sequentially in 600uL of 70% MeOH and 600 uL of 100% MeOH. Samples were dried with a " +
      "vacuum concentrator then resuspended in 130uL of 70% MeOH containing 0.2 uM of amitriptyline. Plates were " +
      "centrifuged at 2000rpm for 15 min at 4C. 100uL of resulting supernatant was transferred to a new 96-well plate " +
      "for LC-MS analysis.",
    dataAcquisitionHint: "This description should include chromatographic and spectrometry conditions including MS2 acquisition mode and polarity.",
    dataAcquisitionExample: "Separation was performed using reverse-phase C18 liquid chromatography, with 10 µl " +
      "injected onto a Waters CSH column (dimensions: 3.0 mm x 150 mm, 1.7 µm particle size), maintained at 42ºC. " +
      "Separation occurs over a 34-minute gradient at a flow rate of 0.25 mL/min. The gradient begins with 60% mobile " +
      "phase A (ACN/H2O, 40:60, containing 10 mM ammonium acetate) and 40% mobile phase B (ACN/IPA, 10:90, containing " +
      "10 mM ammonium acetate) at 0 minutes. By 2 minutes, this shifts to 50% mobile phase A and 50% mobile phase B, " +
      "progressively transitioning to 40% A and 60% B at 3 minutes, 30% A and 70% B at 12 minutes, and ultimately " +
      "reaching 1% A and 99% B at 25 minutes and remaining stable until 34 minutes.\n\n" +
      "The LC system was interfaced to an LTQ-Velos Orbitrap mass spectrometer (Thermo Scientific, San Jose, CA) " +
      "using electrospray ionization. MS/MS data were collected in data-dependent mode using normalized collision " +
      "energies (NCE) of 35 or 30. Each sample was analyzed in both positive and negative ESI modes.",
  },
  nomProtocols: {
    samplePrepHint: "The description should include details such as extractant(s) and any cleanup steps.",
    samplePrepExample: "300mg of soil was added to a glass vial for sequential extraction. 1mL of MilliQ water was " +
      "added to the vial. The vial was shaken at room temperature and 2000 RPM for 2 hours, then centrifuged at " +
      "4500RPM for 5 minutes. The water supernatant was pulled off and stored at -80C. Extraction was repeated using " +
      "1mL of methanol followed by 1mL of ethanol-stabilized chloroform.",
    dataAcquisitionHint: "This description should include spectrometry conditions like polarity and acquisition mode and (if applicable) chromatographic conditions.",
    dataAcquisitionExample: "Extracts were analyzed using Fourier transform ion cyclotron mass spectrometry (FT-ICR-MS) " +
      "with a 12 T Bruker SolariX equipped with a standard Bruker electrospray ionization (ESI) source using negative " +
      "polarity acquired in full scan, located at the Environmental Molecular Sciences Laboratory (EMSL) user facility " +
      "located in Richland, WA, USA.",
  },
  lipProtocols: {
    samplePrepHint: "The description should include details such as the amount of starting material, extractant(s), reconstitution solvent, and reconstituted volume.",
    samplePrepExample: "Soil was bead beat in 60% MeOH for 15 min at 4°C. 12 mL of ice-cold chloroform was added to " +
      "the sample. Samples were probe sonicated at 60% amplitude for 30 seconds on ice, cooled on ice and sonicated " +
      "again. Samples were incubated for 5 min at -80°C, vortexed for 1 min and centrifuged at 4,500g for 10 min at " +
      "4°C. The upper aqueous phase and interphase were removed. The lower chloroform layer was transferred to a " +
      "separate glass vial and dried, then resuspended in 400uL of 2:1 chloroform:methanol. Samples were spun down to " +
      "remove debris and the supernatants were transferred to glass vials and stored at -20C in preparation for LC-MS " +
      "analysis.",
    dataAcquisitionHint: "This description should include chromatographic and spectrometry conditions including MS2 acquisition mode and polarity.",
    dataAcquisitionExample: "Separation was performed using reverse-phase C18 liquid chromatography, with 10 µl " +
      "injected onto a Waters CSH column (dimensions: 3.0 mm x 150 mm, 1.7 µm particle size), maintained at 42ºC. " +
      "Separation occurs over a 34-minute gradient at a flow rate of 0.25 mL/min. The gradient begins with 60% mobile " +
      "phase A (ACN/H2O, 40:60, containing 10 mM ammonium acetate) and 40% mobile phase B (ACN/IPA, 10:90, containing " +
      "10 mM ammonium acetate) at 0 minutes. By 2 minutes, this shifts to 50% mobile phase A and 50% mobile phase B, " +
      "progressively transitioning to 40% A and 60% B at 3 minutes, 30% A and 70% B at 12 minutes, and ultimately " +
      "reaching 1% A and 99% B at 25 minutes and remaining stable until 34 minutes.\n\n" +
      "The LC system was interfaced to an LTQ-Velos Orbitrap mass spectrometer (Thermo Scientific, San Jose, CA) " +
      "using electrospray ionization. MS/MS data were collected in data-dependent mode using normalized collision " +
      "energies (NCE) of 35 or 30. Each sample was analyzed in both positive and negative ESI modes.",
  },
}

const props = defineProps<{
  dataType: DataType,
}>();

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

const existingProtocols = computed(() => multiOmicsForm[props.dataType]);

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
const showSamplePrepExampleDialog = ref(false);
const showDataAcquisitionExampleDialog = ref(false);

function updateMultiOmicsForm() {
  multiOmicsForm[props.dataType] = currentProtocol.value;
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
            hide-details="auto"
            rows="3"
            @blur="updateMultiOmicsForm()"
          />
          <div class="text-caption text-medium-emphasis px-4 pt-1">
            {{ protocolHelp[props.dataType].samplePrepHint }}
            <a
              href="#"
              class="text-primary text-decoration-none"
              @click.prevent="showSamplePrepExampleDialog = true"
            >
              View Example.
            </a>
          </div>
          <v-dialog
            v-model="showSamplePrepExampleDialog"
            max-width="600"
          >
            <v-card title="Sample Preparation Protocol Description Example">
              <v-card-text>
                <div class="text-body-2 mb-4">
                  Use this as a guide for writing your own protocol description.
                </div>
                <v-textarea
                  auto-grow
                  variant="outlined"
                  readonly
                  hide-details="auto"
                  max-height="500"
                  :model-value="protocolHelp[props.dataType].samplePrepExample"
                  @click.control="(e: MouseEvent) => (e.target as HTMLTextAreaElement)?.select()"
                />
              </v-card-text>
              <v-card-actions>
                <v-spacer />
                <v-btn
                  color="primary"
                  @click="showSamplePrepExampleDialog = false"
                >
                  Close
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
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
        <div class="text-caption text-medium-emphasis px-4 pt-1">
          {{ protocolHelp[props.dataType].dataAcquisitionHint }}
          <a
            href="#"
            class="text-primary text-decoration-none"
            @click.prevent="showDataAcquisitionExampleDialog = true"
          >
            View Example.
          </a>
        </div>
        <v-dialog
          v-model="showDataAcquisitionExampleDialog"
          max-width="600"
        >
          <v-card title="Data Acquisition Protocol Description Example">
            <v-card-text>
              <div class="text-body-2 mb-4">
                Use this as a guide for writing your own protocol description.
              </div>
              <v-textarea
                auto-grow
                variant="outlined"
                readonly
                hide-details="auto"
                max-height="500"
                :model-value="protocolHelp[props.dataType].dataAcquisitionExample"
                @click.control="(e: MouseEvent) => (e.target as HTMLTextAreaElement)?.select()"
              />
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn
                color="primary"
                @click="showDataAcquisitionExampleDialog = false"
              >
                Close
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
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
