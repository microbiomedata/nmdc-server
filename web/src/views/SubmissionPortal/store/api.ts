import { client, SearchParams } from '@/data/api';
import {
  AllowedStatusTransitions,
  LockOperationResult,
  MetadataSuggestion,
  MetadataSuggestionRequest,
  NmdcAddress,
  PaginatedResponse,
  SignedUploadUrlRequest,
  SignedUrl,
  SubmissionImageType,
  SubmissionMetadata,
  SubmissionMetadataCreate,
  SubmissionMetadataPatch,
  SubmissionMetadataSlim,
  SubmissionSampleSet,
  SubmissionSampleSetCreate,
  SubmissionSampleSetListItem,
  SubmissionSampleSetPatch,
  SubmissionSampleSetStatusPatch,
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

async function createSubmission(submission: SubmissionMetadataCreate) {
  const resp = await client.post<
    SubmissionMetadata,
    SubmissionMetadataCreate
  >('metadata_submission', submission);
  return resp.data;
}

async function updateSubmission(id: string, submission: SubmissionMetadataPatch) {
  const resp = await client.patch<SubmissionMetadata>(`metadata_submission/${id}`, submission);
  return resp.data;
}

async function createSubmissionSampleSet(submissionId: string, sampleSet: SubmissionSampleSetCreate) {
  const resp = await client.post<SubmissionSampleSet>(`metadata_submission/${submissionId}/sample_set`, sampleSet);
  return resp.data;
}

async function updateSubmissionSampleSet(sampleSetId: string, sampleSet: SubmissionSampleSetPatch) {
  const resp = await client.patch<SubmissionSampleSet>(`metadata_submission/sample_set/${sampleSetId}`, sampleSet);
  return resp.data;
}

async function updateSubmissionSampleSetStatus(sampleSetId: string, body: SubmissionSampleSetStatusPatch) {
  const resp = await client.patch<SubmissionSampleSet>(`metadata_submission/sample_set/${sampleSetId}/status`, body);
  return resp.data;
}

async function getAllStatusTransitions() {
  const resp = await client.get<AllowedStatusTransitions>(
    'status_transitions',
    {
      cache: { enabled: true }
    }
  );
  return resp.data;
}

async function addSubmissionRole(submission_id: string, orcid: string, role: string) {
  const resp = await client.post<SubmissionMetadata>(`metadata_submission/${submission_id}/role`, {
    orcid,
    role,
  });
  return resp.data;
}

async function listSubmissions(searchParams: SearchParams, isTestFilter: boolean | null, searchText: string) {
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
  const resp = await client.get<PaginatedResponse<SubmissionMetadataSlim>>(
    'metadata_submission/slim',
    { params },
  );
  return resp.data;
}

async function getSubmission(id: string) {
  const resp = await client.get<SubmissionMetadata>(`metadata_submission/${id}`);
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
): Promise<SubmissionMetadata> {
  const endpoint = `metadata_submission/${submissionId}/image/${imageType ?? 'study_images'}`;
  const resp = await client.post<SubmissionMetadata>(endpoint, {
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
  await client.delete<SubmissionMetadata>(endpoint);
}

async function listSubmissionSampleSets(submissionId: string) {
  const resp = await client.get<SubmissionSampleSetListItem[]>(`metadata_submission/${submissionId}/sample_set`);
  return resp.data;
}

async function getSampleSet(sampleSetId: string) {
  const resp = await client.get<SubmissionSampleSet>(`metadata_submission/sample_set/${sampleSetId}`);
  return resp.data;
}

export {
  addressToString,
  createSubmission,
  getSubmission,
  listSubmissions,
  updateSubmission,
  createSubmissionSampleSet,
  updateSubmissionSampleSet,
  updateSubmissionSampleSetStatus,
  lockSubmission,
  unlockSubmission,
  deleteSubmission,
  getMetadataSuggestions,
  getMetadataSuggestionsFromStudyDetails,
  generateSignedUploadUrl,
  getAllStatusTransitions,
  setSubmissionImage,
  deleteSubmissionImage,
  addSubmissionRole,
  listSubmissionSampleSets,
  getSampleSet,
};
