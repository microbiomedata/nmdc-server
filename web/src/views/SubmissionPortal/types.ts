import { User } from '@/types';

/**
 * A manifest of the options available in DataHarmonizer
 */
export const EMSL = 'emsl';
export const JGI_MG = 'jgi_mg';
export const JGI_MG_LR = 'jgi_mg_lr';
export const JGT_MT = 'jgi_mt';
export interface HarmonizerTemplateInfo {
  displayName: string,
  schemaClass?: string,
  sampleDataSlot?: string,
  status: 'published' | 'mixin' | 'disabled',
  // This value comes from annotations in the schema. It will be populated once the schema is loaded.
  excelWorksheetName?: string,
}
export const HARMONIZER_TEMPLATES: Record<string, HarmonizerTemplateInfo> = {
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
  'human-associated': {
    displayName: 'human-associated',
    status: 'disabled',
  },
  'human-gut': {
    displayName: 'human - gut',
    status: 'disabled',
  },
  'human-oral': {
    displayName: 'human - oral',
    status: 'disabled',
  },
  'human-skin': {
    displayName: 'human - skin',
    status: 'disabled',
  },
  'human-vaginal': {
    displayName: 'human - vaginal',
    status: 'disabled',
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
  [JGT_MT]: {
    displayName: 'JGI MT',
    schemaClass: 'JgiMtInterface',
    sampleDataSlot: 'jgi_mt_data',
    status: 'mixin',
  },
};

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
  type: 'add' | 'replace'
  row: number
  slot: string
  value: string
  current_value?: string
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

export interface MetadataSubmission {
  packageName: (keyof typeof HARMONIZER_TEMPLATES)[];
  addressForm: any;
  templates: string[];
  studyForm: any;
  multiOmicsForm: any;
  sampleData: Record<string, any[]>;
}

export interface MetadataSubmissionRecord {
  id: string;
  author_orcid: string;
  created: string;
  metadata_submission: MetadataSubmission;
  status: string;
  locked_by: User;
  lock_updated: string;
  permission_level: string | null;
  source_client: 'submission_portal' | 'field_notes' | 'nmdc_edge' | null;
  study_name: string;
  templates: string[];
  is_test_submission: boolean;
  date_last_modified: string;
}

export interface PaginatedResponse<T> {
  count: number;
  results: T[];
}

export interface LockOperationResult {
  success: boolean;
  message: string
  locked_by?: User | null;
  lock_updated?: string | null;
}

export type PermissionTitle = 'Viewer' | 'Metadata Contributor' | 'Editor';

export type PermissionLevelValues = 'viewer' | 'metadata_contributor' | 'editor' | 'owner';

export type SubmissionStatus = 'In Progress' | 'Submitted- Pending Review' | 'Complete';
