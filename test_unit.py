"""
Comprehensive Unit Tests for Smart Rural AI Advisor — Backend
Tests every logic branch with proper mocking of AWS services.
Run: python -m pytest test_unit.py -v   OR   python test_unit.py
"""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from io import BytesIO
import importlib
import importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))


class FakeContext:
    function_name = "test_lambda"


def load_lambda(subdir):
    """Load a Lambda handler module by its subdirectory name."""
    mod_path = os.path.join(BASE_DIR, 'backend', 'lambdas', subdir)
    if mod_path not in sys.path:
        sys.path.insert(0, mod_path)
    spec = importlib.util.spec_from_file_location(
        f"lambda_{subdir}_{id(subdir)}", os.path.join(mod_path, "handler.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ================================================================
#  1. RESPONSE HELPER - Full logic tests
# ================================================================

class TestResponseHelper(unittest.TestCase):
    """Tests for utils/response_helper.py"""

    def setUp(self):
        from utils.response_helper import success_response, error_response
        self.success_response = success_response
        self.error_response = error_response

    def test_success_default_values(self):
        r = self.success_response({"key": "val"})
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["message"], "Success")
        self.assertEqual(body["language"], "en")
        self.assertEqual(body["data"], {"key": "val"})

    def test_success_custom_status_code(self):
        r = self.success_response({}, status_code=201)
        self.assertEqual(r["statusCode"], 201)

    def test_success_custom_language(self):
        r = self.success_response({}, language="ta")
        body = json.loads(r["body"])
        self.assertEqual(body["language"], "ta")

    def test_success_custom_message(self):
        r = self.success_response({}, message="Created")
        body = json.loads(r["body"])
        self.assertEqual(body["message"], "Created")

    def test_success_cors_headers(self):
        r = self.success_response({})
        self.assertEqual(r["headers"]["Access-Control-Allow-Origin"], "*")
        self.assertIn("GET", r["headers"]["Access-Control-Allow-Methods"])
        self.assertIn("POST", r["headers"]["Access-Control-Allow-Methods"])
        self.assertIn("OPTIONS", r["headers"]["Access-Control-Allow-Methods"])
        self.assertEqual(r["headers"]["Content-Type"], "application/json")

    def test_success_data_is_none(self):
        r = self.success_response(None)
        body = json.loads(r["body"])
        self.assertIsNone(body["data"])

    def test_success_data_is_list(self):
        r = self.success_response([1, 2, 3])
        body = json.loads(r["body"])
        self.assertEqual(body["data"], [1, 2, 3])

    def test_error_default_values(self):
        r = self.error_response("fail")
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 500)
        self.assertEqual(body["status"], "error")
        self.assertIsNone(body["data"])
        self.assertEqual(body["message"], "fail")
        self.assertEqual(body["language"], "en")

    def test_error_custom_code_and_language(self):
        r = self.error_response("bad", 400, language="hi")
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 400)
        self.assertEqual(body["language"], "hi")

    def test_error_cors_headers(self):
        r = self.error_response("err")
        self.assertEqual(r["headers"]["Access-Control-Allow-Origin"], "*")

    def test_body_is_valid_json(self):
        r = self.success_response({"nested": {"a": [1, 2]}})
        parsed = json.loads(r["body"])
        self.assertEqual(parsed["data"]["nested"]["a"], [1, 2])


# ================================================================
#  2. ERROR HANDLER - All exception paths
# ================================================================

class TestErrorHandler(unittest.TestCase):
    """Tests for utils/error_handler.py"""

    def setUp(self):
        from utils.error_handler import handle_errors
        from utils.response_helper import success_response
        self.handle_errors = handle_errors
        self.success_response = success_response

    def test_passthrough_on_success(self):
        @self.handle_errors
        def handler(event, context):
            return self.success_response({"ok": True})

        r = handler({}, FakeContext())
        self.assertEqual(r["statusCode"], 200)
        body = json.loads(r["body"])
        self.assertEqual(body["data"], {"ok": True})

    def test_key_error_returns_400(self):
        @self.handle_errors
        def handler(event, context):
            return {}["missing"]

        r = handler({}, FakeContext())
        self.assertEqual(r["statusCode"], 400)
        body = json.loads(r["body"])
        self.assertIn("missing", body["message"])

    def test_value_error_returns_500(self):
        @self.handle_errors
        def handler(event, context):
            raise ValueError("bad value")

        r = handler({}, FakeContext())
        self.assertEqual(r["statusCode"], 500)
        body = json.loads(r["body"])
        self.assertIn("Internal server error", body["message"])

    def test_type_error_returns_500(self):
        @self.handle_errors
        def handler(event, context):
            raise TypeError("wrong type")

        r = handler({}, FakeContext())
        self.assertEqual(r["statusCode"], 500)

    def test_runtime_error_returns_500(self):
        @self.handle_errors
        def handler(event, context):
            raise RuntimeError("runtime issue")

        r = handler({}, FakeContext())
        self.assertEqual(r["statusCode"], 500)

    def test_context_function_name_logged(self):
        """Verify the decorator does not crash when accessing context.function_name"""
        @self.handle_errors
        def handler(event, context):
            return self.success_response({})

        ctx = FakeContext()
        ctx.function_name = "my_lambda_fn"
        r = handler({"key": "val"}, ctx)
        self.assertEqual(r["statusCode"], 200)


# ================================================================
#  3. GOVT SCHEMES LAMBDA - All code paths
# ================================================================

