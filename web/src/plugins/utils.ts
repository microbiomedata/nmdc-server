import { cloneDeep } from 'lodash';
import protobufjs from 'protobufjs';

import { Condition } from '@/data/api';
import descriptor from '@/data/protobuf-descriptor.json';

const QueryParams = protobufjs.Root.fromJSON(descriptor).lookupType('nmdc.QueryParams');

function arrayBufferToBase64(buffer: Iterable<number>) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

function stringifyQuery(q: any) {
  if ('conditions' in q && q.conditions.length) {
    const clone = cloneDeep(q);
    clone.conditions.forEach((c: Condition) => {
      // eslint-disable-next-line no-param-reassign
      c.value = JSON.stringify(c.value);
    });
    // https://github.com/protobufjs/protobuf.js/issues/1261#issuecomment-667430623
    const msg = QueryParams.fromObject(clone);
    const u8a = QueryParams.encode(msg).finish();
    return '?q='.concat(arrayBufferToBase64(u8a));
  }
  return '';
}

function parseQuery(q: string) {
  const b64 = q.length >= 3 ? q.slice(2) : '';
  const u8a = new Uint8Array(atob(b64).split('').map((c) => c.charCodeAt(0)));
  const msg = QueryParams.decode(u8a);
  const obj = QueryParams.toObject(msg, { enums: String });
  obj.conditions = obj.conditions ?? [];
  obj.conditions.forEach((c: Condition) => {
    // @ts-ignore
    // eslint-disable-next-line no-param-reassign
    c.value = JSON.parse(c.value);
  });
  return obj;
}

export {
  parseQuery,
  stringifyQuery,
};
