from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

from gateway import nutri_ai_lite


class NutritionVisionTests(unittest.TestCase):
    @patch.object(nutri_ai_lite.requests, 'post')
    def test_uses_current_groq_vision_model_and_json_mode(self, post):
        response = Mock(ok=True)
        response.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '{"calories": 120, "protein": 4}',
                    },
                },
            ],
        }
        post.return_value = response

        with patch.dict(os.environ, {'GROQ_API_KEY': 'test-key'}):
            result = nutri_ai_lite.extract_nutrition_from_image(
                b'image-bytes',
                'image/png',
            )

        request = post.call_args.kwargs['json']
        self.assertEqual(request['model'], 'qwen/qwen3.6-27b')
        self.assertEqual(request['response_format'], {'type': 'json_object'})
        self.assertEqual(request['reasoning_effort'], 'none')
        self.assertEqual(result['calories'], 120)
        self.assertEqual(result['protein'], 4)

    @patch.object(nutri_ai_lite.requests, 'post')
    def test_returns_groq_error_message_when_vision_request_fails(self, post):
        response = Mock(ok=False, status_code=400)
        response.json.return_value = {
            'error': {'message': 'The selected model does not support images.'},
        }
        post.return_value = response

        with patch.dict(os.environ, {'GROQ_API_KEY': 'test-key'}):
            result = nutri_ai_lite.extract_nutrition_from_image(
                b'image-bytes',
                'image/png',
            )

        self.assertIn('does not support images', result['error'])


if __name__ == '__main__':
    unittest.main()
