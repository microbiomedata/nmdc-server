import axios from 'axios';

const client = axios.create({
  baseURL: process.env.VUE_APP_BASE_URL || '/api',
});

export type entityType = 'biosample' | 'study' | 'project';
export const typeMap: Map<string, entityType> = new Map([
  ['sample', 'biosample'],
  ['biosample', 'biosample'],
  ['project', 'project'],
  ['study', 'study'],
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

interface AttributeSummary {
  total: number;
  attributes: Record<string, number>;
}

export interface DatabaseSummaryResponse {
  study: AttributeSummary;
  project: AttributeSummary;
  biosample: AttributeSummary;
}

export interface FacetSummaryResponse {
  facet: string;
  count: number;
}

export interface Condition {
  field: string;
  op: string;
  value: string;
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

export type ResultUnion = (SearchResponse<BiosampleSearchResult>
  | SearchResponse<ProjectSearchResult>
  | SearchResponse<StudySearchResults> | null);

async function searchCount(type: entityType, params: SearchParams): Promise<number> {
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
    default:
      throw new Error(`Unexpected type: ${type}`);
  }
  return results.count;
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

async function getDatabaseSummary() {
  const { data } = await client.get<DatabaseSummaryResponse>('summary');
  return data;
}

const api = {
  getDatabaseSummary,
  getFacetSummary,
  searchBiosample,
  searchProject,
  searchStudy,
  searchCount,
};

export {
  api,
  client,
};
