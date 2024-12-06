import { AxiosResponse } from 'axios';
import { client, SearchParams, User } from '@/data/api';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';

interface NmdcAddress {
  name: string;
  email: string;
  phone: string;
  line1: string;
  line2: string;
  city: string;
  state: string;
  postalCode: string;
}

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

interface MetadataSubmission {
  packageName: keyof typeof HARMONIZER_TEMPLATES;
  contextForm: any;
  addressForm: any;
  templates: string[];
  studyForm: any;
  multiOmicsForm: any;
  sampleData: Record<string, any[]>;
}

interface MetadataSubmissionRecord {
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
}

interface PaginatedResponse<T> {
  count: number;
  results: T[];
}

interface LockOperationResult {
  success: boolean;
  message: string
  locked_by?: User | null;
  lock_updated?: string | null;
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

export {
  NmdcAddress,
  addressToString,
  MetadataSubmission,
  MetadataSubmissionRecord,
  createRecord,
  getRecord,
  listRecords,
  updateRecord,
  lockSubmission,
  unlockSubmission,
  deleteSubmission,
};
