import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';

import { User } from '@/types';
import { RouteLocationRaw } from 'vue-router';
import { InjectionKey, Ref } from 'vue';

/**
 * A manifest of the options available in DataHarmonizer
 */
export const EMSL = 'emsl';
export const JGI_MG = 'jgi_mg';
export const JGI_MG_LR = 'jgi_mg_lr';
export const JGI_MT = 'jgi_mt';
export const DATA_MG = 'data_mg';
export const DATA_MG_INTERLEAVED = 'data_mg_interleaved';
export const DATA_MT = 'data_mt';
export const DATA_MT_INTERLEAVED = 'data_mt_interleaved';

export interface HarmonizerTemplateInfo {
  displayName: string,
  schemaClass: string,
  sampleDataSlot: string,
  status: 'published' | 'mixin' | 'disabled',
}
export const HARMONIZER_TEMPLATES = {
  air: {
    displayName: 'air',
    schemaClass: 'AirInterface',
    sampleDataSlot: 'air_data',
    status: 'published',
  },
  'built environment': {
    displayName: 'built environment',
    schemaClass: 'BuiltEnvInterface',
    sampleDataSlot: 'built_env_data',
    status: 'published',
  },
  'host-associated': {
    displayName: 'host-associated',
    schemaClass: 'HostAssociatedInterface',
    sampleDataSlot: 'host_associated_data',
    status: 'published',
  },
  'hydrocarbon resources-cores': {
    displayName: 'hydrocarbon resources - cores',
    schemaClass: 'HcrCoresInterface',
    sampleDataSlot: 'hcr_cores_data',
    status: 'published',
  },
  'hydrocarbon resources-fluids_swabs': {
    displayName: 'hydrocarbon resources - fluids swabs',
    schemaClass: 'HcrFluidsSwabsInterface',
    sampleDataSlot: 'hcr_fluids_swabs_data',
    status: 'published',
  },
  'microbial mat_biofilm': {
    displayName: 'microbial mat_biofilm',
    schemaClass: 'BiofilmInterface',
    sampleDataSlot: 'biofilm_data',
    status: 'published',
  },
  'miscellaneous natural or artificial environment': {
    displayName: 'miscellaneous natural or artificial environment',
    schemaClass: 'MiscEnvsInterface',
    sampleDataSlot: 'misc_envs_data',
    status: 'published',
  },
  'plant-associated': {
    displayName: 'plant-associated',
    schemaClass: 'PlantAssociatedInterface',
    sampleDataSlot: 'plant_associated_data',
    status: 'published',
  },
  sediment: {
    displayName: 'sediment',
    schemaClass: 'SedimentInterface',
    sampleDataSlot: 'sediment_data',
    status: 'published',
  },
  soil: {
    displayName: 'soil',
    schemaClass: 'SoilInterface',
    sampleDataSlot: 'soil_data',
    status: 'published',
  },
  water: {
    displayName: 'water',
    schemaClass: 'WaterInterface',
    sampleDataSlot: 'water_data',
    status: 'published',
  },
  [EMSL]: {
    displayName: 'EMSL',
    schemaClass: 'EmslInterface',
    sampleDataSlot: 'emsl_data',
    status: 'mixin',
  },
  [JGI_MG]: {
    displayName: 'JGI MG',
    schemaClass: 'JgiMgInterface',
    sampleDataSlot: 'jgi_mg_data',
    status: 'mixin',
  },
  [JGI_MG_LR]: {
    displayName: 'JGI MG (Long Read)',
    schemaClass: 'JgiMgLrInterface',
    sampleDataSlot: 'jgi_mg_lr_data',
    status: 'mixin',
  },
  [JGI_MT]: {
    displayName: 'JGI MT',
    schemaClass: 'JgiMtInterface',
    sampleDataSlot: 'jgi_mt_data',
    status: 'mixin',
  },
  [DATA_MG]: {
    displayName: 'Metagenomics Data',
    schemaClass: 'MetagenomeSequencingNonInterleavedDataInterface',
    sampleDataSlot: 'metagenome_sequencing_non_interleaved_data',
    status: 'mixin',
  },
  [DATA_MG_INTERLEAVED]: {
    displayName: 'Metagenomics Data (Interleaved)',
    schemaClass: 'MetagenomeSequencingInterleavedDataInterface',
    sampleDataSlot: 'metagenome_sequencing_interleaved_data',
    status: 'mixin',
  },
  [DATA_MT]: {
    displayName: 'Metatranscriptomics Data',
    schemaClass: 'MetatranscriptomeSequencingNonInterleavedDataInterface',
    sampleDataSlot: 'metatranscriptome_sequencing_non_interleaved_data',
    status: 'mixin',
  },
  [DATA_MT_INTERLEAVED]: {
    displayName: 'Metatranscriptomics Data (Interleaved)',
    schemaClass: 'MetatranscriptomeSequencingInterleavedDataInterface',
    sampleDataSlot: 'metatranscriptome_sequencing_interleaved_data',
    status: 'mixin',
  },
} satisfies Record<string, HarmonizerTemplateInfo>;

