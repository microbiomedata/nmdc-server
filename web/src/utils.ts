import { cloneDeep } from 'lodash';
import protobufjs from 'protobufjs';

import { Condition } from '@/data/api';
import descriptor from '@/data/protobuf-descriptor.json';

const QueryParams = protobufjs.Root.fromJSON(descriptor).lookupType('nmdc.QueryParams');

/**
 * Convert an ArrayBuffer to a base6 encoded string using URL-safe characters since the result will
 * be used in a URL query param.
 * See: https://www.rfc-editor.org/rfc/rfc4648#section-5
 * @param buffer
 */
function arrayBufferToBase64Urlencoded(buffer: Iterable<number>) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i += 1) {
    binary += String.fromCharCode(bytes[i]!);
  }
  const base64 = window.btoa(binary);
  return base64
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

/**
 * Convert a base64 encoded string using URL-safe characters to an ArrayBuffer.
 * @param base64Urlencoded
 */
function base64UrlencodedToArrayBuffer(base64Urlencoded: string) {
  const base64 = base64Urlencoded
    .replace(/-/g, '+')
    .replace(/_/g, '/');
  return new Uint8Array(window.atob(base64).split('').map((c) => c.charCodeAt(0)));
}

/**
 * If the query contains conditions, encode them as a protobuf message, put the result into the
 * q parameter, and remove the conditions parameter.
 */
export function stringifyQuery(params: any) {
  if ('conditions' in params) {
    if (params.conditions.length) {
      const clone = cloneDeep(params);
      clone.conditions.forEach((c: Condition) => {
         
        c.value = JSON.stringify(c.value);
      });
      // https://github.com/protobufjs/protobuf.js/issues/1261#issuecomment-667430623
      const msg = QueryParams.fromObject(clone);
      const u8a = QueryParams.encode(msg).finish();
       
      params.q = arrayBufferToBase64Urlencoded(u8a);
    }
     
    delete params.conditions;
  }
  const queryParamsString = new URLSearchParams(params).toString();
  return queryParamsString ? `${queryParamsString}` : '';
}

/**
 * If the query contains a q parameter, decode it into the conditions parameter.
 */
export function parseQuery(q: string) {
  const params = new URLSearchParams(q);
  const parsed = Object.fromEntries(params.entries());
  if (params.has('q')) {
    const u8a = base64UrlencodedToArrayBuffer(params.get('q')!);
    const msg = QueryParams.decode(u8a);
    const obj = QueryParams.toObject(msg, { enums: String });
    obj.conditions.forEach((c: Condition) => {
      // @ts-ignore
       
      c.value = JSON.parse(c.value);
    });
    parsed.conditions = obj.conditions;
  }
  return parsed;
}

export function downloadJson(json: object, filename: string) {
  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(json, null, 2));
  const downloadAnchorNode = document.createElement('a');
  downloadAnchorNode.setAttribute('href', dataStr);
  downloadAnchorNode.setAttribute('download', filename);
  document.body.appendChild(downloadAnchorNode);
  downloadAnchorNode.click();
  downloadAnchorNode.remove();
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const downloadAnchorNode = document.createElement('a');
  downloadAnchorNode.setAttribute('href', url);
  downloadAnchorNode.setAttribute('download', filename);
  document.body.appendChild(downloadAnchorNode);
  downloadAnchorNode.click();
  downloadAnchorNode.remove();
  window.URL.revokeObjectURL(url);
}