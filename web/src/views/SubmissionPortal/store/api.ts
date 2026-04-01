import { AxiosResponse } from 'axios';
import { client, SearchParams } from '@/data/api';
import {
  AllowedStatusTransitions,
  LockOperationResult,
  MetadataSubmission,
  MetadataSubmissionRecord,
  MetadataSubmissionRecordSlim,
  MetadataSuggestion,
  MetadataSuggestionRequest,
  NmdcAddress,
  PaginatedResponse,
  SignedUploadUrlRequest,
  SignedUrl,
  SubmissionImageType,
  SuggestionType,
  UploadCompleteRequest,
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

async function createRecord(record: MetadataSubmission, isTestSubmission: boolean) {
  const resp = await client.post<
    MetadataSubmissionRecord,
    AxiosResponse<MetadataSubmissionRecord>,
    Partial<MetadataSubmissionRecord>
  >('metadata_submission', {
    metadata_submission: record,
    source_client: 'submission_portal',
    is_test_submission: isTestSubmission,
  });
  return resp.data;
}

async function updateRecord(id: string, record: Partial<MetadataSubmission>, permissions?: Record<string, string>) {
  const resp = await client.patch<MetadataSubmissionRecord>(`metadata_submission/${id}`, {
    metadata_submission: record,
    permissions,
  });
  return resp.data;
}

async function updateSubmissionStatus(submission_id: string, newStatus: string) {
  const resp = await client.patch<MetadataSubmissionRecord>(`metadata_submission/${submission_id}/status`, {
    status: newStatus,
  });
  return resp.data;
}

async function getAllStatusTransitions() {
  const resp = await client.get<AllowedStatusTransitions>('status_transitions', {
  });
  return resp.data;
}

async function addSubmissionRole(submission_id: string, orcid: string, role: string) {
  const resp = await client.post<MetadataSubmissionRecord>(`metadata_submission/${submission_id}/role`, {
    orcid,
    role,
  });
  return resp.data;
}

async function listRecords(searchParams: SearchParams, isTestFilter: boolean | null, searchText: string) {
  const params: Record<string, any> = {
    limit: searchParams.limit,
    offset: searchParams.offset,
    column_sort: searchParams.sortColumn,
    sort_order: searchParams.sortOrder,
  };
  if (isTestFilter !== null) {
    params.is_test_submission_filter = isTestFilter;
  }
  if (searchText !== '') {
    params.search_text = searchText;
  }
  const resp = await client.get<PaginatedResponse<MetadataSubmissionRecordSlim>>(
    'metadata_submission/slim',
    { params },
  );
  return resp.data;
}

async function getRecord(id: string) {
  const resp = await client.get<MetadataSubmissionRecord>(`metadata_submission/${id}`);
  return resp.data;
}

async function getSubmissionStatus(id: string) {
  const resp = await client.get<{ status: string }>(`metadata_submission/${id}/status`);
  return resp.data.status;
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

async function getMetadataSuggestionsFromStudyDetails(submissionId: string) {
  const resp = await client.post<MetadataSuggestion[]>(`metadata_submission/${submissionId}/study-suggest`);
  return resp.data;
}

async function generateSignedUploadUrl(submissionId: string, file: File): Promise<SignedUrl> {
  const endpoint = `metadata_submission/${submissionId}/image/signed_upload_url`;
  const resp = await client.post<SignedUrl>(endpoint, {
    file_name: file.name,
    file_size: file.size,
    content_type: file.type,
  } as SignedUploadUrlRequest);
  return resp.data;
}

async function setSubmissionImage(
  submissionId: string,
  file: File,
  blobName: string,
  imageType?: SubmissionImageType,
): Promise<MetadataSubmissionRecord> {
  let endpoint = `metadata_submission/${submissionId}/image`;
  if (imageType) {
    endpoint += `/${imageType}`;
  }
  const resp = await client.post<MetadataSubmissionRecord>(endpoint, {
    object_name: blobName,
    file_size: file.size,
    content_type: file.type,
  } as UploadCompleteRequest);
  return resp.data;
}

async function deleteSubmissionImage(submissionId: string, imageType: SubmissionImageType, imageName?: string): Promise<void> {
  let endpoint = `metadata_submission/${submissionId}/image/${imageType}`;
  if (imageName) {
    endpoint += `?image_name=${imageName}`;
  }
  await client.delete<MetadataSubmissionRecord>(endpoint);
}

interface FieldValidationResponse {
  valid: boolean;
  value?: string;
  ontology_id?: string;
  errors: string[];
  warnings: string[];
}

interface SampleTriadValidationResponse {
  sample_index: number;
  sample_name?: string;
  env_broad_scale: FieldValidationResponse;
  env_local_scale: FieldValidationResponse;
  env_medium: FieldValidationResponse;
  cross_field_errors: string[];
}

export interface SubmissionTriadValidationResponse {
  submission_id: string;
  valid: boolean;
  sample_results: Record<string, SampleTriadValidationResponse[]>;
  error_count: number;
  warning_count: number;
}

async function validateEnvTriad(submissionId: string): Promise<SubmissionTriadValidationResponse> {
  const resp = await client.post<SubmissionTriadValidationResponse>(
    `metadata_submission/${submissionId}/validate_env_triad`,
  );
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
  getMetadataSuggestionsFromStudyDetails,
  generateSignedUploadUrl,
  getAllStatusTransitions,
  setSubmissionImage,
  deleteSubmissionImage,
  updateSubmissionStatus,
  addSubmissionRole,
  getSubmissionStatus,
  validateEnvTriad,
};
