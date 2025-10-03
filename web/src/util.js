import moment from 'moment';
import filesize from 'filesize';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';
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
  if (field === 'processing_institution') {
    return NmdcSchema.enums.ProcessingInstitutionEnum.permissible_values[value].title;
  }
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

/**
 * Returns a string describing the depth of a biosample, or returns null.
 *
 * If the biosample's depth annotation contains enough information for this function to format the depth into a string
 * having one of the formats listed below, the function formats it that way. Otherwise, the function returns whatever
 * the biosample's top-level `depth` property contains, which could be `null` (per `nmdc_server/ingest/biosample.py`).
 *
 * Formats:
 * 1. Range with unit (e.g. "1 - 2 meters")
 * 2. Range without unit (e.g. "1 - 2")
 * 3. Number with unit (e.g. "1 meter")
 *
 * Note: I check values' types instead of their truthiness here because I consider `0` to be a valid depth magnitude,
 *       while JavaScript considers it to be falsy (per https://developer.mozilla.org/en-US/docs/Glossary/Falsy).
 *
 * References:
 * - https://jsdoc.app/tags-param#parameters-with-properties
 * - https://microbiomedata.github.io/nmdc-schema/QuantityValue/
 *
 * @param depthAnnotation {object | null} Value of the biosample's `annotations.depth` property
 * @param depthAnnotation.has_minimum_numeric_value {number?} Lower magnitude of the quantity's range
 * @param depthAnnotation.has_maximum_numeric_value {number?} Upper magnitude of the quantity's range
 * @param depthAnnotation.has_numeric_value {number?} Magnitude of the quantity
 * @param depthAnnotation.has_unit {string?} Unit of the quantity
 * @param depth {number | null} Value of the biosample's top-level `depth` property
 * @return {string | null} Either a string describing the depth of the biosample, or `null`
 */
export function formatBiosampleDepth(depthAnnotation, depth) {
  let formattedStr = depth; // fallback value
  if (depthAnnotation !== null) {
    const {
      has_minimum_numeric_value: minMagnitude,
      has_maximum_numeric_value: maxMagnitude,
      has_numeric_value: magnitude,
      has_unit: unit,
    } = depthAnnotation;
    if (typeof minMagnitude === 'number' && typeof maxMagnitude === 'number' && typeof unit === 'string') {
      formattedStr = `${minMagnitude} - ${maxMagnitude} ${unit}`; // range with unit
    } else if (typeof minMagnitude === 'number' && typeof maxMagnitude === 'number') {
      formattedStr = `${minMagnitude} - ${maxMagnitude}`; // range without unit
    } else if (typeof magnitude === 'number' && typeof unit === 'string') {
      formattedStr = `${magnitude} ${unit}`; // number with unit
    }
  }
  return formattedStr;
}

/**
 * Base URL (without a trailing slash) at which the user can access
 * the same ORCID environment being used by the backend API.
 */
export const ORCID_BASE_URL = process.env.NMDC_ORCID_BASE_URL || 'https://orcid.org';
