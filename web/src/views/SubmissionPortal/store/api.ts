import { AxiosResponse } from 'axios';
import { client, SearchParams } from '@/data/api';
import {
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

async function updateRecord(id: string, record: Partial<MetadataSubmission>, status?: string, permissions?: Record<string, string>) {
  const resp = await client.patch<MetadataSubmissionRecord>(`metadata_submission/${id}`, {
    metadata_submission: record,
    status,
    permissions,
  });
  return { data: resp.data, httpStatus: resp.status };
}

async function listRecords(searchParams: SearchParams, isTestFilter: boolean | null) {
  const params: Record<string, any> = {
    limit: searchParams.limit,
    offset: searchParams.offset,
    column_sort: searchParams.sortColumn,
    sort_order: searchParams.sortOrder,
  };
  if (isTestFilter !== null) {
    params.is_test_submission_filter = isTestFilter;
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

async function requestRecordReopened(id: string) {
  const resp = await client.post<MetadataSubmissionRecord>(
    `metadata_submission/${id}/request_reopen`,
    {},
  );
  return { data: resp.data, httpStatus: resp.status };
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
  generateSignedUploadUrl,
  setSubmissionImage,
  deleteSubmissionImage,
  requestRecordReopened,
};
