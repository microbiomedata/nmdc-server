import { merge } from 'lodash';
import axios from 'axios';
import { setupCache } from 'axios-cache-adapter';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc.schema.json';

const cache = setupCache({
  key: (req) => req.url + JSON.stringify(req.params) + JSON.stringify(req.data),
  maxAge: 15 * 60 * 1000,
  exclude: {
    query: false,
    methods: ['delete'],
    paths: [
      /logout/,
      /data_object\/.*/,
    ],
  },
});

const client = axios.create({
  baseURL: process.env.VUE_APP_BASE_URL || '/api',
  adapter: cache.adapter,
});

const staticFileClient = axios.create({
  baseURL: '/static',
});

/* The real entity types */
export type entityType = 'biosample'
  | 'study'
  | 'omics_processing'
  | 'reads_qc'
  | 'metagenome_assembly'
  | 'metagenome_annotation'
  | 'metaproteomic_analysis'
  | 'data_object'
  | 'gene_function';

/**
 * By including this file in source with a git submodule,
 * we get build-time typescript support for the dynamic types coming
 * out of an entirely different repository.
 */
export type entitySchemaType = keyof typeof NmdcSchema.$defs;

export interface BaseSearchResult {
  id: string;
  name: string;
  description: string;
  alternate_identifiers: string[];
  annotations: Record<string, string | string[]>;
  [key: string]: unknown; // possibly other things.
}

export interface DataObjectSearchResult extends BaseSearchResult {
  file_size_bytes: number | null;
  md5_checksum: string;
  file_type: string;
  file_type_description: string;
  url: string;

  // download count
  downloads: number;

  // indicates selected for bulk download
  selected: boolean;
}

export interface DerivedDataResult extends BaseSearchResult {
  type: string;
  git_url: string;
  started_at_time: string;
  ended_at_time: string;
  execution_resource: string;
  omics_processing_id: string;
  outputs: DataObjectSearchResult[];
}

export interface OmicsProcessingResult extends BaseSearchResult {
  study_id: string;
  add_date: string;
  mod_date: string;
  open_in_gold: string;
  omics_data: DerivedDataResult[];
  outputs: DataObjectSearchResult[]; // RAW outputs
}

export interface BiosampleSearchResult extends BaseSearchResult {
  omics_processing_id: string;
  depth: number;
  env_broad_scale_id: string;
  env_local_scale_id: string;
  env_medium_id: string;
  longitude: number | null;
  latitude: number | null;
  add_date: string;
  mod_date: string;
  open_in_gold: string;
  env_broad_scale: {
    id: string;
    label: string;
    data: string;
  };
  env_local_scale: {
    id: string;
    label: string;
    data: string;
  };
  env_medium: {
    id: string;
    label: string;
    data: string;
  };
  omics_processing: OmicsProcessingResult[];
  emsl_biosample_identifiers: string[];
}

interface PrincipalInvestigator {
  name?: string;
  email?: string;
  orcid?: string;
}

export interface DOI {
  cite: string,
  id:string,
  provider: string,
}

export interface DOIMAP {
  info: Record<string, any>,
  category: string,
  provider: string,
}

export interface StudySearchResults extends BaseSearchResult {
  principal_investigator_websites: string[];
  principal_investigator_name: string;
  principal_investigator_image_url: string;
  image_url: string;
  principal_investigator: PrincipalInvestigator;
  award_dois: DOI[];
  dataset_dois: DOI[],
  doi_map: Record<string, DOIMAP>,
  publication_dois: DOI[];
  omics_counts: {
    type: string;
    count: number;
  }[];
  omics_processing_counts: {
    type: string;
    count: number;
  }[];
  gold_name: string;
  gold_description: string;
  scientific_objective: string;
  add_date: string;
  mod_date: string;
  open_in_gold: string;
  funding_sources: string[];
  relevant_protocols: string[];
  gold_study_identifiers: string[];
  sample_count: number;
  study_category: string;
  homepage_website: string[] | null;
  part_of: string[] | null;
  children: StudySearchResults[];
  has_credit_associations: {
    applied_roles: string[];
    applies_to_person: {
      name?: string;
      orcid?: string;
      email?: string;
    };
  }[];
}

export interface ReadsQCResult extends DerivedDataResult {
  stats: object;
  has_inputs: string[];
  has_output: string[];
}

