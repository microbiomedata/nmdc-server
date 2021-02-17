/**
 * useActiveConditions uses a boolean ref as a clock gate
 * for some other bit of reactive state.
 *
 * https://en.wikipedia.org/wiki/Clock_gating
 */
import { cloneDeep } from 'lodash';
import { computed, Ref, watch } from '@vue/composition-api';

export default function <T> (gate: Ref<boolean>, clock: Ref<T>) {
  let clockStateCache: T = cloneDeep(clock.value);
  const gatedClock = computed(() => {
    if (gate.value) {
      return clock.value;
    }
    return clockStateCache;
  });
  watch(clock, (val) => {
    if (gate.value) {
      clockStateCache = cloneDeep(val);
    }
  });
  return gatedClock;
}
