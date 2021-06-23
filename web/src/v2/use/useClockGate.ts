/**
 * useClickGate uses a boolean ref as a clock gate
 * for some other bit of reactive state.  This isn't
 * actually realated to time, it's just the name for this
 * kind of boolean logic.
 *
 * In other words, useClockGate reutrns a reactive var
 * that only updates when the clock is true. The trick is to
 * cache changes that happen while the clock is false so the
 * state can change if clock changes.
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