export interface MetagenomeAssembyResult extends DerivedDataResult {
  stats: object;
  has_inputs: string[];
  has_output: string[];
}

export interface MetagenomeAnnotationResult extends DerivedDataResult {
  stats: object;
  has_inputs: string[];
  has_output: string[];
}

export type MetaproteomicAnalysisResult = DerivedDataResult;

export interface UnitSchema {
  /* https://github.com/microbiomedata/nmdc-server/pull/350 */
  name: string;
  abbreviation: string;
  dimensionality: {
    quantity: string;
    exponent: 1;
  }[];
}

export interface AttributeSummary {
  count: number;
  type: 'string' | 'date' | 'integer' | 'float' | 'kegg_search';
  min?: string | number;
  max?: string | number;
  units?: UnitSchema;
}

export interface TableSummary {
  total: number;
  attributes: Record<string, AttributeSummary>;
}

export type DatabaseSummaryResponse = Record<entityType, TableSummary>;

export interface DatabaseStatsResponse {
  studies: number;
  locations: number;
  habitats: number;
  data_size: number;
  metagenomes: number;
  metatranscriptomes: number;
  proteomics: number;
  metabolomics: number;
  lipodomics: number;
  organic_matter_characterization: number;
}

export interface FacetSummaryResponse {
  facet: string;
  count: number;
}

export interface EnvironmentGeospatialEntity {
  count: number;
  ecosystem: string;
  ecosystem_category: string;
  latitude: number | null;
  longitude: number | null;
}

interface EnvironmentSankeyEntity {
  count: number;
  ecosystem: string;
  ecosystem_category: string;
  ecosystem_type: string;
  ecosystem_subtype: string;
  specific_ecosystem: string;
}

export interface EnvironmentSankeyResponse {
  [index: number]: EnvironmentSankeyEntity;
}

export type opType = 'between' | '<' | '<=' | '>' | '>=' | '==' | '!=' | 'has' | 'like';
export const opMap: Record<opType, string> = {
  between: 'between',
  has: 'has',
  '<': 'less',
  '<=': 'lte',
  '>': 'greater',
  '>=': 'gte',
  '!=': 'not',
  '==': 'is',
  like: 'like',
};

// See https://github.com/microbiomedata/nmdc-server/pull/403 for documentation
export type BulkDownloadSummary = Record<string, {
  count: number;
  file_types: Record<string, number>,
}>;

export type BulkDownloadAggregateSummary = {
  count: number;
  size: number;
};

export interface Condition {
  field: string;
  op: opType;
  value: string | number | [number, number];
  table: string;
}

export interface DataObjectFilter {
  workflow: string;
  file_type: string;
}

export interface EnvoNode {
  id: string;
  label: string;
  children?: EnvoNode[];
}

export interface EnvoTree {
  trees: Record<string, EnvoNode[]>;
}

export interface BulkDownload {
  ip: string;
  user_agent: string;
  orcid: string;
  conditions: Condition[];
  filter: DataObjectFilter[];
  id: string;
  created: string;
  url: string;
}

export interface SearchParams {
  offset?: number;
  limit?: number;
  conditions: Condition[];
  data_object_filter?: DataObjectFilter[];
}

export interface SearchResponse<T> {
  count: number;
  results: T[];
}

export interface BinResponse<T = string | number> {
  bins: T[];
  facets: number[];
}

export interface User{
    id: string,
    orcid: string;
    name: string;
    is_admin: boolean;
}

async function _search<T>(
  table: string,
  {
    offset = 0, limit = 100, conditions, data_object_filter,
  }: SearchParams,
): Promise<SearchResponse<T>> {
  const { data } = await client.post<SearchResponse<T>>(
    `${table}/search`,
    { conditions, data_object_filter },
    {
      params: { offset, limit },
    },
  );
  return data;
}

async function searchBiosample(params: SearchParams) {
  return _search<BiosampleSearchResult>('biosample', params);
}

async function searchStudy(params: SearchParams) {
  return _search<StudySearchResults>('study', params);
}

async function searchOmicsProcessing(params: SearchParams) {
  return _search<OmicsProcessingResult>('omics_processing', params);
}

async function searchReadsQC(params: SearchParams) {
  return _search<ReadsQCResult>('reads_qc', params);
}