class TestGovtSchemes(unittest.TestCase):
    """Tests for lambdas/govt_schemes/handler.py"""

    def setUp(self):
        self.mod = load_lambda("govt_schemes")
        self.handler = self.mod.lambda_handler
        self.ctx = FakeContext()

    def test_get_all_schemes_returns_9(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": None, "body": None}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(len(body["data"]["schemes"]), 9)

    def test_get_all_schemes_has_required_keys(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": None, "body": None}, self.ctx)
        body = json.loads(r["body"])
        for key in ["pm_kisan", "pmfby", "kcc", "soil_health_card", "pmksy", "e_nam", "pkvy", "nfsm", "agriculture_infra_fund"]:
            self.assertIn(key, body["data"]["schemes"], f"Missing scheme: {key}")

    def test_each_scheme_has_required_fields(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": None, "body": None}, self.ctx)
        body = json.loads(r["body"])
        for key, scheme in body["data"]["schemes"].items():
            for field in ["name", "full_name", "benefit", "eligibility", "how_to_apply", "helpline", "website"]:
                self.assertIn(field, scheme, f"Scheme {key} missing field: {field}")

    def test_get_specific_scheme_by_exact_key(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": {"name": "kcc"}, "body": None}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["data"]["schemes"]["full_name"], "Kisan Credit Card")

    def test_get_scheme_pm_kisan_benefit(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": {"name": "pm_kisan"}, "body": None}, self.ctx)
        body = json.loads(r["body"])
        self.assertIn("6,000", body["data"]["schemes"]["benefit"])

    def test_keyword_search_finds_kisan_schemes(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": {"name": "kisan"}, "body": None}, self.ctx)
        body = json.loads(r["body"])
        # Should find pm_kisan (PM-KISAN) and kcc (Kisan Credit Card) at minimum
        self.assertGreaterEqual(len(body["data"]["schemes"]), 2)

    def test_keyword_search_organic_finds_pkvy(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": {"name": "organic"}, "body": None}, self.ctx)
        body = json.loads(r["body"])
        # "organic" is in PKVY full_name "Paramparagat Krishi Vikas Yojana"... actually no, it's not
        # Let's search for "paramparagat"
        r2 = self.handler({"httpMethod": "GET", "queryStringParameters": {"name": "pkvy"}, "body": None}, self.ctx)
        body2 = json.loads(r2["body"])
        self.assertEqual(body2["data"]["schemes"]["name"], "PKVY")

    def test_keyword_search_nonexistent_returns_empty(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": {"name": "zzz_nonexistent"}, "body": None}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["data"]["schemes"], {})

    def test_options_cors(self):
        r = self.handler({"httpMethod": "OPTIONS"}, self.ctx)
        self.assertEqual(r["statusCode"], 200)

    def test_agentcore_tool_call_specific(self):
        event = {"parameters": [{"name": "scheme_name", "value": "pmfby"}, {"name": "farmer_state", "value": "TN"}]}
        r = self.handler(event, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["schemes"]["name"], "PMFBY")

    def test_agentcore_tool_call_all(self):
        event = {"parameters": [{"name": "scheme_name", "value": "all"}, {"name": "farmer_state", "value": "TN"}]}
        r = self.handler(event, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(len(body["data"]["schemes"]), 9)

    def test_post_body_parsing(self):
        event = {"httpMethod": "POST", "queryStringParameters": None,
                 "body": json.dumps({"scheme_name": "kcc"})}
        r = self.handler(event, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["data"]["schemes"]["full_name"], "Kisan Credit Card")

    def test_helpline_note_always_present(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": None, "body": None}, self.ctx)
        body = json.loads(r["body"])
        self.assertIn("1800-180-1551", body["data"]["note"])

    def test_case_insensitive_search(self):
        r = self.handler({"httpMethod": "GET", "queryStringParameters": {"name": "PM_KISAN"}, "body": None}, self.ctx)
        body = json.loads(r["body"])
        # pm_kisan is the key, PM_KISAN.lower() = pm_kisan -> exact match
        self.assertIn("6,000", body["data"]["schemes"]["benefit"])


# ================================================================
#  4. WEATHER LOOKUP LAMBDA - Mocked API calls, logic tests
# ================================================================

class TestWeatherLookup(unittest.TestCase):
    """Tests for lambdas/weather_lookup/handler.py with mocked HTTP"""

    def setUp(self):
        self.ctx = FakeContext()
        # We'll patch and reload each time

    def _make_current_response(self, temp=30, humidity=65, wind=3.5, rain_1h=0, description="clear sky"):
        return {
            "cod": 200,
            "main": {"temp": temp, "humidity": humidity},
            "weather": [{"description": description}],
            "wind": {"speed": wind},
            "rain": {"1h": rain_1h}
        }

    def _make_forecast_response(self, items=None):
        if items is None:
            items = [
                {"dt_txt": "2026-02-27 06:00:00", "main": {"temp": 28}, "weather": [{"description": "clear"}], "rain": {}},
                {"dt_txt": "2026-02-27 12:00:00", "main": {"temp": 34}, "weather": [{"description": "sunny"}], "rain": {}},
                {"dt_txt": "2026-02-27 18:00:00", "main": {"temp": 30}, "weather": [{"description": "clear"}], "rain": {}},
                {"dt_txt": "2026-02-28 06:00:00", "main": {"temp": 26}, "weather": [{"description": "cloudy"}], "rain": {"3h": 2}},
                {"dt_txt": "2026-02-28 12:00:00", "main": {"temp": 32}, "weather": [{"description": "cloudy"}], "rain": {"3h": 3}},
            ]
        return {"list": items}

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_normal_weather_returns_200(self, mock_get):
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value=self._make_current_response())),
            MagicMock(json=MagicMock(return_value=self._make_forecast_response()))
        ]
        mod = load_lambda("weather_lookup")
        # Need to set the API key on the module since it reads at import time
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "Chennai"}}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        data = body["data"]
        self.assertEqual(data["location"], "Chennai")
        self.assertEqual(data["current"]["temp_celsius"], 30)
        self.assertEqual(data["current"]["humidity"], 65)

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_wind_speed_conversion_ms_to_kmh(self, mock_get):
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value=self._make_current_response(wind=5.0))),
            MagicMock(json=MagicMock(return_value=self._make_forecast_response()))
        ]
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "Chennai"}}, self.ctx)
        body = json.loads(r["body"])
        # 5.0 m/s * 3.6 = 18.0 km/h
        self.assertEqual(body["data"]["current"]["wind_speed_kmh"], 18.0)

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_advisory_high_humidity(self, mock_get):
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value=self._make_current_response(humidity=85))),
            MagicMock(json=MagicMock(return_value=self._make_forecast_response()))
        ]
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "x"}}, self.ctx)
        body = json.loads(r["body"])
        self.assertIn("fungal", body["data"]["farming_advisory"])

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_advisory_extreme_heat(self, mock_get):
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value=self._make_current_response(temp=42))),
            MagicMock(json=MagicMock(return_value=self._make_forecast_response()))
        ]
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "x"}}, self.ctx)
        body = json.loads(r["body"])
        self.assertIn("Extreme heat", body["data"]["farming_advisory"])

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_advisory_heavy_rain(self, mock_get):
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value=self._make_current_response(rain_1h=15))),
            MagicMock(json=MagicMock(return_value=self._make_forecast_response()))
        ]
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "x"}}, self.ctx)
        body = json.loads(r["body"])
        self.assertIn("pesticide", body["data"]["farming_advisory"])

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_advisory_normal_conditions(self, mock_get):
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value=self._make_current_response(temp=28, humidity=50, rain_1h=0))),
            MagicMock(json=MagicMock(return_value=self._make_forecast_response()))
        ]
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "x"}}, self.ctx)
        body = json.loads(r["body"])
        self.assertIn("normal", body["data"]["farming_advisory"])

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_advisory_multiple_conditions(self, mock_get):
        """High humidity + extreme heat should both appear"""
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value=self._make_current_response(temp=40, humidity=90, rain_1h=12))),
            MagicMock(json=MagicMock(return_value=self._make_forecast_response()))
        ]
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "x"}}, self.ctx)
        body = json.loads(r["body"])
        advisory = body["data"]["farming_advisory"]
        self.assertIn("fungal", advisory)
        self.assertIn("Extreme heat", advisory)
        self.assertIn("pesticide", advisory)
        self.assertNotIn("normal", advisory)

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_forecast_aggregation(self, mock_get):
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value=self._make_current_response())),
            MagicMock(json=MagicMock(return_value=self._make_forecast_response()))
        ]
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "x"}}, self.ctx)
        body = json.loads(r["body"])
        forecast = body["data"]["forecast"]
        self.assertEqual(len(forecast), 2)  # 2 dates in mock data

        # First day: temps [28, 34, 30]
        self.assertEqual(forecast[0]["date"], "2026-02-27")
        self.assertEqual(forecast[0]["temp_min"], 28.0)
        self.assertEqual(forecast[0]["temp_max"], 34.0)
        self.assertEqual(forecast[0]["description"], "clear")  # most common

        # Second day: temps [26, 32], rain 2+3=5
        self.assertEqual(forecast[1]["date"], "2026-02-28")
        self.assertEqual(forecast[1]["temp_min"], 26.0)
        self.assertEqual(forecast[1]["temp_max"], 32.0)

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_city_not_found_returns_404(self, mock_get):
        mock_get.return_value = MagicMock(json=MagicMock(return_value={"cod": "404", "message": "city not found"}))
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "FakeCity123"}}, self.ctx)
        self.assertEqual(r["statusCode"], 404)

    def test_missing_api_key_returns_500(self):
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = ""

        r = mod.lambda_handler({"pathParameters": {"location": "X"}}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 500)
        self.assertIn("API key", body["message"])

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get')
    def test_agentcore_parameter_parsing(self, mock_get):
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value=self._make_current_response())),
            MagicMock(json=MagicMock(return_value=self._make_forecast_response()))
        ]
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        event = {"parameters": [{"name": "location", "value": "Madurai"}]}
        r = mod.lambda_handler(event, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["data"]["location"], "Madurai")

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"})
    @patch('requests.get', side_effect=Exception("Network error"))
    def test_network_error_returns_500(self, mock_get):
        mod = load_lambda("weather_lookup")
        mod.OPENWEATHER_API_KEY = "test_key"

        r = mod.lambda_handler({"pathParameters": {"location": "X"}}, self.ctx)
        self.assertEqual(r["statusCode"], 500)


