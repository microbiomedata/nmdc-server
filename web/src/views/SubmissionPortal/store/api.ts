import { AxiosResponse } from 'axios';
import { client, SearchParams } from '@/data/api';
import {
  LockOperationResult,
  MetadataSubmission,
  MetadataSubmissionRecord,
  MetadataSuggestion,
  MetadataSuggestionRequest,
  NmdcAddress,
  PaginatedResponse,
  SuggestionType,
} from '@/views/SubmissionPortal/types';

function addressToString(address: NmdcAddress): string {
  let result = '';
  const contactAndStreetInfo = [address.name, address.email, address.phone, address.line1, address.line2];
  contactAndStreetInfo.forEach((line) => {
    if (line.trim()) {
      result += `${line.trim()}\n`;
    }
  });
  const stateAndZip = `${address.state} ${address.postalCode}`;
  const joinString = (address.city.trim() && stateAndZip.trim()) ? ', ' : '';
  result += [address.city, stateAndZip].join(joinString);
  return result;
}

async function createRecord(record: MetadataSubmission) {
  const resp = await client.post<
    MetadataSubmissionRecord,
    AxiosResponse<MetadataSubmissionRecord>,
    Partial<MetadataSubmissionRecord>
  >('metadata_submission', {
    metadata_submission: record,
    source_client: 'submission_portal',
  });
  return resp.data;
}

async function updateRecord(id: string, record: Partial<MetadataSubmission>, status?: string, permissions?: Record<string, string>) {
  const resp = await client.patch<MetadataSubmissionRecord>(`metadata_submission/${id}`, {
    metadata_submission: record,
    status,
    permissions,
  });
  return { data: resp.data, httpStatus: resp.status };
}

async function listRecords(params: SearchParams) {
  const resp = await client.get<PaginatedResponse<MetadataSubmissionRecord>>('metadata_submission', {
    params: {
      limit: params.limit,
      offset: params.offset,
      column_sort: params.sortColumn,
      sort_order: params.sortOrder,
    },
  });
  return resp.data;
}

async function getRecord(id: string) {
  const resp = await client.get<MetadataSubmissionRecord>(`metadata_submission/${id}`);
  return resp.data;
}

async function lockSubmission(id: string) {
  const resp = await client.put<LockOperationResult>(`metadata_submission/${id}/lock`);
  return resp.data;
}

async function unlockSubmission(id: string) {
  const resp = await client.put<LockOperationResult>(`metadata_submission/${id}/unlock`);
  return resp.data;
}

async function deleteSubmission(id: string) {
  const resp = await client.delete(`metadata_submission/${id}`);
  return resp.data;
}

async function getMetadataSuggestions(data: MetadataSuggestionRequest[], type: SuggestionType) {
  let endpoint = 'metadata_submission/suggest';
  if (type === SuggestionType.ADDITIONS) {
    endpoint += '?types=add';
  } else if (type === SuggestionType.REPLACEMENTS) {
    endpoint += '?types=replace';
  }
  const resp = await client.post<
    MetadataSuggestion[],
    AxiosResponse<MetadataSuggestion[]>,
    MetadataSuggestionRequest[]
  >(endpoint, data);
  return resp.data;
}

export {
  addressToString,
  createRecord,
  getRecord,
  listRecords,
  updateRecord,
  lockSubmission,
  unlockSubmission,
  deleteSubmission,
  getMetadataSuggestions,
};