export type TemplateName = keyof typeof HARMONIZER_TEMPLATES;

export const JGI_TEMPLATE_NAMES: TemplateName[] = [JGI_MG, JGI_MG_LR, JGI_MT]

export enum BiosafetyLevels {
  BSL1 = 'BSL1',
  BSL2 = 'BSL2'
}

export enum AwardTypes {
  CSP = 'CSP',
  BERSS = 'BERSS',
  BRCS = 'BRCs',
  MONET = 'MONet',
  FICUS = 'FICUS'
}

export enum SuggestionType {
  ALL = 'All Types',
  ADDITIONS = 'Additions Only',
  REPLACEMENTS = 'Replacements Only',
}

export enum SuggestionsMode {
  LIVE = 'Live',
  ON_DEMAND = 'On Demand',
  OFF = 'Off',
}

export interface CellData {
  row: number,
  col: number,
  text: string,
}

export interface ColumnHelpInfo {
  title: string,
  name: string,
  description: string,
  guidance: string,
  examples: string,
  sources: string,
}

export interface MetadataSuggestionRequest {
  row: number,
  data: Record<string, string>,
}

export interface MetadataSuggestion {
  type: 'add' | 'replace' | 'attention';
  row: number | null;
  slot: string;
  value: string | null;
  current_value: string | null;
  is_ai_generated: boolean;
  source: string | null;
}