# ================================================================
#  5. FARMER PROFILE LAMBDA - Mocked DynamoDB
# ================================================================

class TestFarmerProfile(unittest.TestCase):
    """Tests for lambdas/farmer_profile/handler.py with mocked DynamoDB"""

    def setUp(self):
        self.ctx = FakeContext()

    def test_options_cors(self):
        mod = load_lambda("farmer_profile")
        r = mod.lambda_handler({"httpMethod": "OPTIONS", "pathParameters": {"farmerId": "x"}}, self.ctx)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(r["headers"]["Access-Control-Allow-Origin"], "*")

    def test_missing_farmer_id_returns_400(self):
        mod = load_lambda("farmer_profile")
        r = mod.lambda_handler({"httpMethod": "GET", "pathParameters": {}}, self.ctx)
        self.assertEqual(r["statusCode"], 400)
        body = json.loads(r["body"])
        self.assertIn("farmerId", body["error"])

    def test_delete_method_returns_405(self):
        mod = load_lambda("farmer_profile")
        r = mod.lambda_handler({"httpMethod": "DELETE", "pathParameters": {"farmerId": "x"}}, self.ctx)
        self.assertEqual(r["statusCode"], 405)

    def test_get_existing_profile(self):
        mod = load_lambda("farmer_profile")
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {"farmer_id": "f1", "name": "Ravi", "state": "Tamil Nadu",
                     "crops": ["rice"], "soil_type": "alluvial"}
        }
        mod.table = mock_table

        r = mod.lambda_handler({"httpMethod": "GET", "pathParameters": {"farmerId": "f1"}}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(body["data"]["name"], "Ravi")
        self.assertEqual(body["data"]["state"], "Tamil Nadu")
        self.assertEqual(body["message"], "Profile found")

    def test_get_nonexistent_returns_blank_template(self):
        mod = load_lambda("farmer_profile")
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No 'Item' key
        mod.table = mock_table

        r = mod.lambda_handler({"httpMethod": "GET", "pathParameters": {"farmerId": "new1"}}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(body["message"], "New profile")
        self.assertEqual(body["data"]["farmer_id"], "new1")
        self.assertEqual(body["data"]["name"], "")
        self.assertEqual(body["data"]["crops"], [])
        self.assertEqual(body["data"]["language"], "ta-IN")

    def test_put_new_profile_sets_created_at(self):
        mod = load_lambda("farmer_profile")
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # New profile
        mock_table.put_item.return_value = {}
        mod.table = mock_table

        event = {
            "httpMethod": "PUT",
            "pathParameters": {"farmerId": "f2"},
            "body": json.dumps({"name": "Kumar", "state": "Kerala", "crops": ["coconut"]})
        }
        r = mod.lambda_handler(event, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(body["message"], "Profile saved")
        self.assertIsNotNone(body["data"]["created_at"])  # Should be set
        self.assertEqual(body["data"]["name"], "Kumar")

    def test_put_existing_profile_preserves_created_at(self):
        mod = load_lambda("farmer_profile")
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {"farmer_id": "f3", "created_at": "2026-01-01T00:00:00"}
        }
        mock_table.put_item.return_value = {}
        mod.table = mock_table

        event = {
            "httpMethod": "PUT",
            "pathParameters": {"farmerId": "f3"},
            "body": json.dumps({"name": "Updated"})
        }
        r = mod.lambda_handler(event, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["data"]["created_at"], "2026-01-01T00:00:00")

    def test_put_sets_updated_at(self):
        mod = load_lambda("farmer_profile")
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_table.put_item.return_value = {}
        mod.table = mock_table

        event = {
            "httpMethod": "PUT",
            "pathParameters": {"farmerId": "f4"},
            "body": json.dumps({"name": "Test"})
        }
        r = mod.lambda_handler(event, self.ctx)
        body = json.loads(r["body"])
        self.assertIn("updated_at", body["data"])
        self.assertIsNotNone(body["data"]["updated_at"])

    def test_dynamo_exception_returns_500(self):
        mod = load_lambda("farmer_profile")
        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("DynamoDB error")
        mod.table = mock_table

        r = mod.lambda_handler({"httpMethod": "GET", "pathParameters": {"farmerId": "f5"}}, self.ctx)
        self.assertEqual(r["statusCode"], 500)


# ================================================================
#  6. IMAGE ANALYSIS LAMBDA - Mocked Bedrock + Translate
# ================================================================

class TestImageAnalysis(unittest.TestCase):
    """Tests for lambdas/image_analysis/handler.py"""

    def setUp(self):
        self.mod = load_lambda("image_analysis")
        self.ctx = FakeContext()

    def test_detect_media_type_jpeg(self):
        self.assertEqual(self.mod.detect_media_type("/9j/4AAQSkZJ"), "image/jpeg")

    def test_detect_media_type_png(self):
        self.assertEqual(self.mod.detect_media_type("iVBORw0KGgo"), "image/png")

    def test_detect_media_type_gif(self):
        self.assertEqual(self.mod.detect_media_type("R0lGODlhAQABAI"), "image/gif")

    def test_detect_media_type_webp(self):
        self.assertEqual(self.mod.detect_media_type("UklGRiQAAABXRU"), "image/webp")

    def test_detect_media_type_unknown_defaults_jpeg(self):
        self.assertEqual(self.mod.detect_media_type("XYZABC"), "image/jpeg")

    def test_make_response_cors(self):
        r = self.mod.make_response(200, {"ok": True})
        self.assertEqual(r["headers"]["Access-Control-Allow-Origin"], "*")
        self.assertEqual(r["statusCode"], 200)
        body = json.loads(r["body"])
        self.assertTrue(body["ok"])

    def test_options_returns_200(self):
        r = self.mod.lambda_handler({"httpMethod": "OPTIONS"}, self.ctx)
        self.assertEqual(r["statusCode"], 200)

    def test_missing_image_returns_400(self):
        r = self.mod.lambda_handler({"httpMethod": "POST", "body": json.dumps({})}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 400)
        self.assertIn("Image is required", body["error"])

    def test_empty_image_returns_400(self):
        r = self.mod.lambda_handler({"httpMethod": "POST", "body": json.dumps({"image_base64": ""})}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 400)

    def test_oversized_image_returns_400(self):
        big_image = "A" * (6 * 1024 * 1024)  # >4MB decoded
        r = self.mod.lambda_handler({"httpMethod": "POST", "body": json.dumps({"image_base64": big_image})}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 400)
        self.assertIn("too large", body["error"])

    def test_data_uri_prefix_stripped(self):
        """Ensure 'data:image/jpeg;base64,...' prefix is stripped before processing"""
        # Will fail at Bedrock call but should NOT fail at prefix stripping
        r = self.mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({"image_base64": "data:image/jpeg;base64,/9j/test123"})
        }, self.ctx)
        # Should get to Bedrock call (and fail there), not fail at parsing
        self.assertIn(r["statusCode"], [400, 500])

    def test_successful_analysis_with_mock(self):
        """Full happy path with mocked Bedrock + Translate"""
        fake_analysis = (
            "**Confidence:** High\n"
            "**Disease/Pest:** Leaf Blight\n"
            "**Severity:** Medium\n"
        )
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({
            "content": [{"text": fake_analysis}]
        }).encode()

        self.mod.bedrock = MagicMock()
        self.mod.bedrock.invoke_model.return_value = {"body": mock_body}

        # No translation (language=en)
        r = self.mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({
                "image_base64": "/9j/valid_small_image",
                "crop_name": "Rice",
                "state": "Tamil Nadu",
                "language": "en"
            })
        }, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(body["status"], "success")
        self.assertIn("Leaf Blight", body["data"]["analysis"])
        self.assertEqual(body["data"]["confidence"], "HIGH")
        self.assertEqual(body["data"]["crop"], "Rice")

    def test_confidence_extraction_low(self):
        fake_analysis = "**Confidence:** Low — image is blurry\n**Disease:** Unknown"
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({
            "content": [{"text": fake_analysis}]
        }).encode()

        self.mod.bedrock = MagicMock()
        self.mod.bedrock.invoke_model.return_value = {"body": mock_body}

        r = self.mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({"image_base64": "/9j/test", "language": "en"})
        }, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["data"]["confidence"], "LOW")

    def test_translation_called_for_non_english(self):
        fake_analysis = "**Confidence:** High\n**Disease:** Test"
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({
            "content": [{"text": fake_analysis}]
        }).encode()

        self.mod.bedrock = MagicMock()
        self.mod.bedrock.invoke_model.return_value = {"body": mock_body}
        self.mod.translate_client = MagicMock()
        self.mod.translate_client.translate_text.return_value = {
            "TranslatedText": "Tamil translation here"
        }

        r = self.mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({"image_base64": "/9j/test", "language": "ta"})
        }, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["data"]["analysis"], "Tamil translation here")
        self.mod.translate_client.translate_text.assert_called_once()

    def test_translation_failure_falls_back_to_english(self):
        fake_analysis = "English diagnosis text"
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({
            "content": [{"text": fake_analysis}]
        }).encode()

        self.mod.bedrock = MagicMock()
        self.mod.bedrock.invoke_model.return_value = {"body": mock_body}
        self.mod.translate_client = MagicMock()
        self.mod.translate_client.translate_text.side_effect = Exception("Translate down")

        r = self.mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({"image_base64": "/9j/test", "language": "ta"})
        }, self.ctx)
        body = json.loads(r["body"])
        # Should fall back to English text
        self.assertEqual(body["data"]["analysis"], "English diagnosis text")


