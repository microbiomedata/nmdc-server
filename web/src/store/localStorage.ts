import { MetadataSuggestion } from '@/views/SubmissionPortal/types';

const QUERY_STATE_KEY = 'storage.queryState';
const REFRESH_TOKEN_KEY = 'storage.refreshToken';
const REJECTED_SUGGESTIONS = 'storage.rejectedSuggestions';
const PENDING_SUGGESTIONS = 'storage.pendingSuggestions';

function getQueryState() {
  const state = window.localStorage.getItem(QUERY_STATE_KEY);
  return state ? JSON.parse(state) : null;
}

function setQueryState(state: any) {
  return window.localStorage.setItem(QUERY_STATE_KEY, JSON.stringify(state));
}

function clearQueryState() {
  return window.localStorage.removeItem(QUERY_STATE_KEY);
}

function getRefreshToken() {
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setRefreshToken(token: string) {
  return window.localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

function clearRefreshToken() {
  return window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function getRejectedSuggestions(): string[] {
  const suggestions = window.localStorage.getItem(REJECTED_SUGGESTIONS);
  return suggestions ? JSON.parse(suggestions) : [];
}

function setRejectedSuggestions(suggestions: string[]) {
  return window.localStorage.setItem(REJECTED_SUGGESTIONS, JSON.stringify(suggestions));
}

function getPendingSuggestions(schemaClassName: string) {
  const suggestionsStr = window.localStorage.getItem(PENDING_SUGGESTIONS);
  const suggestionsObj = suggestionsStr ? JSON.parse(suggestionsStr) : {};
  return suggestionsObj[schemaClassName] || [];
}

function setPendingSuggestions(schemaClassName: string, suggestions: MetadataSuggestion[]) {
  const pendingSuggestions = window.localStorage.getItem(PENDING_SUGGESTIONS);
  const pendingSuggestionsObj = pendingSuggestions ? JSON.parse(pendingSuggestions) : {};
  pendingSuggestionsObj[schemaClassName] = suggestions;
  window.localStorage.setItem(PENDING_SUGGESTIONS, JSON.stringify(pendingSuggestionsObj));
}

export {
  getQueryState,
  setQueryState,
  clearQueryState,
  getRefreshToken,
  setRefreshToken,
  clearRefreshToken,
  getRejectedSuggestions,
  setRejectedSuggestions,
  getPendingSuggestions,
  setPendingSuggestions,
};
