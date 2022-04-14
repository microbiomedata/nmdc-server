import axios from 'axios';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';

const client = axios.create({
  baseURL: process.env.VUE_APP_BASE_URL || '/api',
});

interface MetadataSubmission {
  template: keyof typeof HARMONIZER_TEMPLATES;
  studyForm: any;
  multiOmicsForm: any;
  sampleData: any[][];
  [key: string]: any;
}

interface MetadataSubmissionRecord {
  id: string;
  author_orcid: string;
  created: string;
  metadata_submission: MetadataSubmission;
  status: string;
}

interface PaginatedResponse<T> {
  count: number;
  results: T[];
}

async function createRecord(record: MetadataSubmission) {
  const resp = await client.post<MetadataSubmissionRecord>('metadata_submission', {
    metadata_submission: record,
  });
  return resp.data;
}

async function updateRecord(id: string, record: MetadataSubmission, status?: string) {
  const resp = await client.patch<MetadataSubmissionRecord>(`metadata_submission/${id}`, {
    metadata_submission: record,
    status,
  });
  return resp.data;
}

async function listRecords() {
  const resp = await client.get<PaginatedResponse<MetadataSubmissionRecord>>('metadata_submission');
  return resp.data;
}

async function getRecord(id: string) {
  const resp = await client.get<MetadataSubmissionRecord>(`metadata_submission/${id}`);
  return resp.data;
}

export {
  MetadataSubmission,
  MetadataSubmissionRecord,
  createRecord,
  getRecord,
  listRecords,
  updateRecord,
};
