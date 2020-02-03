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

function parseNamedThings(arr, parentType) {
  return arr.map((d) => {
    const datum = {
      id: d.id,
      name: d.name,
      description: d.description,
    };
    if (parentType !== undefined) {
      if (d.part_of !== undefined) {
        [datum[`${parentType}_id`]] = d.part_of;
      } else {
        datum[`${parentType}_id`] = 'None';
      }
    }
    d.annotations.forEach((a) => {
      datum[a.has_characteristic.name] = parseAnnotation(a);
    });
    return datum;
  });
}

function idMap(items) {
  const itemMap = {};
  for (let i = 0; i < items.length; i += 1) {
    const item = items[i];
    itemMap[item.id] = item;
  }
  return itemMap;
}

function meetsCondition(d, condition) {
  if (condition.op === '==') {
    if (Array.isArray(d[condition.field])) {
      return d[condition.field].includes(condition.value);
    }
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

export default class DataAPI {
  constructor() {
    this.sample = parseNamedThings(biosamples, 'project');
    this.sampleMap = idMap(this.sample);
    this.project = parseNamedThings(projects, 'study');
    this.projectMap = idMap(this.project);
    this.study = parseNamedThings(studies);
    this.studyMap = idMap(this.study);
    this.file = [{ id: '0', name: 'Test' }];
    this.fileMap = idMap(this.file);
    this.backPopulate('study', 'project');
    this.backPopulate('project', 'sample');

    // Build transitive link between sample/study through project
    for (let i = 0; i < this.study.length; i += 1) {
      this.study[i].sample_id = [];
    }
    for (let i = 0; i < this.sample.length; i += 1) {
      const s = this.sample[i];
      if (this.projectMap[s.project_id]) {
        s.study_id = this.projectMap[s.project_id].study_id;
        if (this.studyMap[s.study_id]) {
          this.studyMap[s.study_id].sample_id.push(s.id);
        }
      }
    }
    for (let i = 0; i < this.sample.length; i += 1) {
      const s = this.sample[i];
      s.jgi_gold_link = `https://gold.jgi.doe.gov/biosample?id=${s.id}`;
    }
    for (let i = 0; i < this.project.length; i += 1) {
      const p = this.project[i];
      p.jgi_gold_link = `https://gold.jgi.doe.gov/project?id=${p.id}`;
    }
    for (let i = 0; i < this.study.length; i += 1) {
      const s = this.study[i];
      s.jgi_gold_link = `https://gold.jgi.doe.gov/study?id=${s.id}`;
    }
  }

  backPopulate(parentType, childType) {
    const parentMap = this[`${parentType}Map`];
    const parents = this[parentType];
    const children = this[childType];
    parents.forEach((p) => {
      parentMap[p.id] = p;
      // eslint-disable-next-line no-param-reassign
      p[`${childType}_id`] = [];
    });
    children.forEach((c) => {
      const parent = parentMap[c[`${parentType}_id`]];
      if (parent !== undefined) {
        parent[`${childType}_id`].push(c.id);
      }
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
