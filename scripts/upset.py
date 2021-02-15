from typing import Dict, MutableSet

import requests

sample_map: Dict[str, MutableSet[str]] = {}
study_map: Dict[str, MutableSet[str]] = {}
page_size = 10
params = {
    'limit': page_size,
    'offset': 0
}
count = float('inf')

while params['offset'] < count:
    print(params, count)
    resp = requests.post('http://localhost:8080/api/biosample/search', params=params, verify=False)
    results = resp.json()
    count = results['count']
    for result in results['results']:
        sample_set: MutableSet[str] = set()

        study_id = result['study_id']
        sample_id = result['id']

        for project in result['projects']:
            sample_set.add(project['annotations']['omics_type'].lower())
        key = '_'.join(list(sample_set))
        if key not in sample_map:
            sample_map[key] = set()
        if key not in study_map:
            study_map[key] = set()

        sample_map[key].add(sample_id)
        study_map[key].add(study_id)

    params['offset'] = params['offset'] + page_size

print("Sample Counts")
for key, val in sample_map.items():
    print(key, len(list(val)))

print("Study counts")
for key, val in study_map.items():
    print(key, len(list(val)))