async function searchMetagenomeAssembly(params: SearchParams) {
  return _search<MetagenomeAssembyResult>('metagenome_assembly', params);
}

async function searchMetagenomeAnnotation(params: SearchParams) {
  return _search<MetagenomeAnnotationResult>('metagenome_annotation', params);
}

async function searchMetaproteomicAnalysis(params: SearchParams) {
  return _search<MetaproteomicAnalysisResult>('metaproteomic_analysis', params);
}

async function searchDataObject(params: SearchParams) {
  return _search<DataObjectSearchResult>('data_object', params);
}

export type ResultUnion = (
    SearchResponse<BiosampleSearchResult>
| SearchResponse<OmicsProcessingResult>
| SearchResponse<StudySearchResults>
| SearchResponse<ReadsQCResult>
| SearchResponse<MetagenomeAssembyResult>
| SearchResponse<MetagenomeAnnotationResult>
| SearchResponse<MetaproteomicAnalysisResult>
| SearchResponse<DataObjectSearchResult>);

async function search(type: entityType, params: SearchParams) {
  let results: ResultUnion;
  switch (type) {
    case 'study':
      results = await searchStudy(params);
      break;
    case 'omics_processing':
      results = await searchOmicsProcessing(params);
      break;
    case 'biosample':
      results = await searchBiosample(params);
      break;
    case 'metagenome_assembly':
      results = await searchMetagenomeAssembly(params);
      break;
    case 'metagenome_annotation':
      results = await searchMetagenomeAnnotation(params);
      break;
    case 'reads_qc':
      results = await searchReadsQC(params);
      break;
    case 'data_object':
      results = await searchDataObject(params);
      break;
    default:
      throw new Error(`Unexpected type: ${type}`);
  }
  return results;
}

async function _getById<T>(route: string, id: string): Promise<T> {
  const { data } = await client.get<T>(`${route}/${id}`);
  return data;
}

async function getBiosample(id: string): Promise<BiosampleSearchResult> {
  return _getById<BiosampleSearchResult>('biosample', id);
}

async function getStudy(id: string): Promise<StudySearchResults> {
  return _getById<StudySearchResults>('study', id);
}

async function getFacetSummary(
  type: string,
  field: string,
  conditions: Condition[],
): Promise<FacetSummaryResponse[]> {
  const path = type;
  const { data } = await client.post<{ facets: Record<string, number> }>(`${path}/facet`, {
    conditions, attribute: field,
  });
  return Object.keys(data.facets)
    .map((facetName) => ({
      facet: facetName,
      count: data.facets[facetName],
    }))
    /* TODO: Take out all these lipidomics hacks */
    .filter((facetName) => (facetName.facet !== 'Lipidomics'))
    .sort((a, b) => b.count - a.count);
}

async function getBinnedFacet<T = string | number>(
  table: entityType,
  attribute: string,
  conditions: Condition[],
  numBins: number,
  resolution: 'day' | 'week' | 'month' | 'year' = 'month',
) {
  const { data } = await client.post<BinResponse<T>>(`${table}/binned_facet`, {
    attribute,
    conditions,
    resolution,
    num_bins: numBins,
  });
  return data;
}

async function getDatabaseSummary(): Promise<DatabaseSummaryResponse> {
  const { data } = await client.get<DatabaseSummaryResponse>('summary');
  // TODO: fix this on the server
  // merge this object with summary response
  const mergeSummary = {
    biosample: {
      attributes: {
        gold_classification: {
          type: 'sankey-tree',
          count: -1,
        },
        env_broad_scale: {
          type: 'tree',
          count: -1,
        },
        env_local_scale: {
          type: 'tree',
          count: -1,
        },
        env_medium: {
          type: 'tree',
          count: -1,
        },
      },
    },
    gene_function: {
      attributes: {
        id: {
          type: 'kegg_search',
        },
      },
    },
  };
  return merge(data, mergeSummary);
}

async function getDatabaseStats() {
  const { data } = await client.get<DatabaseStatsResponse>('stats');
  return data;
}

async function getEnvironmentGeospatialAggregation(
  conditions: Condition[],
): Promise<EnvironmentGeospatialEntity[]> {
  const { data } = await client.post<EnvironmentGeospatialEntity[]>('environment/geospatial', {
    conditions,
  });
  return data;
}