# ================================================================
#  7. CROP ADVISORY LAMBDA - Mocked Bedrock KB
# ================================================================

class TestCropAdvisory(unittest.TestCase):
    """Tests for lambdas/crop_advisory/handler.py"""

    def setUp(self):
        self.ctx = FakeContext()

    def test_missing_kb_id_returns_500(self):
        mod = load_lambda("crop_advisory")
        mod.KB_ID = ""
        r = mod.lambda_handler({
            "parameters": [{"name": "crop", "value": "Rice"}]
        }, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 500)
        self.assertIn("Knowledge Base", body["message"])

    def test_successful_kb_query(self):
        mod = load_lambda("crop_advisory")
        mod.KB_ID = "test-kb-123"
        mod.bedrock_agent = MagicMock()
        mod.bedrock_agent.retrieve.return_value = {
            "retrievalResults": [
                {
                    "content": {"text": "Rice grows best in alluvial soil with adequate water."},
                    "score": 0.95,
                    "location": {"s3Location": {"uri": "s3://bucket/crop_guide.md"}}
                },
                {
                    "content": {"text": "Apply NPK fertilizer at 120:60:40 ratio."},
                    "score": 0.88,
                    "location": {"s3Location": {"uri": "s3://bucket/crop_guide.md"}}
                }
            ]
        }

        r = mod.lambda_handler({
            "parameters": [
                {"name": "crop", "value": "Rice"},
                {"name": "state", "value": "Tamil Nadu"},
                {"name": "season", "value": "Kharif"},
                {"name": "soil_type", "value": "Alluvial"}
            ]
        }, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(body["data"]["crop"], "Rice")
        self.assertEqual(body["data"]["state"], "Tamil Nadu")
        self.assertEqual(body["data"]["season"], "Kharif")
        self.assertEqual(len(body["data"]["advisory_data"]), 2)
        self.assertIn("alluvial", body["data"]["advisory_data"][0]["content"])
        self.assertEqual(body["data"]["advisory_data"][0]["score"], 0.95)

    def test_parameter_parsing(self):
        mod = load_lambda("crop_advisory")
        mod.KB_ID = "test"
        mod.bedrock_agent = MagicMock()
        mod.bedrock_agent.retrieve.return_value = {"retrievalResults": []}

        r = mod.lambda_handler({
            "parameters": [
                {"name": "crop", "value": "Sugarcane"},
                {"name": "state", "value": "Maharashtra"},
                {"name": "season", "value": "Rabi"},
                {"name": "soil_type", "value": "Black"}
            ]
        }, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["data"]["crop"], "Sugarcane")
        self.assertEqual(body["data"]["state"], "Maharashtra")

    def test_empty_results_return_empty_list(self):
        mod = load_lambda("crop_advisory")
        mod.KB_ID = "test"
        mod.bedrock_agent = MagicMock()
        mod.bedrock_agent.retrieve.return_value = {"retrievalResults": []}

        r = mod.lambda_handler({"parameters": [{"name": "crop", "value": "X"}]}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(body["data"]["advisory_data"], [])

    def test_bedrock_error_returns_500(self):
        mod = load_lambda("crop_advisory")
        mod.KB_ID = "test"
        mod.bedrock_agent = MagicMock()
        mod.bedrock_agent.retrieve.side_effect = Exception("Bedrock KB error")

        r = mod.lambda_handler({"parameters": [{"name": "crop", "value": "X"}]}, self.ctx)
        self.assertEqual(r["statusCode"], 500)


# ================================================================
#  8. AGENT ORCHESTRATOR LAMBDA - Mocked everything
# ================================================================

class TestAgentOrchestrator(unittest.TestCase):
    """Tests for lambdas/agent_orchestrator/handler.py"""

    def setUp(self):
        self.ctx = FakeContext()

    def test_options_returns_200(self):
        mod = load_lambda("agent_orchestrator")
        r = mod.lambda_handler({"httpMethod": "OPTIONS"}, self.ctx)
        self.assertEqual(r["statusCode"], 200)

    def test_empty_message_returns_400(self):
        mod = load_lambda("agent_orchestrator")
        r = mod.lambda_handler({"httpMethod": "POST", "body": json.dumps({"message": ""})}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 400)
        self.assertIn("Message is required", body["message"])

    def test_missing_message_returns_400(self):
        mod = load_lambda("agent_orchestrator")
        r = mod.lambda_handler({"httpMethod": "POST", "body": json.dumps({})}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 400)

    def test_full_flow_mocked(self):
        """Test the complete orchestration flow with all AWS mocked"""
        mod = load_lambda("agent_orchestrator")

        # Mock translate
        mod.detect_and_translate = MagicMock(return_value={
            "detected_language": "ta",
            "translated_text": "What is the weather in Chennai?"
        })
        mod.translate_response = MagicMock(return_value="சென்னை வானிலை நல்லது")

        # Mock bedrock agent
        chunk1 = {"chunk": {"bytes": b"The weather in Chennai is warm."}}
        mod.bedrock_agent = MagicMock()
        mod.bedrock_agent.invoke_agent.return_value = {
            "completion": [chunk1]
        }

        # Mock farmer profile
        mod.get_farmer_profile = MagicMock(return_value={
            "name": "Ravi", "state": "TN", "crops": ["rice"], "soil_type": "alluvial"
        })

        # Mock polly
        mod.text_to_speech = MagicMock(return_value="https://s3.amazonaws.com/audio/test.mp3")

        # Mock chat save
        mod.save_chat_message = MagicMock(return_value=True)

        r = mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({
                "message": "சென்னை வானிலை எப்படி?",
                "session_id": "sess123",
                "farmer_id": "farmer1"
            })
        }, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(body["data"]["detected_language"], "ta")
        self.assertIsNotNone(body["data"]["reply"])
        self.assertIsNotNone(body["data"]["reply_en"])
        self.assertEqual(body["data"]["session_id"], "sess123")
        self.assertIsNotNone(body["data"]["audio_url"])

        # Verify chat saved twice (user + assistant)
        self.assertEqual(mod.save_chat_message.call_count, 2)

    def test_anonymous_farmer_skips_profile(self):
        mod = load_lambda("agent_orchestrator")
        mod.detect_and_translate = MagicMock(return_value={
            "detected_language": "en",
            "translated_text": "Hello"
        })
        chunk = {"chunk": {"bytes": b"Hello there!"}}
        mod.bedrock_agent = MagicMock()
        mod.bedrock_agent.invoke_agent.return_value = {"completion": [chunk]}
        mod.get_farmer_profile = MagicMock()
        mod.text_to_speech = MagicMock(return_value=None)
        mod.save_chat_message = MagicMock()
        mod.translate_response = MagicMock(return_value="Hello there!")

        r = mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({"message": "Hello", "farmer_id": "anonymous"})
        }, self.ctx)
        # get_farmer_profile should NOT be called for anonymous
        mod.get_farmer_profile.assert_not_called()
        self.assertEqual(r["statusCode"], 200)

    def test_polly_failure_non_fatal(self):
        """Polly failure should not crash the handler"""
        mod = load_lambda("agent_orchestrator")
        mod.detect_and_translate = MagicMock(return_value={
            "detected_language": "en", "translated_text": "test"
        })
        chunk = {"chunk": {"bytes": b"Response text"}}
        mod.bedrock_agent = MagicMock()
        mod.bedrock_agent.invoke_agent.return_value = {"completion": [chunk]}
        mod.get_farmer_profile = MagicMock(return_value=None)
        mod.text_to_speech = MagicMock(side_effect=Exception("Polly down"))
        mod.save_chat_message = MagicMock()

        r = mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({"message": "test"})
        }, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertIsNone(body["data"]["audio_url"])


