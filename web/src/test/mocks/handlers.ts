import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/facet-summary', () => {
    return HttpResponse.json([
      { facet: '1', count: 5 },
      { facet: '2', count: 3 },
    ]);
  }),

  http.post('/api/study/facet', () => {
    return HttpResponse.json([
      { facet: '1', count: 5 },
      { facet: '2', count: 3 },
    ]);
  }),

  http.post('/api/biosample/facet', () => {
    return HttpResponse.json([
      { facet: '1', count: 5 },
      { facet: '2', count: 3 },
    ]);
  }),

  http.post('/api/biosample/binned_facet', () => {
    return HttpResponse.json([
      { facet: '1', count: 5 },
      { facet: '2', count: 3 },
    ]);
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

  http.post('/api/biosample/search', async () => {
    return HttpResponse.json({
      count: 13,
      results: [
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
      count: 13,
      results: [
        {
          id: 'bs-1',
          name: 'Biosample 1',
          type: 'Biosample',
        },
      ],
    });
  }),
];