import moment from 'moment';
import filesize from 'filesize';
import { types, fields } from './encoding';

export function valueCardinality(value) {
  if (Array.isArray(value)) {
    return value.length;
  }
  return 1;
}

export function typeWithCardinality(type, cardinality) {
  if (types[type] === undefined) {
    return type;
  }
  if (cardinality === 1) {
    return types[type].name;
  }
  return types[type].plural;
}

export function capitalizeAcronyms(word) {
  if (['id', 'ncbi', 'gold', 'jgi', 'doi'].includes(word.toLowerCase())) {
    return word.toUpperCase();
  }
  return word;
}

export function toSentenceCase(word) {
  return `${word[0].toUpperCase()}${word.slice(1)}`;
}

export function fieldDisplayName(field) {
  if (field in fields && 'name' in fields[field]) {
    return fields[field].name;
  }
  return field.split('_')
    .map((word, i) => (i === 0 ? toSentenceCase(word) : word))
    .map((word) => capitalizeAcronyms(word))
    .reduce((prev, cur) => `${prev}${prev === '' ? '' : ' '}${cur}`, '');
}

export function valueDisplayName(field, value) {
  if (field.includes('date')) {
    return moment.utc(value).format('YYYY-MM-DD, hh:mm:ss');
  }
  if (field === 'file_size') {
    return filesize(value);
  }
  return `${value}`;
}

/**
 * Transform flat array representing fixed-height tree into actual tree object.
 * Tree is built in topological order, so return topoSort for convenience.
 * O(n) = len(data) * (len(heirarchy)^2)
 *
 * @param {Array<{ [heirarchy_key]: value, ..., count: number }>} data
 * example: [
 *   { level1: 'foo', level2: 'bar', level3: 'baz', count: 2 },
 *   { level1: 'foo', level2: 'bar', level3: 'other', count: 4 },
 * ]
 * @param {Array<string>} heirarchy keys in data array
 * example: [ 'level1', 'level2', 'level3' ]
 * @returns {{ root, nodeMap, topoSort }} tree of height len(heirarchy) + 1 (including root)
 */
export function makeTree(data, heirarchy) {
  const root = {
    id: '',
    parent: null,
    name: '',
    count: 0,
    depth: 0,
    children: [],
  };
  const nodeMap = {
    [root.id]: root,
  };
  const topoSort = [root];
  heirarchy.forEach((_, depth) => {
    data.forEach((item) => {
      const parentKey = heirarchy
        .slice(0, depth)
        .map((k) => item[k])
        .join('.');
      const nodeName = item[heirarchy[depth]];
      const nodeKey = `${parentKey}${parentKey && '.'}${nodeName}`;
      const parent = nodeMap[parentKey];
      let node = nodeMap[nodeKey];
      if (!node) {
        node = {
          id: nodeKey,
          parent,
          name: nodeName,
          count: 0,
          depth: depth + 1,
          children: [],
        };
        nodeMap[nodeKey] = node;
        parent.children.push(node);
        topoSort.push(node);
      }
      node.count += item.count;
    });
  });
  return {
    root, nodeMap, topoSort,
  };
}