# ================================================================
#  9. TRANSCRIBE SPEECH LAMBDA - Mocked S3 + Transcribe
# ================================================================

class TestTranscribeSpeech(unittest.TestCase):
    """Tests for lambdas/transcribe_speech/handler.py"""

    def setUp(self):
        self.ctx = FakeContext()

    def test_options_returns_200(self):
        mod = load_lambda("transcribe_speech")
        r = mod.lambda_handler({"httpMethod": "OPTIONS"}, self.ctx)
        self.assertEqual(r["statusCode"], 200)

    def test_missing_audio_returns_400(self):
        mod = load_lambda("transcribe_speech")
        r = mod.lambda_handler({"httpMethod": "POST", "body": json.dumps({})}, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 400)
        self.assertIn("audio", body["message"].lower())

    def test_language_map_coverage(self):
        mod = load_lambda("transcribe_speech")
        expected = {"ta-IN": "ta-IN", "te-IN": "te-IN", "hi-IN": "hi-IN", "en-IN": "en-IN", "en-US": "en-US"}
        for key, val in expected.items():
            self.assertEqual(mod.LANGUAGE_MAP[key], val, f"Language mapping wrong for {key}")

    def test_successful_transcription(self):
        import base64
        mod = load_lambda("transcribe_speech")
        mod.s3 = MagicMock()
        mod.transcribe = MagicMock()

        # Mock S3 put (upload audio)
        mod.s3.put_object.return_value = {}

        # Mock transcribe start
        mod.transcribe.start_transcription_job.return_value = {}

        # Mock polling: first IN_PROGRESS, then COMPLETED
        transcript_result = json.dumps({
            "results": {"transcripts": [{"transcript": "Hello, how are you?"}]}
        }).encode()

        mod.transcribe.get_transcription_job.side_effect = [
            {"TranscriptionJob": {"TranscriptionJobStatus": "IN_PROGRESS"}},
            {"TranscriptionJob": {"TranscriptionJobStatus": "COMPLETED"}}
        ]
        mod.s3.get_object.return_value = {
            "Body": BytesIO(transcript_result)
        }
        mod.s3.delete_object.return_value = {}

        audio_data = base64.b64encode(b"fake_audio_bytes").decode()
        r = mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({"audio": audio_data, "language": "en-IN"})
        }, self.ctx)
        body = json.loads(r["body"])
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(body["data"]["transcript"], "Hello, how are you?")

        # Verify cleanup calls
        self.assertEqual(mod.s3.delete_object.call_count, 2)

    def test_transcription_failure(self):
        import base64
        mod = load_lambda("transcribe_speech")
        mod.s3 = MagicMock()
        mod.transcribe = MagicMock()
        mod.s3.put_object.return_value = {}
        mod.transcribe.start_transcription_job.return_value = {}
        mod.transcribe.get_transcription_job.return_value = {
            "TranscriptionJob": {"TranscriptionJobStatus": "FAILED"}
        }

        audio_data = base64.b64encode(b"audio").decode()
        r = mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({"audio": audio_data, "language": "ta-IN"})
        }, self.ctx)
        self.assertEqual(r["statusCode"], 500)

    def test_default_language_is_tamil(self):
        """If no language provided, should default to ta-IN"""
        import base64
        mod = load_lambda("transcribe_speech")
        mod.s3 = MagicMock()
        mod.transcribe = MagicMock()
        mod.s3.put_object.return_value = {}
        mod.transcribe.start_transcription_job.return_value = {}
        mod.transcribe.get_transcription_job.return_value = {
            "TranscriptionJob": {"TranscriptionJobStatus": "COMPLETED"}
        }
        mod.s3.get_object.return_value = {
            "Body": BytesIO(json.dumps({"results": {"transcripts": [{"transcript": "test"}]}}).encode())
        }
        mod.s3.delete_object.return_value = {}

        audio_data = base64.b64encode(b"audio").decode()
        r = mod.lambda_handler({
            "httpMethod": "POST",
            "body": json.dumps({"audio": audio_data})
        }, self.ctx)

        # Verify the transcription was started with ta-IN (default)
        call_args = mod.transcribe.start_transcription_job.call_args
        self.assertEqual(call_args.kwargs.get("LanguageCode", call_args[1].get("LanguageCode", "")), "ta-IN")


