import moment from 'moment';
import { isObject } from 'lodash';
import filesize from 'filesize';
import { tsvParseRows } from 'd3-dsv';

import biosamples from './biosample.json';
import projects from './project.json';
import studies from './study.json';
import studyAdditional from './study_additional.json';
import projectFiles from './ficus_project_files_v1.tsv';

function parseDataObjectCSV(data) {
  const fields = [
    {
      name: 'project_id',
      description: 'This should map to the ids in the projects.json you have.',
      include: true,
      type: 'string',
    },
    {
      name: 'id',
      description: 'unique file identifier (JAMO hash id)',
      include: true,
      type: 'string',
    },
    {
      name: 'name',
      description: 'File name, not necessarily unique',
      include: true,
      type: 'string',
    },
    {
      name: 'category',
      description: 'This is derived from a field used by JGI\'s Genome Portal',
      include: true,
      type: 'string',
    },
    {
      name: 'its_sequencing_project_id',
      description: 'I have it for mapping, should not be used in NMDC',
      include: false,
      type: 'string',
    },
    {
      name: 'its_final_deliverable_id',
      description: 'Another internal entity ID, not for use in NMDC',
      include: false,
      type: 'string',
    },
    {
      name: 'file_type',
      description: 'Doesn\'t look useful for display, I may use it to filter',
      include: false,
      type: 'string',
    },
    {
      name: 'file_size',
      description: 'Useful for display',
      include: true,
      type: 'number',
    },
  ];
  return tsvParseRows(data).map((row) => {
    const record = {};
    row.forEach((d, i) => {
      if (fields[i].include) {
        record[fields[i].name] = fields[i].type === 'number' ? +d : d;
      }
    });
    record.description = filesize(record.file_size);
    return record;
  });
}

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

class DataAPI {
  constructor() {
    this.sample = parseNamedThings(biosamples, 'project');
    this.sample_map = idMap(this.sample);
    this.project = parseNamedThings(projects, 'study');
    this.project_map = idMap(this.project);
    this.study = parseNamedThings(studies);
    this.study_map = idMap(this.study);
    this.data_object = parseDataObjectCSV(projectFiles);
    this.data_object_map = idMap(this.data_object);
    this.backPopulate('study', 'project');
    this.backPopulate('project', 'sample');
    this.backPopulate('project', 'data_object');
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
