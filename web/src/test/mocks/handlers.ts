import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/facet-summary', () => {
    return HttpResponse.json({
      facets: {
        'facet-1': 5,
        'facet-2': 3,
      },
    });
  }),

  http.post('/api/study/facet', () => {
    return HttpResponse.json({
      facets: {
        'study-1': 100,
        'study-2': 75,
        'study-3': 50,
      },
    });
  }),

  http.post('/api/biosample/facet', () => {
    return HttpResponse.json({
      facets: {
        'soil': 200,
        'aquatic': 150,
        'host-associated': 100,
      },
    });
  }),

  http.post('/api/biosample/binned_facet', () => {
    return HttpResponse.json({
      facets: {
        '0-100': 50,
        '100-200': 75,
        '200-300': 100,
      },
    });
  }),

  http.post('/api/submission/sample-set', () => {
    return HttpResponse.json({
      id: 'sample-set-1',
      name: 'Sample Set 1',
    });
  }),

  http.get('/api/study/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'Test Study',
      description: 'Test study description',
    });
  }),

  http.post('/api/biosample/search', () => {
    return HttpResponse.json({
      results: {
        count: 13,
        limit: 5,
        offset: 0,
      },
      data: [
        {
          id: 'bs-1',
          name: 'Biosample 1',
          type: 'Biosample',
        },
      ],
    });
  }),

  http.post('/api/biosamples', () => {
    return HttpResponse.json({
      results: {
        count: 13,
        limit: 5,
        offset: 0,
      },
      data: [
        {
          id: 'bs-1',
          name: 'Biosample 1',
          type: 'Biosample',
        },
      ],
    });
  }),

  http.post('/api/data_generation/facet', () => {
    return HttpResponse.json({
      facets: {
        'metagenomics': 100,
        'metatranscriptomics': 75,
        'metabolomics': 50,
      },
    });
  }),

  http.post('/api/data_object/workflow_summary', () => {
    return HttpResponse.json({});
  }),

  http.post('/api/bulk_download/summary', () => {
    return HttpResponse.json({ count: 0, size: 0 });
  }),

  http.get('/api/summary', () => {
    return HttpResponse.json({});
  }),

  http.get('/api/settings', () => {
    return HttpResponse.json({
      portal_banner_title: null,
      portal_banner_message: null,
      disable_bulk_data_product_download: false,
      disable_individual_data_product_download: false,
    });
  }),

  http.post('/api/study/search', () => {
    return HttpResponse.json({
      count: 0,
      results: [],
    });
  }),
];