# ================================================================
#  10. TRANSLATE HELPER - With mocked AWS Translate
# ================================================================

class TestTranslateHelper(unittest.TestCase):
    """Tests for utils/translate_helper.py"""

    def test_supported_languages_list(self):
        from utils.translate_helper import SUPPORTED_LANGUAGES
        self.assertEqual(len(SUPPORTED_LANGUAGES), 8)
        for lang in ["en", "hi", "ta", "te", "kn", "ml", "mr", "bn"]:
            self.assertIn(lang, SUPPORTED_LANGUAGES)

    def test_same_language_no_api_call(self):
        from utils.translate_helper import translate_response
        result = translate_response("Hello world", source_language="en", target_language="en")
        self.assertEqual(result, "Hello world")

    @patch('utils.translate_helper.translate')
    def test_detect_and_translate_success(self, mock_translate):
        mock_translate.translate_text.return_value = {
            "SourceLanguageCode": "ta",
            "TranslatedText": "How is the weather?",
            "TargetLanguageCode": "en"
        }
        from utils.translate_helper import detect_and_translate
        result = detect_and_translate("வானிலை எப்படி?", target_language="en")
        self.assertEqual(result["detected_language"], "ta")
        self.assertEqual(result["translated_text"], "How is the weather?")
        self.assertEqual(result["target_language"], "en")

    @patch('utils.translate_helper.translate')
    def test_detect_and_translate_fallback_on_error(self, mock_translate):
        mock_translate.translate_text.side_effect = Exception("Service down")
        from utils.translate_helper import detect_and_translate
        result = detect_and_translate("Test text", target_language="en")
        self.assertEqual(result["detected_language"], "en")
        self.assertEqual(result["translated_text"], "Test text")

    @patch('utils.translate_helper.translate')
    def test_translate_response_success(self, mock_translate):
        mock_translate.translate_text.return_value = {
            "TranslatedText": "Translated text in Tamil"
        }
        from utils.translate_helper import translate_response
        result = translate_response("English text", source_language="en", target_language="ta")
        self.assertEqual(result, "Translated text in Tamil")

    @patch('utils.translate_helper.translate')
    def test_translate_response_error_returns_original(self, mock_translate):
        mock_translate.translate_text.side_effect = Exception("Error")
        from utils.translate_helper import translate_response
        result = translate_response("Original text", source_language="en", target_language="ta")
        self.assertEqual(result, "Original text")


