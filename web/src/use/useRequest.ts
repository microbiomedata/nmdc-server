import { reactive, toRefs } from 'vue';

/**
 * Hook to manage the state of an async request, including loading, error, and count of successful calls.
 */
export default function useRequest() {
  const state = reactive({
    loading: false, // indicates request in progress
    error: null as string | null, // indicates request failure
    count: 0, // indicates number of successful calls
  });

   /**
    * Helper function to wrap an async request and manage loading and error state.
    * Callers of this function can check state.error to determine if an error occurred.
    * If state.error is null, then an error has not (yet) occurred.
    * @param func 
    * @returns 
    */
  async function request<T>(func: () => Promise<T>) {
    try {
      state.loading = true;
      state.error = null;
      const val = await func();
      state.count += 1;
      state.loading = false;
      return val;
    } catch (err) {
      state.loading = false;
      state.error = String(err);
      return null;
    }
  }

  function reset() {
    state.loading = false;
    state.error = null;
    state.count = 0;
  }

  return {
    ...toRefs(state),
    state,
    request,
    reset,
  };
}
