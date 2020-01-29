import moment from 'moment';
import { isObject } from 'lodash';

import biosamples from './biosample.json';
import projects from './project.json';
import studies from './study.json';

function parseAnnotation(a) {
  const value = a.has_raw_value;
  if (a.has_characteristic.name.includes('date')) {
    return moment(value, 'DD-MMM-YY hh.mm.ss.SSSSSSSSS a').valueOf();
  }
  return value;
}

function parseNamedThings(arr) {
  return arr.map((d) => {
    const datum = {
      id: d.id,
      name: d.name,
      description: d.description,
    };
    if (d.part_of !== undefined) {
      [datum.part_of] = d.part_of;
    }
    d.annotations.forEach((a) => {
      datum[a.has_characteristic.name] = parseAnnotation(a);
    });
    return datum;
  });
}

function meetsCondition(d, condition) {
  if (condition.op === '==') {
    return d[condition.field] === condition.value;
  }
  if (condition.op === '<') {
    return d[condition.field] < condition.value;
  }
  if (condition.op === '>') {
    return d[condition.field] > condition.value;
  }
  if (condition.op === '<=') {
    return d[condition.field] <= condition.value;
  }
  if (condition.op === '>=') {
    return d[condition.field] >= condition.value;
  }
  return false;
}

function groupConditionsByField(conditions) {
  const fieldConditions = {};
  conditions.forEach((cond) => {
    if (fieldConditions[cond.field] === undefined) {
      fieldConditions[cond.field] = [];
    }
    fieldConditions[cond.field].push(cond);
  });
  return Object.values(fieldConditions);
}

function meetsAllConditions(d, fieldConditions) {
  for (let i = 0; i < fieldConditions.length; i += 1) {
    let anyCondTrue = false;
    for (let j = 0; j < fieldConditions[i].length; j += 1) {
      if (meetsCondition(d, fieldConditions[i][j])) {
        anyCondTrue = true;
      }
    }
    if (!anyCondTrue) {
      return false;
    }
  }
  return true;
}

function backPopulate(parents, children, field) {
  const parentMap = {};
  parents.forEach((p) => {
    parentMap[p.id] = p;
    // eslint-disable-next-line no-param-reassign
    p[field] = [];
  });
  children.forEach((c) => {
    if (parentMap[c.part_of] !== undefined) {
      parentMap[c.part_of][field].push(c);
    }
  });
}

export default class DataAPI {
  constructor() {
    this.sample = parseNamedThings(biosamples);
    this.project = parseNamedThings(projects);
    this.study = parseNamedThings(studies);
    this.file = [{ id: '0', name: 'Test' }];
    backPopulate(this.study, this.project, 'project');
    backPopulate(this.project, this.sample, 'sample');
    this.sample.forEach((s) => {
      // eslint-disable-next-line no-param-reassign
      s.part_of = this.project.find((p) => p.id === s.part_of);
    });
    this.project.forEach((p) => {
      // eslint-disable-next-line no-param-reassign
      p.part_of = this.study.find((s) => s.id === p.part_of);
    });
  }

  primitiveFields(type) {
    return this.fields(type).filter((field) => !isObject(this[type][0][field]));
  }

  fields(type) {
    return Object.keys(this[type][0]);
  }

  count(type) {
    return this[type].length;
  }

  query(type, conditions) {
    return this[type].filter((d) => meetsAllConditions(d, groupConditionsByField(conditions)));
  }

  facetSummary(type, field, conditions) {
    const valueMap = new Map();
    // Don't filter by conditions that match the field.
    // This seems odd, but enables checking multiple boxes
    // for the same field as an "or".
    const paredConditions = groupConditionsByField(
      conditions.filter((cond) => cond.field !== field),
    );
    this[type].forEach((d) => {
      if (d[field] === undefined) {
        return;
      }
      if (valueMap.get(d[field]) === undefined) {
        valueMap.set(d[field], { all: 0, count: 0 });
      }
      valueMap.get(d[field]).all += 1;
      if (meetsAllConditions(d, paredConditions)) {
        valueMap.get(d[field]).count += 1;
      }
    });
    return [...valueMap.keys()]
      .map((value) => ({ value, ...valueMap.get(value) }))
      .sort((a, b) => b.all - a.all);
  }
}
