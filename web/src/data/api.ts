import { merge } from 'lodash';
import axios from 'axios';

const client = axios.create({
  baseURL: process.env.VUE_APP_BASE_URL || '/api',
});

export type entityType = 'biosample'
  | 'study'
  | 'project'
  | 'reads_qc'
  | 'metagenome_assembly'
  | 'metagenome_annotation'
  | 'metaproteomic_analysis'
  | 'data_object';

export const typeMap: Map<string, entityType> = new Map([
  ['sample', 'biosample'],
  ['biosample', 'biosample'],
  ['project', 'project'],
  ['study', 'study'],
  ['reads_qc', 'reads_qc'],
  ['metagenome_assembly', 'metagenome_assembly'],
  ['metagenome_annotation', 'metagenome_annotation'],
  ['metaproteomic_analysis', 'metaproteomic_analysis'],
]);

interface BaseSearchResult {
  id: string;
  name: string;
  description: string;
  alternate_ideantifiers: string[];
  annotations: Record<string, unknown>;
}

export interface BiosampleSearchResult extends BaseSearchResult {
  project_id: string;
  depth: number;
  env_broad_scale_id: string;
  env_local_scale_id: string;
  env_medium_id: string;
  longitude: number;
  latitude: number;
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
}

export interface DataObjectSearchResult extends BaseSearchResult {
  file_size_bytes: number;
  md5_checksum: string;
}

export interface StudySearchResults extends BaseSearchResult {
  principal_investigator_websites: string[];
  publication_dois: string[];
  gold_name: string;
  gold_description: string;
  scientific_objective: string;
  add_date: string;
  mod_date: string;
  open_in_gold: string;
}

export interface ProjectSearchResult extends BaseSearchResult {
  study_id: string;
  add_date: string;
  mod_date: string;
  open_in_gold: string;
}

interface DerivedDataResult extends BaseSearchResult {
  type: string;
  git_url: string;
  started_at_time: string;
  ended_at_time: string;
  execution_resource: string;
  project_id: string;
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

export type MetaproteomicAnalysisResult = DerivedDataResult

interface AttributeSummary {
  count: number;
  type: 'string' | 'date' | 'integer' | 'float';
  min?: string | number;
  max?: string | number;
}

interface TableSummary {
  total: number;
  attributes: Record<string, AttributeSummary>;
}

export interface DatabaseSummaryResponse {
  study: TableSummary;
  project: TableSummary;
  biosample: TableSummary;
  reads_qc: TableSummary;
  metagenome_assembly: TableSummary;
  metagenome_annotation: TableSummary;
  metaproteomic_analysis: TableSummary;
  data_object: TableSummary;
}

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

interface EnvironmentGeospatialEntity {
  count: number;
  ecosystem: string;
  ecosystem_category: string;
  latitude: number;
  longitude: number;
}

export interface EnvironmentGeospatialResponse {
  [index: number]: EnvironmentGeospatialEntity;
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

export type opType = 'between' | '<' | '<=' | '>' | '>=' | '==' | '!=';
export const opMap: Record<opType, string> = {
  between: 'between',
  '<': 'less',
  '<=': 'lte',
  '>': 'greater',
  '>=': 'gte',
  '!=': 'not',
  '==': 'is',
};

export interface Condition {
  field: string;
  op: opType;
  value: string | number | [number, number];
  table: string;
}

interface SearchParams {
  offset?: number;
  limit?: number;
  conditions: Condition[];
}

export interface SearchResponse<T> {
  count: number;
  results: T[];
}

async function _search<T>(
  table: string,
  { offset = 0, limit = 100, conditions }: SearchParams,
): Promise<SearchResponse<T>> {
  const { data } = await client.post<SearchResponse<T>>(`${table}/search`,
    { conditions },
    {
      params: { offset, limit },
    });
  return data;
}

async function searchBiosample(params: SearchParams) {
  return _search<BiosampleSearchResult>('biosample', params);
}

async function searchStudy(params: SearchParams) {
  return _search<StudySearchResults>('study', params);
}

async function searchProject(params: SearchParams) {
  return _search<ProjectSearchResult>('project', params);
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
  | SearchResponse<ProjectSearchResult>
  | SearchResponse<StudySearchResults>
  | SearchResponse<ReadsQCResult>
  | SearchResponse<MetagenomeAssembyResult>
  | SearchResponse<MetagenomeAnnotationResult>
  | SearchResponse<MetaproteomicAnalysisResult>
  | SearchResponse<DataObjectSearchResult>
  | null);

async function search(type: entityType, params: SearchParams) {
  let results: ResultUnion;
  switch (type) {
    case 'study':
      results = await searchStudy(params);
      break;
    case 'project':
      results = await searchProject(params);
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

async function getFacetSummary(
  type: string,
  field: string,
  conditions: Condition[],
): Promise<FacetSummaryResponse[]> {
  const path = typeMap.get(type) || type;
  const { data } = await client.post<{ facets: Record<string, number> }>(
    `${path}/facet`, {
      conditions, attribute: field,
    },
  );
  return Object.keys(data.facets)
    .map((facetName) => ({
      facet: facetName,
      count: data.facets[facetName],
    }))
    .sort((a, b) => b.count - a.count);
}

async function getDatabaseSummary(): Promise<DatabaseSummaryResponse> {
  const { data } = await client.get<DatabaseSummaryResponse>('summary');
  // TODO: fix this on the server
  // merge this object with summary response
  const mergeSummary = {
    biosample: {
      attributes: {
        gold_classification: {
          type: 'tree',
          count: -1,
        },
      },
    },
    study: {
      attributes: {
        gold_classification: {
          type: 'tree',
          count: -1,
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
): Promise<EnvironmentGeospatialResponse> {
  const { data } = await client.post<EnvironmentGeospatialResponse>(
    'environment/geospatial', {
      conditions,
    },
  );
  return data;
}

async function getEnvironmentSankeyAggregation(
  conditions: Condition[],
): Promise<EnvironmentSankeyResponse> {
  const { data } = await client.post<EnvironmentSankeyResponse>(
    'environment/sankey', {
      conditions,
    },
  );
  return data;
}

async function getDataObjectList(
  parentType: string,
  parentId: string,
): Promise<DataObjectSearchResult[]> {
  const type = typeMap.get(parentType);
  if (type === undefined) {
    return [];
  }
  const supportedTypes: entityType[] = [
    'project',
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

async function me(): Promise<string> {
  const { data } = await client.get<string>('me');
  return data;
}

const api = {
  getDatabaseSummary,
  getDatabaseStats,
  getDataObjectList,
  getEnvironmentGeospatialAggregation,
  getEnvironmentSankeyAggregation,
  getFacetSummary,
  me,
  searchBiosample,
  searchProject,
  searchStudy,
  searchReadsQC,
  searchMetagenomeAssembly,
  searchMetagenomeAnnotation,
  searchMetaproteomicAnalysis,
  search,
};

export {
  api,
  client,
};
