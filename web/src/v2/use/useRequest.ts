/**
 * useRequest adds loading and error state to any sort of
 * API request you might need.
 */

import { ref } from '@vue/composition-api';

export default function useRequest() {
  const loading = ref(false);
  const error = ref(null);

  async function request<T>(func: () => Promise<T>) {
    try {
      loading.value = true;
      error.value = null;
      const val = await func();
      loading.value = false;
      return val;
    } catch (err) {
      loading.value = false;
      error.value = err;
      throw err;
    }
  }

  return {
    loading,
    error,
    request,
  };
}
