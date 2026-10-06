"""Regression coverage for application startup, recommendations and saved history.

Run: python -m unittest discover -s tests -v
"""
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient
import main
from model_retraining import ModelRetrainer
from profile_store import ProfileStore
from security import RateLimitMiddleware, request_history
from skill_decay_utils import SkillDecayModel, apply_skill_decay, get_skill_decay_info


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.store = ProfileStore(cls.temp.name)
        cls.patcher = patch.object(main, 'profile_store', cls.store)
        cls.patcher.start()
        cls.client = TestClient(main.app)
        cls.payload = json.loads((main.BASE_DIR / 'test_input.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.patcher.stop()
        cls.temp.cleanup()

    def setUp(self):
        request_history.clear()
        environment = patch.dict(os.environ, {'ADMIN_API_KEY': 'test-admin-key-' + 'x' * 32, 'ENABLE_RETRAINING_SCHEDULER': 'true'})
        environment.start()
        self.addCleanup(environment.stop)
        self.client.headers['Authorization'] = 'Bearer ' + os.environ['ADMIN_API_KEY']

    def test_recommendation_and_all_skill_mappings(self):
        payload = {**self.payload, 'skill_python': 3.5, 'skill_data_analysis': 4.5,
                   'skill_machine_learning': 4.0}
        response = self.client.post('/recommend?include_explanation=true', json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data['recommended_career'], data['top_3_predictions'][0]['career'])
        self.assertEqual(data['confidence'], data['top_3_predictions'][0]['probability'])
        gaps = {gap['skill']: gap for gap in data['skill_gap_analysis']}
        self.assertEqual(len(gaps), 14)
        self.assertEqual(gaps['skill_data_analysis']['user_level'], 4.5)
        self.assertEqual(gaps['skill_machine_learning']['user_level'], 4.0)
        self.assertIn('explanation', data)

    def test_skill_decay_dates_and_consistency(self):
        payload = {**self.payload, 'skill_python': 5, 'last_used_skill_python': '2020-01-01T00:00:00Z'}
        response = self.client.post('/recommend', json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        info = data['skill_decay_info']['skill_python']
        gap = next(g for g in data['skill_gap_analysis'] if g['skill'] == 'skill_python')
        self.assertLess(info['decayed_level'], 5)
        self.assertEqual(info['decayed_level'], gap['user_level'])
        self.assertGreater(info['days_since_used'], 0)

    def test_invalid_input_returns_json(self):
        response = self.client.post('/recommend', json={**self.payload, 'skill_python': 6})
        self.assertEqual(response.status_code, 422)
        self.assertIsInstance(response.json()['errors'], list)
        response = self.client.post('/recommend', json={})
        self.assertEqual(response.status_code, 422)

    def test_cors_preflight(self):
        response = self.client.options('/recommend', headers={
            'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://localhost:3000')

    def test_lifespan_loads_active_model_and_stops_scheduler(self):
        original = main.model, main.preprocessor, main.label_encoder
        try:
            with TestClient(main.app) as client:
                self.assertEqual(client.get('/health').status_code, 200)
                response = client.post('/recommend', json=self.payload)
                self.assertEqual(response.status_code, 200, response.text)
                if main.model_retrainer.model is not None:
                    self.assertIs(main.model, main.model_retrainer.model)
                else:
                    self.assertIs(main.model, original[0])
            self.assertFalse(main.model_retrainer.scheduler_thread.is_alive())
        finally:
            main.model, main.preprocessor, main.label_encoder = original

    def test_profile_lifecycle(self):
        response = self.client.post('/profiles', json={'name': 'Test User'})
        self.assertEqual(response.status_code, 200)
        profile_id = response.json()['id']
        self.client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
        try:
            result = self.client.post('/recommend', json=self.payload).json()
            response = self.client.post(f'/profiles/{profile_id}/assessments', json=result)
            self.assertEqual(response.status_code, 200, response.text)
            history = self.client.get(f'/profiles/{profile_id}/assessments').json()
            self.assertEqual(len(history), 1)
            self.assertIn('id', history[0])
            self.assertEqual(history[0]['recommended_career'], result['recommended_career'])
            self.assertEqual(self.client.put(f'/profiles/{profile_id}', json={'field_of_study': 'Math'}).status_code, 200)
            profile = self.client.get(f'/profiles/{profile_id}').json()
            self.assertEqual(profile['name'], 'Test User')
            self.assertEqual(len(profile['assessments']), 1)
        finally:
            self.assertEqual(self.client.delete(f'/profiles/{profile_id}').status_code, 200)
        self.assertEqual(self.client.get(f'/profiles/{profile_id}').status_code, 404)
        self.assertEqual(self.client.delete(f'/profiles/{profile_id}').status_code, 404)

    def test_retrying_assessment_save_does_not_duplicate_history(self):
        created = self.client.post('/profiles', json={'name': 'Retry Test'}).json()
        profile_id = created['id']
        self.client.headers['Authorization'] = 'Bearer ' + created['access_token']
        result = self.client.post('/recommend', json=self.payload).json()
        result.update(id='stable-client-request-id', explanation='A saved explanation')
        try:
            for _ in range(2):
                response = self.client.post(f'/profiles/{profile_id}/assessments', json=result)
                self.assertEqual(response.status_code, 200, response.text)
            history = self.client.get(f'/profiles/{profile_id}').json()['assessments']
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]['id'], result['id'])
            self.assertEqual(history[0]['explanation'], result['explanation'])
            result['id'] = 'another-client-request-id'
            self.assertEqual(self.client.post(f'/profiles/{profile_id}/assessments', json=result).status_code, 200)
            self.assertEqual(len(self.client.get(f'/profiles/{profile_id}').json()['assessments']), 2)
        finally:
            self.client.delete(f'/profiles/{profile_id}')
        self.assertEqual(self.client.put(f'/profiles/{profile_id}', json={}).status_code, 404)
        self.assertEqual(self.client.get(f'/profiles/{profile_id}/assessments').status_code, 404)

    def test_invalid_profile_paths_and_pagination(self):
        self.assertEqual(self.client.get('/profiles/not-a-uuid').status_code, 422)
        self.assertEqual(self.client.get('/profiles?limit=-1').status_code, 422)
        with self.assertRaises(ValueError):
            self.store.get_profile('../outside')

    def test_profile_creation_reports_write_failure(self):
        with patch.object(self.store, '_save_profile', return_value=False):
            self.assertEqual(self.client.post('/profiles', json={}).status_code, 500)

    def test_market_ranking_matches_winner(self):
        with patch.object(main, 'adjust_predictions_with_market', return_value=[('Frontend Developer', 0.8), ('Data Scientist', 0.2)]):
            career, predictions = main.get_market_adjusted_predictions(main.preprocess_input(main.UserInput(**self.payload)))
        self.assertEqual(career, predictions[0][0])

    def test_target_derived_features_are_excluded_from_inference(self):
        self.assertNotIn('confidence_score', main.original_features)
        self.assertNotIn('skill_gaps', main.original_features)
        first = main.preprocess_input(main.UserInput(**self.payload))
        changed = main.preprocess_input(main.UserInput(**{**self.payload, 'confidence_score': 0.01, 'skill_gaps': '{}'}))
        np.testing.assert_array_equal(first, changed)

    def test_promotion_uses_service_and_reloads(self):
        with patch.object(main, 'promote_stored_model_version', return_value=True) as promote, patch.object(main, 'reload_active_model') as reload:
            response = self.client.post('/model/promote/vtest')
            self.assertEqual(response.status_code, 200)
            promote.assert_called_once_with('vtest')
            reload.assert_called_once()
        with patch.object(main, 'promote_stored_model_version', return_value=False):
            self.assertEqual(self.client.post('/model/promote/vmissing').status_code, 400)

    def test_explanation_path(self):
        with patch.object(main, 'anthropic_client', object()), patch.object(main, 'get_llm_explanation', return_value='Explanation'):
            response = self.client.post('/explain', json=self.payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['explanation'], 'Explanation')


class UtilityTests(unittest.TestCase):
    def test_decay_handles_metadata_blank_and_timestamp_dates(self):
        now = datetime(2026, 1, 1)
        payload = {'skill_python': 4, 'skill_gaps': '{}', 'last_used_skill_python': '2025-01-01T00:00:00Z'}
        result = apply_skill_decay(payload, SkillDecayModel(), now)
        self.assertLess(result['skill_python'], 4)
        self.assertEqual(payload['skill_python'], 4)
        self.assertEqual(result['skill_gaps'], '{}')
        self.assertLess(SkillDecayModel().apply_decay_to_user_profile(payload, now)['skill_python'], 4)
        for date in ['', None, '2030-01-01']:
            data = {**payload, 'last_used_skill_python': date}
            self.assertEqual(apply_skill_decay(data, now=now)['skill_python'], 4)
            self.assertEqual(get_skill_decay_info(data, now=now)['skill_python']['decay_amount'], 0)

    def test_rate_limit_returns_429_and_recovers(self):
        request_history.clear()
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, calls=2, period=60)
        @app.get('/')
        def root():
            return {'ok': True}
        with TestClient(app) as client:
            self.assertEqual(client.get('/').status_code, 200)
            self.assertEqual(client.get('/').status_code, 200)
            response = client.get('/')
            self.assertEqual(response.status_code, 429)
            self.assertIn('Retry-After', response.headers)
            with patch('security.time.time', return_value=10**12):
                self.assertEqual(client.get('/').status_code, 200)
        request_history.clear()

    def test_scheduler_can_stop_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            retrainer = ModelRetrainer(model_dir=str(Path(directory) / 'models'), data_dir=str(Path(directory) / 'data'))
            for _ in range(2):
                retrainer.start_scheduler()
                retrainer.start_scheduler()
                self.assertEqual(len(retrainer._scheduler.jobs), 1)
                retrainer.stop_scheduler()
                self.assertFalse(retrainer.scheduler_thread.is_alive())
                self.assertEqual(len(retrainer._scheduler.jobs), 0)

    def test_retraining_preserves_numeric_features_and_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            retrainer = ModelRetrainer(model_dir=str(Path(directory) / 'models'), data_dir=str(Path(directory) / 'data'))
            version = retrainer.retrain_model(force=True)
            self.assertIsNotNone(version)
            numeric = dict((name, cols) for name, _, cols in retrainer.preprocessor.transformers_)['num']
            self.assertIn('skill_python', numeric)
            should_retrain, reason = retrainer.should_retrain()
            self.assertFalse(should_retrain, reason)
            self.assertTrue(retrainer.promote_model(version))
            self.assertFalse(retrainer.promote_model('../outside'))


if __name__ == '__main__':
    unittest.main()
