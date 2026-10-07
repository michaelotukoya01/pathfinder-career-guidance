"""Check a deployed Pathfinder instance with synthetic data; delete the test profile."""

import argparse
import json
import uuid
from pathlib import Path

import requests


def check(base):
    base = base.rstrip('/')
    session = requests.Session()
    profile_url = None
    headers = {}

    def call(method, path, expected=200, **kwargs):
        response = session.request(method, base + path, timeout=60, **kwargs)
        if response.status_code != expected:
            raise RuntimeError(f'{method} {path}: expected {expected}, got {response.status_code}')
        return response

    for path in ['/', '/dashboard', '/guide']:
        assert 'text/html' in call('GET', path).headers['Content-Type']
    health = call('GET', '/api/health').json()
    assert health['model_loaded'] and health['profile_store_available']
    payload = json.loads((Path(__file__).resolve().parents[1] / 'test_input.json').read_text())
    payload['skill_python'] = 3.5
    result = call('POST', '/api/recommend', json=payload).json()
    assert len(result['top_3_predictions']) == 3
    assert len(result['skill_gap_analysis']) == 14
    call('POST', '/api/recommend', expected=422, json={})

    try:
        credentials = call('POST', '/api/profiles', json={'name': 'Synthetic deployment check'}).json()
        profile_url = '/api/profiles/' + credentials['id']
        headers = {'Authorization': 'Bearer ' + credentials['access_token']}
        call('GET', profile_url, expected=401)
        call('GET', profile_url, expected=401, headers={'Authorization': 'Bearer invalid-test-token'})
        result['id'] = str(uuid.uuid4())
        for _ in range(2):
            call('POST', profile_url + '/assessments', json=result, headers=headers)
        call('PUT', profile_url, json={'field_of_study': 'Computer Science'}, headers=headers)

        # A fresh client restores access using the saved ID and token.
        restored = requests.get(base + profile_url, headers=headers, timeout=60)
        restored.raise_for_status()
        profile = restored.json()
        assert len(profile['assessments']) == 1, 'Retry created duplicate history'
        assert profile['field_of_study'] == 'Computer Science'
        assert '_access_token_hash' not in profile
        assert restored.headers.get('Cache-Control') == 'no-store'
        assert len(call('GET', profile_url + '/assessments', headers=headers).json()) == 1
    finally:
        if profile_url:
            call('DELETE', profile_url, headers=headers)
            call('GET', profile_url, expected=404, headers=headers)

    print('Passed: pages, health, predictions, validation, private access, save retries, recovery, history, deletion.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', help='Deployed HTTPS origin, for example https://your-project.vercel.app')
    check(parser.parse_args().url)
