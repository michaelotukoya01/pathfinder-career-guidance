import concurrent.futures
import hashlib
import json
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import main
from profile_store import ProfileStore
from security import request_history


class StorageSecurityTests(unittest.TestCase):
    def setUp(self):
        request_history.clear()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = ProfileStore(self.directory.name)
        patcher = patch.object(main, 'profile_store', self.store)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)

    def test_profile_tokens_isolate_users_and_are_not_returned_or_stored_plaintext(self):
        first = self.client.post('/profiles', json={'name': 'First'}).json()
        second = self.client.post('/profiles', json={'name': 'Second'}).json()
        url = '/profiles/' + first['id']
        self.assertEqual(self.client.get(url).status_code, 401)
        other = {'Authorization': 'Bearer ' + second['access_token']}
        owner = {'Authorization': 'Bearer ' + first['access_token']}
        for method in ('get', 'put', 'delete'):
            kwargs = {'json': {}} if method == 'put' else {}
            self.assertEqual(getattr(self.client, method)(url, headers=other, **kwargs).status_code, 401)
        response = self.client.get(url, headers=owner)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_access_token_hash', response.json())
        self.assertNotIn(first['access_token'], json.dumps(self.store.get_profile(first['id'])))
        self.assertEqual(self.store.get_profile(first['id'])['_access_token_hash'], hashlib.sha256(first['access_token'].encode()).hexdigest())
        self.assertEqual(self.client.delete(url, headers=owner).status_code, 200)

    def test_admin_endpoints_fail_closed(self):
        for endpoint in ['/model/retrain', '/model/promote/vexample', '/model/scheduler/start', '/model/scheduler/stop']:
            with patch.dict(os.environ, {'ADMIN_API_KEY': ''}):
                self.assertEqual(self.client.post(endpoint).status_code, 503)
            with patch.dict(os.environ, {'ADMIN_API_KEY': 'a' * 40}):
                self.assertEqual(self.client.post(endpoint).status_code, 401)
        with patch.dict(os.environ, {'ADMIN_API_KEY': 'a' * 40}):
            self.assertEqual(self.client.get('/profiles').status_code, 401)
            response = self.client.get('/profiles', headers={'Authorization': 'Bearer ' + 'a' * 40})
            self.assertEqual(response.status_code, 200)

    def test_large_bodies_are_rejected_before_validation(self):
        response = self.client.post('/recommend', content=b'x' * (1024 * 1024 + 1), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 413)

    def test_concurrent_writes_keep_every_assessment_and_deduplicate_retries(self):
        profile_id = self.store.create_profile({'name': 'Concurrent'})
        def save(index):
            return self.store.add_assessment(profile_id, {'id': str(index), 'recommended_career': 'Data Scientist'})
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertTrue(all(pool.map(save, list(range(20)) * 2)))
        self.assertEqual(len(self.store.get_assessment_history(profile_id)), 20)
        self.store.update_profile(profile_id, {'field_of_study': 'Math'})
        self.assertEqual(len(self.store.get_assessment_history(profile_id)), 20)
        self.assertEqual(self.store.get_profile(profile_id)['name'], 'Concurrent')

    def test_legacy_import_preserves_files_but_deletion_does_not_resurrect_records(self):
        profile_id = str(uuid.uuid4())
        legacy_path = Path(self.directory.name) / (profile_id + '.json')
        legacy_path.write_text(json.dumps({'name': 'Legacy', 'assessments': []}), encoding='utf-8')
        migrated = ProfileStore(self.directory.name)
        self.assertEqual(migrated.get_profile(profile_id)['name'], 'Legacy')
        self.assertTrue(legacy_path.exists())
        legacy_path.write_text(json.dumps({'name': 'Legacy', 'assessments': [{'id': 'late-save'}]}), encoding='utf-8')
        migrated = ProfileStore(self.directory.name)
        self.assertEqual(len(migrated.get_assessment_history(profile_id)), 1)
        self.assertEqual(len(ProfileStore(self.directory.name).get_assessment_history(profile_id)), 1)
        self.assertTrue(migrated.delete_profile(profile_id))
        self.assertFalse(legacy_path.exists())
        self.assertIsNone(ProfileStore(self.directory.name).get_profile(profile_id))


if __name__ == '__main__':
    unittest.main()