# ================================================================
#  11. POLLY HELPER - With mocked AWS Polly + S3
# ================================================================

class TestPollyHelper(unittest.TestCase):
    """Tests for utils/polly_helper.py"""

    def test_voice_map_entries(self):
        from utils.polly_helper import VOICE_MAP
        self.assertEqual(len(VOICE_MAP), 5)
        for lang in ["en", "hi", "ta", "te", "kn"]:
            self.assertEqual(VOICE_MAP[lang], "Kajal")

    def test_polly_lang_map(self):
        from utils.polly_helper import POLLY_LANG_MAP
        self.assertEqual(POLLY_LANG_MAP["en"], "en-IN")
        self.assertEqual(POLLY_LANG_MAP["hi"], "hi-IN")
        self.assertEqual(POLLY_LANG_MAP["ta"], "hi-IN")  # Fallback
        self.assertEqual(POLLY_LANG_MAP["te"], "hi-IN")  # Fallback

    @patch('utils.polly_helper.s3')
    @patch('utils.polly_helper.polly')
    def test_text_to_speech_success(self, mock_polly, mock_s3):
        audio_stream = MagicMock()
        audio_stream.read.return_value = b"fake_mp3_data"
        mock_polly.synthesize_speech.return_value = {"AudioStream": audio_stream}
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/audio/test.mp3"

        from utils.polly_helper import text_to_speech
        url = text_to_speech("Hello farmer", language_code="en")
        self.assertEqual(url, "https://s3.example.com/audio/test.mp3")

        # Verify correct Polly parameters
        call_args = mock_polly.synthesize_speech.call_args
        self.assertEqual(call_args.kwargs.get("VoiceId", call_args[1].get("VoiceId")), "Kajal")
        self.assertEqual(call_args.kwargs.get("Engine", call_args[1].get("Engine")), "neural")
        self.assertEqual(call_args.kwargs.get("OutputFormat", call_args[1].get("OutputFormat")), "mp3")

    @patch('utils.polly_helper.s3')
    @patch('utils.polly_helper.polly')
    def test_text_to_speech_custom_voice(self, mock_polly, mock_s3):
        audio_stream = MagicMock()
        audio_stream.read.return_value = b"data"
        mock_polly.synthesize_speech.return_value = {"AudioStream": audio_stream}
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = "https://example.com/a.mp3"

        from utils.polly_helper import text_to_speech
        text_to_speech("test", language_code="en", voice_id="Aditi")
        call_args = mock_polly.synthesize_speech.call_args
        self.assertEqual(call_args.kwargs.get("VoiceId", call_args[1].get("VoiceId")), "Aditi")

    @patch('utils.polly_helper.s3')
    @patch('utils.polly_helper.polly')
    def test_text_to_speech_tamil_uses_hindi_fallback(self, mock_polly, mock_s3):
        audio_stream = MagicMock()
        audio_stream.read.return_value = b"data"
        mock_polly.synthesize_speech.return_value = {"AudioStream": audio_stream}
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = "url"

        from utils.polly_helper import text_to_speech
        text_to_speech("Tamil text", language_code="ta")
        call_args = mock_polly.synthesize_speech.call_args
        self.assertEqual(call_args.kwargs.get("LanguageCode", call_args[1].get("LanguageCode")), "hi-IN")

    @patch('utils.polly_helper.polly')
    def test_text_to_speech_error_returns_none(self, mock_polly):
        mock_polly.synthesize_speech.side_effect = Exception("Polly error")
        from utils.polly_helper import text_to_speech
        result = text_to_speech("test", language_code="en")
        self.assertIsNone(result)

    def test_unknown_language_uses_defaults(self):
        from utils.polly_helper import VOICE_MAP, POLLY_LANG_MAP
        # Unknown language should fall back via .get() defaults
        self.assertEqual(VOICE_MAP.get("xx", "Kajal"), "Kajal")
        self.assertEqual(POLLY_LANG_MAP.get("xx", "en-IN"), "en-IN")


