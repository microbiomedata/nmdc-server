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

class StoredMap<T> {
  private readonly storageKey: string;

  constructor(storageKey: string) {
    this.storageKey = storageKey;
  }

  get(key: string): T {
    const str = window.localStorage.getItem(this.storageKey);
    const obj = str ? JSON.parse(str) : {};
    return obj[key];
  }

  set(key: string, value: T) {
    const str = window.localStorage.getItem(this.storageKey);
    const obj = str ? JSON.parse(str) : {};
    obj[key] = value;
    window.localStorage.setItem(this.storageKey, JSON.stringify(obj));
  }
}

const rejectedSuggestions = new StoredMap<string[]>(REJECTED_SUGGESTIONS);
const pendingSuggestions = new StoredMap<MetadataSuggestion[]>(PENDING_SUGGESTIONS);

function getRejectedSuggestions(schemaClassName: string): string[] {
  return rejectedSuggestions.get(schemaClassName) || [];
}

function setRejectedSuggestions(schemaClassName: string, suggestions: string[]) {
  rejectedSuggestions.set(schemaClassName, suggestions);
}

function getPendingSuggestions(schemaClassName: string) {
  return pendingSuggestions.get(schemaClassName) || [];
}

function setPendingSuggestions(schemaClassName: string, suggestions: MetadataSuggestion[]) {
  return pendingSuggestions.set(schemaClassName, suggestions);
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
