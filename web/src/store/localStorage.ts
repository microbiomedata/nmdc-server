const QUERY_STATE_KEY = 'storage.queryState';
const REFRESH_TOKEN_KEY = 'storage.refreshToken';

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

export {
  getQueryState,
  setQueryState,
  clearQueryState,
  getRefreshToken,
  setRefreshToken,
  clearRefreshToken,
};
