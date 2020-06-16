import axios from 'axios';

const BASE_URL = '/api';

class DataAPI {
  constructor() {
    this.client = axios;
    this.summary = null;
  }

  static typeMap(type) {
    if (type === 'sample') {
      return 'biosample';
    }
    return type;
  }

  async post(path, data) {
    return this.client.post(`${BASE_URL}/${path}`, data);
  }

  async query(type, conditions) {
    const path = DataAPI.typeMap(type);
    const { data } = await this.post(`${path}/search`, { conditions });
    const { results } = data;
    return results.map((d) => {
      const { annotations } = d;
      delete d.annotations; // eslint-disable-line
      return { ...annotations, ...d };
    });
  }

  async facetSummary({
    type, field, conditions = [],
  }) {
    let path = type;
    if (type === 'sample') {
      path = 'biosample';
    }
    const resp = await this.post(`${path}/facet`, { conditions, attribute: field });
    return Object.keys(resp.data.facets)
      .map((value) => ({ value, count: resp.data.facets[value] }))
      .sort((a, b) => b.count - a.count);
  }

  async databaseSummary() {
    if (this.summary === null) {
      const resp = await this.client.get(`${BASE_URL}/summary`);
      this.summary = resp.data;
    }
    return this.summary;
  }

  async primitiveFields(type) {
    const summary = await this.databaseSummary();
    return Object.keys(summary[DataAPI.typeMap(type)].attributes);
  }

  count(table) {
    if (this.summary === null) {
      return 0;
    }
    return this.summary[table].total;
  }
}

export default new DataAPI();