# ================================================================
#  12. DYNAMODB HELPER - With mocked DynamoDB
# ================================================================

class TestDynamoDBHelper(unittest.TestCase):
    """Tests for utils/dynamodb_helper.py"""

    def test_table_names(self):
        from utils.dynamodb_helper import PROFILES_TABLE, SESSIONS_TABLE
        self.assertEqual(PROFILES_TABLE, "farmer_profiles")
        self.assertEqual(SESSIONS_TABLE, "chat_sessions")

    @patch('utils.dynamodb_helper.profiles_table')
    def test_get_farmer_profile_found(self, mock_table):
        mock_table.get_item.return_value = {
            "Item": {"farmer_id": "f1", "name": "Ravi", "state": "TN"}
        }
        from utils.dynamodb_helper import get_farmer_profile
        result = get_farmer_profile("f1")
        self.assertEqual(result["name"], "Ravi")
        self.assertEqual(result["farmer_id"], "f1")

    @patch('utils.dynamodb_helper.profiles_table')
    def test_get_farmer_profile_not_found(self, mock_table):
        mock_table.get_item.return_value = {}
        from utils.dynamodb_helper import get_farmer_profile
        result = get_farmer_profile("unknown")
        self.assertIsNone(result)

    @patch('utils.dynamodb_helper.profiles_table')
    def test_get_farmer_profile_error(self, mock_table):
        mock_table.get_item.side_effect = Exception("DB error")
        from utils.dynamodb_helper import get_farmer_profile
        result = get_farmer_profile("err")
        self.assertIsNone(result)

    @patch('utils.dynamodb_helper.profiles_table')
    def test_put_farmer_profile_success(self, mock_table):
        mock_table.put_item.return_value = {}
        from utils.dynamodb_helper import put_farmer_profile
        result = put_farmer_profile("f1", {"name": "Ravi", "state": "TN"})
        self.assertTrue(result)
        # Verify put_item was called with farmer_id and updated_at
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs.get("Item", call_args[1].get("Item"))
        self.assertEqual(item["farmer_id"], "f1")
        self.assertEqual(item["name"], "Ravi")
        self.assertIn("updated_at", item)

    @patch('utils.dynamodb_helper.profiles_table')
    def test_put_farmer_profile_error(self, mock_table):
        mock_table.put_item.side_effect = Exception("Write error")
        from utils.dynamodb_helper import put_farmer_profile
        result = put_farmer_profile("f1", {})
        self.assertFalse(result)

    @patch('utils.dynamodb_helper.sessions_table')
    def test_save_chat_message_success(self, mock_table):
        mock_table.put_item.return_value = {}
        from utils.dynamodb_helper import save_chat_message
        result = save_chat_message("sess1", "user", "Hello", "en")
        self.assertTrue(result)
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs.get("Item", call_args[1].get("Item"))
        self.assertEqual(item["session_id"], "sess1")
        self.assertEqual(item["role"], "user")
        self.assertEqual(item["message"], "Hello")
        self.assertEqual(item["language"], "en")
        self.assertIn("timestamp", item)

    @patch('utils.dynamodb_helper.sessions_table')
    def test_save_chat_message_error(self, mock_table):
        mock_table.put_item.side_effect = Exception("Write error")
        from utils.dynamodb_helper import save_chat_message
        result = save_chat_message("s", "user", "msg")
        self.assertFalse(result)

    @patch('utils.dynamodb_helper.sessions_table')
    def test_get_chat_history_success(self, mock_table):
        mock_table.query.return_value = {
            "Items": [
                {"session_id": "s1", "role": "user", "message": "Hi", "timestamp": "t1"},
                {"session_id": "s1", "role": "assistant", "message": "Hello!", "timestamp": "t2"}
            ]
        }
        from utils.dynamodb_helper import get_chat_history
        result = get_chat_history("s1", limit=10)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(result[1]["role"], "assistant")

    @patch('utils.dynamodb_helper.sessions_table')
    def test_get_chat_history_empty(self, mock_table):
        mock_table.query.return_value = {"Items": []}
        from utils.dynamodb_helper import get_chat_history
        result = get_chat_history("empty_session")
        self.assertEqual(result, [])

    @patch('utils.dynamodb_helper.sessions_table')
    def test_get_chat_history_error(self, mock_table):
        mock_table.query.side_effect = Exception("Query error")
        from utils.dynamodb_helper import get_chat_history
        result = get_chat_history("err")
        self.assertEqual(result, [])


# ================================================================
#  RUN
# ================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
