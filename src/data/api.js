import moment from 'moment';
import { isObject } from 'lodash';
// import filesize from 'filesize';

import biosamples from './biosample.json';
import projects from './omics_processing.json';
import studies from './study.json';
import dataObjects from './data_objects.json';
import studyAdditional from './study_additional.json';

function parseAnnotation(a) {
  const value = a.has_raw_value;
  if (a.has_characteristic.name.includes('date')) {
    return moment(value, 'DD-MMM-YY hh.mm.ss.SSSSSSSSS a').valueOf();
  }
  return value;
}

function parseNamedThings(arr, { parentType = null, outputType = null } = {}) {
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
    if (outputType !== undefined) {
      if (d.has_output !== undefined) {
        datum[`${outputType}_id`] = d.has_output;
      } else {
        datum[`${outputType}_id`] = [];
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

class DataAPI {
  constructor() {
    this.sample = parseNamedThings(biosamples, { parentType: 'project' });
    this.sample_map = idMap(this.sample);
    this.project = parseNamedThings(projects, { parentType: 'study', outputType: 'data_object' });
    this.project_map = idMap(this.project);
    this.study = parseNamedThings(studies);
    this.study_map = idMap(this.study);
    this.data_object = parseNamedThings(dataObjects);
    this.data_object_map = idMap(this.data_object);
    this.backPopulate('study', 'project');
    this.backPopulate('project', 'sample');
    this.forwardPopulate('project', 'data_object');
    this.transitivePopulate('study', 'project', 'sample');
    this.transitivePopulate('study', 'project', 'data_object');
    this.siblingPopulate('project', 'sample', 'data_object');
    this.siblingPopulate('project', 'data_object', 'sample');

    // Construct web links
    for (let i = 0; i < this.sample.length; i += 1) {
      const s = this.sample[i];
      s.open_in_gold = `https://gold.jgi.doe.gov/biosample?id=${s.id}`;
    }
    for (let i = 0; i < this.project.length; i += 1) {
      const p = this.project[i];
      p.open_in_gold = `https://gold.jgi.doe.gov/project?id=${p.id}`;
    }
    for (let i = 0; i < this.study.length; i += 1) {
      const s = this.study[i];
      s.open_in_gold = `https://gold.jgi.doe.gov/study?id=${s.id}`;
    }

    // Project description
    for (let i = 0; i < this.project.length; i += 1) {
      const p = this.project[i];
      p.description = p.omics_type;
    }

    this.importAdditionalStudyFields();
  }

  importAdditionalStudyFields() {
    studyAdditional.forEach((d) => {
      const s = this.study_map[d.id];
      Object.assign(s, d);
      s.gold_description = s.description;
      s.gold_name = s.name;
      s.name = d.proposal_title;
      s.description = `Principal investigator: ${s.principal_investigator_name}`;
    });
  }

  backPopulate(parentType, childType) {
    const parentMap = this[`${parentType}_map`];
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

  forwardPopulate(parentType, childType) {
    const childMap = this[`${childType}_map`];
    const parents = this[parentType];
    parents.forEach((p) => {
      p[`${childType}_id`].forEach((c) => {
        const child = childMap[c];
        child[`${parentType}_id`] = p.id;
      });
    });
  }

  siblingPopulate(parent, child1, child2) {
    // Build transitive link between child1/child2 through parent
    const parentMap = {};
    for (let i = 0; i < this[child1].length; i += 1) {
      const c1 = this[child1][i];
      if (!parentMap[c1[`${parent}_id`]]) {
        parentMap[c1[`${parent}_id`]] = [];
      }
      parentMap[c1[`${parent}_id`]].push(c1.id);
    }
    for (let i = 0; i < this[child2].length; i += 1) {
      const c2 = this[child2][i];
      c2[`${child1}_id`] = parentMap[c2[`${parent}_id`]] || [];
    }
  }

  transitivePopulate(grandparent, parent, child) {
    // Build transitive link between grandparent/child through parent
    for (let i = 0; i < this[grandparent].length; i += 1) {
      this[grandparent][i][`${child}_id`] = [];
    }
    for (let i = 0; i < this[child].length; i += 1) {
      const s = this[child][i];
      if (this[`${parent}_map`][s[`${parent}_id`]]) {
        s[`${grandparent}_id`] = this[`${parent}_map`][s[`${parent}_id`]][`${grandparent}_id`];
        if (this[`${grandparent}_map`][s[`${grandparent}_id`]]) {
          this[`${grandparent}_map`][s[`${grandparent}_id`]][`${child}_id`].push(s.id);
        }
      }
    }
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

  facetSummary({
    type, field, conditions = [], useMatchingConditions = false,
  }) {
    const valueMap = new Map();
    let paredConditions = null;
    if (useMatchingConditions) {
      paredConditions = groupConditionsByField(conditions);
    } else {
      // Don't filter by conditions that match the field.
      // This seems odd, but enables checking multiple boxes
      // for the same field as an "or".
      paredConditions = groupConditionsByField(
        conditions.filter((cond) => cond.field !== field),
      );
    }
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

export default new DataAPI();
