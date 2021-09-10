import Vue from 'vue';
import VueRouter from 'vue-router';

import protobufjs from 'protobufjs';

import Search from '@/views/Search/Layout.vue';
import SamplePage from '@/views/IndividualResults/SamplePage.vue';
import StudyPage from '@/views/IndividualResults/StudyPage.vue';
import descriptor from '@/data/protobuf-descriptor.json';
import { cloneDeep } from 'lodash';

Vue.use(VueRouter);
const QueryParams = protobufjs.Root.fromJSON(descriptor).lookupType('nmdc.QueryParams');

function arrayBufferToBase64(buffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

export default new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'Search',
      component: Search,
    },
    {
      path: '/details/sample/:id',
      name: 'Sample',
      component: SamplePage,
      props: true,
    },
    {
      path: '/details/study/:id',
      name: 'Study',
      component: StudyPage,
      props: true,
    },
  ],

  parseQuery(q) {
    const b64 = q.length >= 3 ? q.slice(2) : '';
    const u8a = new Uint8Array(atob(b64).split('').map((c) => c.charCodeAt(0)));
    const msg = QueryParams.decode(u8a);
    const obj = QueryParams.toObject(msg, { enums: String });
    obj.conditions.forEach((c) => {
      // eslint-disable-next-line no-param-reassign
      c.value = JSON.parse(c.value);
    });
    return obj;
  },
  stringifyQuery(q) {
    if ('conditions' in q && q.conditions.length) {
      const clone = cloneDeep(q);
      clone.conditions.forEach((c) => {
        // eslint-disable-next-line no-param-reassign
        c.value = JSON.stringify(c.value);
      });
      // https://github.com/protobufjs/protobuf.js/issues/1261#issuecomment-667430623
      const msg = QueryParams.fromObject(clone);
      const u8a = QueryParams.encode(msg).finish();
      return '?q='.concat(arrayBufferToBase64(u8a));
    }
    return '';
  },
});
