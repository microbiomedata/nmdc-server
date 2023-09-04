import moment from 'moment';
import filesize from 'filesize';
import { types, getField } from './encoding';

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

export function fieldDisplayName(field, table) {
  const fieldsname = getField(field, table);
  if ('name' in fieldsname) {
    return fieldsname.name;
  }
  return `${field}`.split('_')
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
  if (value.has_raw_value) {
    return `${value.has_raw_value}`;
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
    label: '',
    heirarchyKey: '',
    count: 0,
    depth: 0,
    children: undefined,
    isDefaultExpanded: false,
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
      if (parent && nodeName) {
        if (!node) {
          node = {
            id: nodeKey,
            parent,
            name: nodeName,
            label: nodeName,
            heirarchyKey: heirarchy[depth],
            count: 0,
            depth: depth + 1,
            children: undefined,
            isDefaultExpanded: false,
          };
          nodeMap[nodeKey] = node;

          if (parent.children === undefined) {
            parent.children = [node];
            parent.isDefaultExpanded = true;
          } else {
            parent.children.push(node);
            parent.isDefaultExpanded = false;
          }

          topoSort.push(node);
        }
        node.count += item.count;
      }
    });
  });
  return {
    root, nodeMap, topoSort,
  };
}

export function getChain(node) {
  if (node) {
    return getChain(node.parent).concat([node]);
  }
  return [];
}

export function saveAs(filename, text) {
  const element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,'.concat(encodeURIComponent(text)));
  element.setAttribute('download', filename);
  element.style.display = 'none';
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}