async function getEnvironmentSankeyAggregation(
  conditions: Condition[],
): Promise<EnvironmentSankeyResponse> {
  const { data } = await client.post<EnvironmentSankeyResponse>('environment/sankey', {
    conditions,
  });
  return data;
}

async function getDataObjectList(
  parentType: entityType,
  parentId: string,
): Promise<DataObjectSearchResult[]> {
  const type = parentType;
  if (type === undefined) {
    return [];
  }
  const supportedTypes: entityType[] = [
    'omics_processing',
    'reads_qc',
    'metagenome_assembly',
    'metagenome_annotation',
    'metaproteomic_analysis',
  ];
  if (supportedTypes.indexOf(type) >= 0) {
    const { data } = await client.get<DataObjectSearchResult[]>(`${type}/${parentId}/outputs`);
    return data;
  }
  return [];
}

/**
 * ENVO Tree API
 */
async function getEnvoTrees() {
  const { data } = await client.get<EnvoTree>('envo/tree');
  return data;
}

/**
 * Bulk Download API
 */
async function getBulkDownloadSummary(conditions: Condition[]) {
  const { data } = await client.post<BulkDownloadSummary>('data_object/workflow_summary', {
    conditions,
  });
  return data;
}

async function getBulkDownloadAggregateSummary(conditions: Condition[], dataObjectFilter: DataObjectFilter[]) {
  const { data } = await client.post<BulkDownloadAggregateSummary>('bulk_download/summary', {
    conditions,
    data_object_filter: dataObjectFilter,
  });
  return data;
}

async function createBulkDownload(conditions: Condition[], dataObjectFilter: DataObjectFilter[]) {
  const { data } = await client.post<BulkDownload>('bulk_download', {
    conditions,
    data_object_filter: dataObjectFilter,
  });
  return {
    ...data,
    /* Construct the URL to stream download this new bulk archive */
    url: `${client.defaults.baseURL}/bulk_download/${data.id}`,
  };
}

export interface KeggTermSearchResponse {
  term: string;
  text: string;
}
async function keggSearch(query: string) {
  const { data } = await client.get('kegg/term/search', { params: { query } });
  return data.terms as KeggTermSearchResponse[];
}

/**
 * Discover facet values by text search
 */
async function textSearch(terms: string) {
  const { data } = await client.get<Condition[]>('search', { params: { terms, limit: 10 } });
  return data;
}

async function me(): Promise<string> {
  const { data } = await client.get<string>('me');
  return data;
}

async function myOrcid(): Promise<string> {
  const { data } = await client.get<string>('me/orcid');
  return data;
}

async function getAllUsers(params: SearchParams) {
  const { data } = await client.get<SearchResponse<User>>('users', {
    params: {
      limit: params.limit,
      offset: params.offset,
    },
  });
  return data;
}

async function updateUser(id: string, body: User) {
  const { data } = await client.post<User>(`users/${id}`, body);
  return data;
}

async function getAppSettings() {
  const { data } = await client.get<Record<string, boolean>>('settings');
  return data;
}

async function getSubmissionSchema() {
  const { data } = await staticFileClient.get('/submission_schema/submission_schema.json');
  return data;
}

async function getGoldEcosystemTree() {
  const { data } = await staticFileClient.get('/submission_schema/GoldEcosystemTree.json');
  return data;
}

const api = {
  createBulkDownload,
  getBinnedFacet,
  getBulkDownloadSummary,
  getBulkDownloadAggregateSummary,
  getBiosample,
  getDatabaseSummary,
  getAppSettings,
  getDatabaseStats,
  getDataObjectList,
  getEnvironmentGeospatialAggregation,
  getEnvironmentSankeyAggregation,
  getEnvoTrees,
  getFacetSummary,
  getStudy,
  getSubmissionSchema,
  getGoldEcosystemTree,
  me,
  myOrcid,
  searchBiosample,
  searchOmicsProcessing,
  searchStudy,
  searchReadsQC,
  searchMetagenomeAssembly,
  searchMetagenomeAnnotation,
  searchMetaproteomicAnalysis,
  search,
  keggSearch,
  textSearch,
  getAllUsers,
  updateUser,
};

export {
  api,
  client,
};
