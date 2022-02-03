import { reactive, toRefs } from '@vue/composition-api';

export default function useRequest<T>(outer?: () => Promise<T>) {
  const state = reactive({
    loading: false, // indicates request in progress
    error: null as string | null, // indicates request failure
    count: 0, // indicates number of successful calls
  });

  async function request(inner?: () => Promise<T>) {
    if (!(outer || inner)) {
      throw new Error('Must provide a request function');
    }
    try {
      state.loading = true;
      state.error = null;
      state.count += 1;
      // @ts-ignore typescript doesn't understand mutual exclusivity from assertion above.
      const val = await (outer || inner)();
      state.loading = false;
      return val;
    } catch (err) {
      state.loading = false;
      state.error = String(err);
      throw err;
    }
  }

  async function reset() {
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
