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

  http.post('/api/submission/sample-set', () => {
    return HttpResponse.json({
      id: 'sample-set-1',
      name: 'Sample Set 1',
    });
  }),
];