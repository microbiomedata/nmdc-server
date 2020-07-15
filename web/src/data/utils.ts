import { Condition } from './api';

function removeCondition(conditions: Condition[], c: Condition) {
  const copy = conditions.slice();
  const foundIndex = copy.findIndex((cond) => (
    cond.field === c.field && cond.op === c.op && cond.value === c.value));
  if (foundIndex >= 0) {
    copy.splice(foundIndex, 1);
  }
  return copy;
}

export default removeCondition;
