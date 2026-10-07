"""Cloud routing and real PostgreSQL regression tests (CI provisions Postgres)."""

import concurrent.futures
import os
import unittest
import uuid

from fastapi.testclient import TestClient
from profile_store import PostgresProfileStore
from security import request_history
from vercel_app import app


class CloudRoutingTests(unittest.TestCase):
    def test_api_is_available_under_same_origin_prefix(self):
        request_history.clear()
        with TestClient(app) as client:
            self.assertEqual(client.get('/api/health').status_code, 200)
            self.assertEqual(client.post('/api/recommend', json={}).status_code, 422)
            self.assertEqual(client.get('/api/not-a-route').status_code, 404)


@unittest.skipUnless(os.getenv('PATHFINDER_TEST_DATABASE_URL'), 'PostgreSQL integration URL not configured')
class PostgresStorageTests(unittest.TestCase):
    def setUp(self):
        self.url = os.environ['PATHFINDER_TEST_DATABASE_URL']
        self.store = PostgresProfileStore(self.url)
        self.profile_id = self.store.create_profile({'name': 'Deployment test'})
        self.addCleanup(self.store.delete_profile, self.profile_id)

    def test_concurrent_saves_and_retries_preserve_history_across_connections(self):
        def save(index):
            return self.store.add_assessment(self.profile_id, {'id': str(index), 'recommended_career': 'Data Scientist'})
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertTrue(all(pool.map(save, list(range(16)) * 2)))
        reopened = PostgresProfileStore(self.url)
        self.assertEqual(len(reopened.get_assessment_history(self.profile_id)), 16)
        self.assertTrue(reopened.update_profile(self.profile_id, {'field_of_study': 'Math'}))
        self.assertEqual(len(self.store.get_assessment_history(self.profile_id)), 16)
        self.assertEqual(self.store.get_profile(self.profile_id)['name'], 'Deployment test')

    def test_delete_and_missing_records(self):
        self.assertTrue(any(item['id'] == self.profile_id for item in self.store.list_profiles()))
        self.assertTrue(self.store.delete_profile(self.profile_id))
        self.assertIsNone(self.store.get_profile(self.profile_id))
        self.assertFalse(self.store.delete_profile(self.profile_id))
        self.assertFalse(self.store.update_profile(self.profile_id, {'name': 'Missing'}))
        self.assertFalse(self.store.add_assessment(self.profile_id, {'id': str(uuid.uuid4())}))

    def test_failed_transactions_rollback_and_ids_are_validated(self):
        with self.assertRaises(RuntimeError):
            with self.store._connect(write=True) as connection:
                connection.execute('DELETE FROM profiles WHERE id=%s', (self.profile_id,))
                raise RuntimeError('Rollback test')
        self.assertIsNotNone(self.store.get_profile(self.profile_id))
        with self.assertRaises(ValueError):
            self.store.get_profile("invalid'; DROP TABLE profiles; --")