export interface NmdcAddress {
  name: string;
  email: string;
  phone: string;
  line1: string;
  line2: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

export interface ValidatedForm {
  validation: string[] | null;
}

export interface SenderShippingInfoForm extends ValidatedForm {
  shipper: NmdcAddress;
  expectedShippingDate: string | null;
  shippingConditions: string;
  sample: string;
  description: string;
  experimentalGoals: string;
  randomization: string;
  usdaRegulated: boolean | null;
  permitNumber: string;
  biosafetyLevel: string;
  irbOrHipaa: boolean | null;
  comments: string;
}

export interface ExternalProtocol {
  url: string | null;
  doi: string | null;
  name: string | null;
  description: string | null;
}

export interface Protocols {
  sampleProtocol: SampleProtocol,
  acquisitionProtocol: AcquisitionProtocol,
  dataProtocol: DataProtocol,
}

export type OmicsProcessingType =
  // non-doe types
  'mg' | 'mt' | 'mp' | 'mb' | 'mb-gc' | 'nom' | 'nom-lc' | 'lipidome' |
  // doe facility associated types
  'lipidome-emsl' | 'mp-emsl' | 'mb-emsl' | 'nom-emsl' | 'mg-jgi' | 'mg-lr-jgi' | 'mt-jgi' | 'mb-jgi';

export interface MultiOmicsForm extends ValidatedForm {
  award: string | null;
  awardDois: Doi[] | null;
  dataGenerated: boolean | null;
  doe: boolean | null;
  facilities: string[] | null;
  facilityGenerated: boolean | null;
  JGIStudyId: string;
  mgCompatible: boolean | null;
  mgInterleaved: boolean | null;
  mtCompatible: boolean | null;
  mtInterleaved: boolean | null;
  omicsProcessingTypes: OmicsProcessingType[];
  otherAward: string | null;
  ship: boolean | null;
  studyNumber: string
  unknownDoi: boolean | null;
  mpProtocols: Protocols | null;
  mbProtocols: Protocols | null;
  mbGcProtocols: Protocols | null;
  lipProtocols: Protocols | null;
  nomProtocols: Protocols | null;
  nomLcProtocols: Protocols | null;
}

export interface SubmissionPage {
  title: string;
  link: RouteLocationRaw;
  validationMessages: string[] | null;
}

export interface SampleMetadataValidationState {
  invalidCells: Record<string, Record<number, Record<number, string>>>;
  tabsValidated: Record<string, boolean>;
}

export interface SampleData {
  data: Record<string, any[]>;
  validation: SampleMetadataValidationState | null;
}

export interface SampleEnvironmentForm extends ValidatedForm {
  packageName: (keyof typeof HARMONIZER_TEMPLATES)[];
}

export interface Contributor {
  name: string;
  orcid: string;
  roles: string[];
  permissionLevel: SubmissionEditorRole | null;
}

export interface StudyFormCreate extends ValidatedForm {
  studyName: string;
  piName: string;
  piEmail: string;
  piOrcid: string;
  fundingSources: string[] | null;
  dataDois: Doi[] | null;
  publicationDois: Doi[] | null;
  linkOutWebpage: string[];
  studyDate: string | null;
  description: string;
  notes: string;
  contributors: Contributor[];
}

export interface StudyForm extends StudyFormCreate {
  alternativeNames: string[];
  GOLDStudyId: string;
  NCBIBioProjectId: string;
}

export interface SubmissionMetadataSlim {
  id: string;
  author: User;
  study_name: string;
  date_last_modified: string;
  created: string;
  is_test_submission: boolean;
  sample_count: number;
  reviewers: string[];
  contributors: string[];
}

export type SourceClient = 'submission_portal' | 'field_notes' | 'nmdc_edge';

export interface SubmissionMetadataCreate {
  study_form: StudyFormCreate;
  source_client: SourceClient | null;
  is_test_submission: boolean;
}

export interface SubmissionMetadataPatch {
  study_form?: StudyForm;
  permissions?: Record<string, string>;
}

export interface SubmissionMetadata extends SubmissionMetadataSlim {
  author_orcid: string;
  study_form: StudyForm;
  nmdc_study_id: string | null;
  locked_by: User | null;
  lock_updated: string | null;
  permission_level: SubmissionEditorRole | null;
  source_client: SourceClient | null;
  primary_study_image_url: string | null;
  pi_image_url: string | null;
  sample_sets: SubmissionSampleSetListItem[];
}

export interface SubmissionSampleSetListItem {
  id: string;
  name: string;
  templates: string[];
  status: string;
  created: string;
  date_last_modified: string;
}

export interface SubmissionSampleSetCreate {
  name: string;
  templates: string[];
  status?: string;
  multi_omics_form: MultiOmicsForm
  sample_environment_form: SampleEnvironmentForm;
  sender_shipping_info_form: SenderShippingInfoForm;
  sample_data: SampleData;
}

export interface SubmissionSampleSetPatch {
  name?: string;
  templates?: string[];
  multi_omics_form?: MultiOmicsForm;
  sample_environment_form?: SampleEnvironmentForm;
  sender_shipping_info_form?: SenderShippingInfoForm;
  sample_data?: SampleData;
}

export interface SubmissionSampleSetStatusPatch {
  status: string;
}

export interface SubmissionSampleSet extends SubmissionSampleSetListItem {
  multi_omics_form: MultiOmicsForm;
  sample_environment_form: SampleEnvironmentForm;
  sender_shipping_info_form: SenderShippingInfoForm;
  sample_data: SampleData;
}

export interface PaginatedResponse<T> {
  count: number;
  results: T[];
}

export interface LockOperationResult {
  success: boolean;
  message: string
  locked_by: User | null;
  lock_updated: string | null;
}

export interface Doi {
  value: string;
  provider: string | null;
}

export interface DataProtocol {
  url?: string;
  doi?: string;
}
export interface AcquisitionProtocol extends DataProtocol {
  name?: string;
  description?: string;
}

export interface SampleProtocol extends AcquisitionProtocol {
  sharedData: boolean;
  sharedDataName?: string;
}

export type PermissionTitle = 'Viewer' | 'Metadata Contributor' | 'Editor';

export type SubmissionEditorRole = 'viewer' | 'reviewer' | 'metadata_contributor' | 'editor' | 'owner';

export type UneditableReason = 'locked_by_other' | 'insufficient_permissions' | 'uneditable_status';

export const SubmissionStatusEnum = NmdcSchema.enums.SubmissionStatusEnum.permissible_values;
export type SubmissionStatusKey = keyof typeof SubmissionStatusEnum;

export type AllowedStatusTransitions = Record<SubmissionEditorRole, Record<SubmissionStatusKey, SubmissionStatusKey[]>>;

export interface SignedUploadUrlRequest {
  file_name: string;
  file_size: number;
  content_type: string;
}

export interface SignedUrl {
  url: string;
  object_name: string;
  expiration: string;
}

export interface UploadCompleteRequest {
  object_name: string;
  file_size: number;
  content_type: string;
}

export type SubmissionImageType = 'pi_image' | 'primary_study_image' | 'study_images';
export interface StatusOption {
  value: string;
  title: string;
}

export const AppBannerHeightKey = Symbol() as InjectionKey<Ref<number>>;
