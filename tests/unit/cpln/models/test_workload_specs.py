import unittest

from cpln.models.workload_specs import WorkloadAutoscaling, WorkloadSpecState


class TestWorkloadAutoscaling(unittest.TestCase):
    """Tests for the WorkloadAutoscaling class"""

    def setUp(self):
        """Set up the test"""
        self.autoscaling = WorkloadAutoscaling(
            metric="cpu",
            target=80,
            max_scale=10,
            min_scale=1,
            max_concurrency=100,
            scale_to_zero_delay=300,
        )

    def test_initialization(self):
        """Test autoscaling initialization"""
        self.assertEqual(self.autoscaling.metric, "cpu")
        self.assertEqual(self.autoscaling.target, 80)
        self.assertEqual(self.autoscaling.max_scale, 10)
        self.assertEqual(self.autoscaling.min_scale, 1)
        self.assertEqual(self.autoscaling.max_concurrency, 100)
        self.assertEqual(self.autoscaling.scale_to_zero_delay, 300)


class TestWorkloadSpecState(unittest.TestCase):
    """Tests for the WorkloadSpecState class"""

    def setUp(self):
        """Set up the test"""
        self.spec = {
            "defaultOptions": {
                "debug": True,
                "autoscaling": {
                    "metric": "cpu",
                    "target": 80,
                    "maxScale": 10,
                    "minScale": 1,
                    "maxConcurrency": 100,
                    "scaleToZeroDelay": 300,
                },
                "capacityAI": True,
                "suspend": False,
                "timeoutSeconds": 300,
            }
        }

    def test_parse_from_spec(self):
        """Test parse_from_spec class method"""
        spec_state = WorkloadSpecState.parse_from_spec(self.spec)

        # Test basic attributes
        self.assertTrue(spec_state.debug)
        self.assertTrue(spec_state.capacity_ai)
        self.assertFalse(spec_state.suspend)
        self.assertEqual(spec_state.timeout_seconds, 300)

        # Test autoscaling attributes
        self.assertEqual(spec_state.autoscaling.metric, "cpu")
        self.assertEqual(spec_state.autoscaling.target, 80)
        self.assertEqual(spec_state.autoscaling.max_scale, 10)
        self.assertEqual(spec_state.autoscaling.min_scale, 1)
        self.assertEqual(spec_state.autoscaling.max_concurrency, 100)
        self.assertEqual(spec_state.autoscaling.scale_to_zero_delay, 300)

    def test_parse_from_spec_missing_autoscaling(self):
        """Test parse_from_spec with missing autoscaling options"""
        spec = {
            "defaultOptions": {
                "debug": True,
                "capacityAI": True,
                "suspend": False,
                "timeoutSeconds": 300,
            }
        }

        with self.assertRaises(KeyError):
            WorkloadSpecState.parse_from_spec(spec)

    def test_parse_from_spec_missing_default_options(self):
        """Test parse_from_spec with missing defaultOptions"""
        spec = {}

        with self.assertRaises(KeyError):
            WorkloadSpecState.parse_from_spec(spec)

    def test_parse_from_spec_missing_required_fields(self):
        """Test parse_from_spec with missing required fields"""
        spec = {
            "defaultOptions": {
                "autoscaling": {
                    "metric": "cpu",
                    "target": 80,
                    "maxScale": 10,
                    "minScale": 1,
                    "maxConcurrency": 100,
                    "scaleToZeroDelay": 300,
                }
            }
        }

        with self.assertRaises(KeyError):
            WorkloadSpecState.parse_from_spec(spec)


if __name__ == "__main__":
    unittest.main()
