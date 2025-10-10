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

/**
 * A class to simplify storing and retrieving objects that are approximately like a Map<string, T> in localStorage.
 */
class StoredMap<T> {
  private readonly storageKey: string;

  /**
   * Create a new StoredMap.
   * @param storageKey The key to use in localStorage.
   */
  constructor(storageKey: string) {
    this.storageKey = storageKey;
  }

  private static joinKeys(keys: string | string[]): string {
    return Array.isArray(keys) ? keys.join('__') : keys;
  }

  /**
   * Get the value associated with the given key from the stored map.
   * @param key
   */
  get(key: string | string[]): T {
    const str = window.localStorage.getItem(this.storageKey);
    const obj = str ? JSON.parse(str) : {};
    return obj[StoredMap.joinKeys(key)];
  }

  /**
   * Set the value associated with the given key in the stored map.
   * @param key
   * @param value
   */
  set(key: string | string[], value: T) {
    const str = window.localStorage.getItem(this.storageKey);
    const obj = str ? JSON.parse(str) : {};
    obj[StoredMap.joinKeys(key)] = value;
    window.localStorage.setItem(this.storageKey, JSON.stringify(obj));
  }
}

const rejectedSuggestions = new StoredMap<string[]>(REJECTED_SUGGESTIONS);
const pendingSuggestions = new StoredMap<MetadataSuggestion[]>(PENDING_SUGGESTIONS);

/**
 * Get the stored rejected suggestions for a given submission and schema class.
 * @param submissionId
 * @param schemaClassName
 */
function getRejectedSuggestions(submissionId: string, schemaClassName: string): string[] {
  return rejectedSuggestions.get([submissionId, schemaClassName]) || [];
}

/**
 * Set the stored rejected suggestions for a given submission and schema class.
 * @param submissionId
 * @param schemaClassName
 * @param suggestions
 */
function setRejectedSuggestions(submissionId: string, schemaClassName: string, suggestions: string[]) {
  rejectedSuggestions.set([submissionId, schemaClassName], suggestions);
}

/**
 * Get the stored pending suggestions for a given submission and schema class.
 * @param submissionId
 * @param schemaClassName
 */
function getPendingSuggestions(submissionId: string, schemaClassName: string) {
  return pendingSuggestions.get([submissionId, schemaClassName]) || [];
}

/**
 * Set the stored pending suggestions for a given submission and schema class.
 * @param submissionId
 * @param schemaClassName
 * @param suggestions
 */
function setPendingSuggestions(submissionId: string, schemaClassName: string, suggestions: MetadataSuggestion[]) {
  return pendingSuggestions.set([submissionId, schemaClassName], suggestions);
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
