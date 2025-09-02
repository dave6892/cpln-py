"""Tests for GVC models following unit testing best practices."""

import unittest
from unittest.mock import MagicMock, call, patch

from cpln.models.gvcs import GVC, GVCCollection


class TestGVCInitialization(unittest.TestCase):
    """Test GVC model initialization and basic properties"""

    def test_gvc_initialization_with_all_parameters_sets_attributes_correctly(self):
        """Test that GVC initializes correctly with all parameters"""
        # Arrange
        test_attrs = {
            "name": "test-gvc",
            "description": "Test GVC Description",
            "id": "gvc-123",
        }
        test_client = MagicMock()
        test_collection = MagicMock()
        test_state = {"active": True}

        # Act
        gvc = GVC(
            attrs=test_attrs,
            client=test_client,
            collection=test_collection,
            state=test_state,
        )

        # Assert
        self.assertEqual(gvc.attrs, test_attrs)
        self.assertEqual(gvc.client, test_client)
        self.assertEqual(gvc.collection, test_collection)
        self.assertEqual(gvc.state, test_state)

    def test_gvc_initialization_with_minimal_parameters_uses_defaults(self):
        """Test that GVC initializes correctly with minimal parameters"""
        # Act
        gvc = GVC()

        # Assert
        self.assertEqual(gvc.attrs, {})
        self.assertIsNone(gvc.client)
        self.assertIsNone(gvc.collection)
        self.assertEqual(gvc.state, {})

    def test_gvc_initialization_with_none_attrs_creates_empty_dict(self):
        """Test that GVC handles None attrs parameter correctly"""
        # Act
        gvc = GVC(attrs=None)

        # Assert
        self.assertEqual(gvc.attrs, {})
        self.assertIsInstance(gvc.attrs, dict)

    def test_gvc_initialization_with_none_state_creates_empty_dict(self):
        """Test that GVC handles None state parameter correctly"""
        # Act
        gvc = GVC(state=None)

        # Assert
        self.assertEqual(gvc.state, {})
        self.assertIsInstance(gvc.state, dict)


class TestGVCPropertiesAndBehavior(unittest.TestCase):
    """Test GVC model properties and inherited behavior from Model base class"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "name": "production-gvc",
            "description": "Production GVC",
            "id": "gvc-prod-123",
            "region": "us-west-2",
        }
        self.test_client = MagicMock()
        self.test_collection = MagicMock()
        self.gvc = GVC(
            attrs=self.test_attrs,
            client=self.test_client,
            collection=self.test_collection,
        )

    def test_gvc_id_property_returns_id_from_attrs(self):
        """Test that id property returns the ID from attrs"""
        # Act
        result = self.gvc.id

        # Assert
        self.assertEqual(result, "gvc-prod-123")

    def test_gvc_short_id_property_returns_truncated_id(self):
        """Test that short_id property returns first 12 characters of ID"""
        # Act
        result = self.gvc.short_id

        # Assert
        self.assertEqual(result, "gvc-prod-123")  # Less than 12 chars, so full ID

    def test_gvc_short_id_with_long_id_truncates_correctly(self):
        """Test that short_id properly truncates long IDs"""
        # Arrange
        self.gvc.attrs["id"] = "very-long-gvc-id-that-exceeds-twelve-characters"  # type: ignore

        # Act
        result = self.gvc.short_id

        # Assert
        self.assertEqual(result, "very-long-gv")  # First 12 characters

    def test_gvc_short_id_with_none_id_returns_none(self):
        """Test that short_id returns None when ID is None"""
        # Arrange
        self.gvc.attrs.pop("id")  # type: ignore  # Remove id from attrs

        # Act
        result = self.gvc.short_id

        # Assert
        self.assertIsNone(result)

    def test_gvc_label_property_returns_name_from_attrs(self):
        """Test that label property returns the name from attrs"""
        # Act
        result = self.gvc.label

        # Assert
        self.assertEqual(result, "production-gvc")

    def test_gvc_attribute_access_returns_attrs_values(self):
        """Test that dynamic attribute access returns values from attrs"""
        # Act & Assert
        self.assertEqual(self.gvc.name, "production-gvc")
        self.assertEqual(self.gvc.description, "Production GVC")
        self.assertEqual(self.gvc.region, "us-west-2")

    def test_gvc_attribute_access_with_missing_key_raises_attribute_error(self):
        """Test that accessing missing attributes raises AttributeError"""
        # Act & Assert
        with self.assertRaises(AttributeError) as context:
            _ = self.gvc.nonexistent_attribute

        self.assertIn(
            "'GVC' has no attribute 'nonexistent_attribute'", str(context.exception)
        )

    def test_gvc_repr_includes_short_id_and_label(self):
        """Test that string representation includes short_id and label"""
        # Act
        result = repr(self.gvc)

        # Assert
        self.assertIn("GVC", result)
        self.assertIn("gvc-prod-123", result)
        self.assertIn("production-gvc", result)

    def test_gvc_equality_comparison_with_same_id_returns_true(self):
        """Test that GVCs with same ID are considered equal"""
        # Arrange
        other_gvc = GVC(attrs={"id": "gvc-prod-123", "name": "other-name"})

        # Act & Assert
        self.assertEqual(self.gvc, other_gvc)

    def test_gvc_equality_comparison_with_different_id_returns_false(self):
        """Test that GVCs with different IDs are not considered equal"""
        # Arrange
        other_gvc = GVC(attrs={"id": "different-id", "name": "production-gvc"})

        # Act & Assert
        self.assertNotEqual(self.gvc, other_gvc)

    def test_gvc_equality_comparison_with_different_type_returns_false(self):
        """Test that GVC is not equal to objects of different types"""
        # Act & Assert
        self.assertNotEqual(self.gvc, "not-a-gvc")
        self.assertNotEqual(self.gvc, {"id": "gvc-prod-123"})

    def test_gvc_hash_is_consistent_with_equality(self):
        """Test that hash is consistent with equality comparison"""
        # Arrange
        other_gvc = GVC(attrs={"id": "gvc-prod-123", "name": "other-name"})

        # Act & Assert
        self.assertEqual(hash(self.gvc), hash(other_gvc))


class TestGVCOperations(unittest.TestCase):
    """Test GVC CRUD operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "name": "api-gvc",
            "description": "API GVC for microservices",
            "id": "gvc-api-456",
        }
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.gvc = GVC(
            attrs=self.test_attrs,
            client=self.mock_client,
            collection=self.mock_collection,
        )

    def test_get_operation_calls_client_api_with_gvc_name(self):
        """Test that get() calls the client API with correct GVC name"""
        # Arrange
        expected_response = {
            "name": "api-gvc",
            "description": "API GVC for microservices",
            "metadata": {"createdAt": "2024-01-01T00:00:00Z"},
        }
        self.mock_client.api.get_gvc.return_value = expected_response

        # Act
        result = self.gvc.get()

        # Assert
        self.assertEqual(result, expected_response)
        self.mock_client.api.get_gvc.assert_called_once_with("api-gvc")

    def test_get_operation_with_missing_name_handles_key_error_gracefully(self):
        """Test that get() handles missing name attribute gracefully"""
        # Arrange
        gvc_without_name = GVC(
            attrs={"description": "No name GVC"}, client=self.mock_client
        )

        # Act & Assert
        with self.assertRaises(KeyError):
            gvc_without_name.get()

    @patch("builtins.print")
    def test_create_operation_calls_client_api_and_prints_messages(self, mock_print):
        """Test that create() calls client API and prints appropriate messages"""
        # Act
        self.gvc.create()

        # Assert
        self.mock_client.api.create_gvc.assert_called_once_with(
            "api-gvc", "API GVC for microservices"
        )
        # Verify print statements were called
        expected_calls = [call(f"Creating GVC: {self.gvc}"), call("Created!")]
        mock_print.assert_has_calls(expected_calls)

    @patch("builtins.print")
    def test_create_operation_with_missing_description_uses_none(self, mock_print):
        """Test that create() handles missing description attribute"""
        # Arrange
        gvc_attrs = {"name": "no-desc-gvc"}
        gvc_no_desc = GVC(attrs=gvc_attrs, client=self.mock_client)

        # Act & Assert
        with self.assertRaises(KeyError):
            gvc_no_desc.create()

    @patch("builtins.print")
    def test_delete_operation_calls_client_api_and_prints_messages(self, mock_print):
        """Test that delete() calls client API and prints appropriate messages"""
        # Act
        self.gvc.delete()

        # Assert
        self.mock_client.api.delete_gvc.assert_called_once_with("api-gvc")
        # Verify print statements were called
        expected_calls = [call(f"Deleting GVC: {self.gvc}"), call("Deleted!")]
        mock_print.assert_has_calls(expected_calls)

    def test_reload_operation_updates_attrs_from_collection_get(self):
        """Test that reload() fetches fresh data and updates attrs"""
        # Arrange
        updated_attrs = {
            "name": "api-gvc",
            "description": "Updated API GVC description",
            "status": "active",
        }
        mock_updated_gvc = MagicMock()
        mock_updated_gvc.attrs = updated_attrs
        self.mock_collection.get.return_value = mock_updated_gvc

        # Act
        self.gvc.reload()

        # Assert
        self.mock_collection.get.assert_called_once_with("gvc-api-456")
        self.assertEqual(self.gvc.attrs, updated_attrs)


class TestGVCCollectionInitialization(unittest.TestCase):
    """Test GVCCollection initialization and basic properties"""

    def test_gvc_collection_initialization_with_client_sets_client(self):
        """Test that GVCCollection initializes correctly with client"""
        # Arrange
        test_client = MagicMock()

        # Act
        collection = GVCCollection(client=test_client)

        # Assert
        self.assertEqual(collection.client, test_client)
        self.assertEqual(collection.model, GVC)

    def test_gvc_collection_initialization_without_client_sets_none(self):
        """Test that GVCCollection initializes correctly without client"""
        # Act
        collection = GVCCollection()

        # Assert
        self.assertIsNone(collection.client)
        self.assertEqual(collection.model, GVC)

    def test_gvc_collection_model_attribute_is_gvc_class(self):
        """Test that collection.model points to GVC class"""
        # Act
        collection = GVCCollection()

        # Assert
        self.assertIs(collection.model, GVC)


class TestGVCCollectionOperations(unittest.TestCase):
    """Test GVCCollection operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_client = MagicMock()
        self.collection = GVCCollection(client=self.mock_client)

    def test_get_operation_returns_gvc_instance_with_correct_attributes(self):
        """Test that get() returns GVC instance with data from API"""
        # Arrange
        gvc_name = "test-gvc"
        api_response = {
            "name": "test-gvc",
            "description": "Test GVC",
            "id": "gvc-test-789",
            "status": "active",
        }
        self.mock_client.api.get_gvc.return_value = api_response

        # Act
        result = self.collection.get(gvc_name)

        # Assert
        self.assertIsInstance(result, GVC)
        self.assertEqual(result.attrs, api_response)
        self.assertEqual(result.client, self.mock_client)
        self.assertEqual(result.collection, self.collection)
        self.mock_client.api.get_gvc.assert_called_once_with(gvc_name)

    def test_get_operation_with_empty_name_passes_empty_string(self):
        """Test that get() passes empty string name to API"""
        # Arrange
        self.mock_client.api.get_gvc.return_value = {
            "name": "",
            "description": "Empty name GVC",
        }

        # Act
        result = self.collection.get("")

        # Assert
        self.assertIsInstance(result, GVC)
        self.mock_client.api.get_gvc.assert_called_once_with("")

    def test_list_operation_returns_list_of_gvc_instances(self):
        """Test that list() returns list of GVC instances from API response"""
        # Arrange
        api_response = {
            "items": [
                {"name": "gvc1", "description": "First GVC", "id": "gvc-1"},
                {"name": "gvc2", "description": "Second GVC", "id": "gvc-2"},
                {"name": "gvc3", "description": "Third GVC", "id": "gvc-3"},
            ]
        }
        self.mock_client.api.get_gvc.return_value = api_response

        # Act
        result = self.collection.list()

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

        # Verify each item is a properly configured GVC instance
        for i, gvc in enumerate(result):
            with self.subTest(gvc_index=i):
                self.assertIsInstance(gvc, GVC)
                self.assertEqual(gvc.attrs, api_response["items"][i])
                self.assertEqual(gvc.client, self.mock_client)
                self.assertEqual(gvc.collection, self.collection)

        self.mock_client.api.get_gvc.assert_called_once_with()

    def test_list_operation_with_empty_items_returns_empty_list(self):
        """Test that list() handles empty items array correctly"""
        # Arrange
        api_response = {"items": []}
        self.mock_client.api.get_gvc.return_value = api_response

        # Act
        result = self.collection.list()

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        self.mock_client.api.get_gvc.assert_called_once_with()

    def test_list_operation_with_single_item_returns_single_element_list(self):
        """Test that list() handles single item response correctly"""
        # Arrange
        api_response = {
            "items": [{"name": "solo-gvc", "description": "Only GVC", "id": "gvc-solo"}]
        }
        self.mock_client.api.get_gvc.return_value = api_response

        # Act
        result = self.collection.list()

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], GVC)
        self.assertEqual(result[0].name, "solo-gvc")

    def test_prepare_model_with_dict_creates_gvc_instance(self):
        """Test that prepare_model creates GVC instance from dictionary"""
        # Arrange
        attrs_dict = {
            "name": "prepared-gvc",
            "description": "Prepared GVC",
            "id": "gvc-prep",
        }

        # Act
        result = self.collection.prepare_model(attrs_dict)

        # Assert
        self.assertIsInstance(result, GVC)
        self.assertEqual(result.attrs, attrs_dict)
        self.assertEqual(result.client, self.mock_client)
        self.assertEqual(result.collection, self.collection)

    def test_prepare_model_with_gvc_instance_updates_references(self):
        """Test that prepare_model updates existing GVC instance references"""
        # Arrange
        existing_gvc = GVC(attrs={"name": "existing-gvc"})
        # Verify initial state
        self.assertIsNone(existing_gvc.client)
        self.assertIsNone(existing_gvc.collection)

        # Act
        result = self.collection.prepare_model(existing_gvc)

        # Assert
        self.assertIs(result, existing_gvc)  # Same instance
        self.assertEqual(result.client, self.mock_client)
        self.assertEqual(result.collection, self.collection)

    def test_prepare_model_with_invalid_type_raises_value_error(self):
        """Test that prepare_model raises ValueError for invalid input types"""
        # Arrange
        invalid_inputs = ["string", 123, None, []]

        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                # Act & Assert
                with self.assertRaises(ValueError) as context:
                    self.collection.prepare_model(invalid_input)

                self.assertIn("Can't create GVC from", str(context.exception))


class TestGVCCollectionErrorHandling(unittest.TestCase):
    """Test GVCCollection error handling and edge cases"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_client = MagicMock()
        self.collection = GVCCollection(client=self.mock_client)

    def test_collection_call_raises_type_error_with_helpful_message(self):
        """Test that calling collection as function raises helpful TypeError"""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            self.collection()

        error_message = str(context.exception)
        self.assertIn("'GVCCollection' object is not callable", error_message)
        self.assertIn("pre-2.0", error_message)
        self.assertIn("docker.APIClient", error_message)

    def test_get_operation_propagates_api_errors(self):
        """Test that get() operation propagates API client errors"""
        # Arrange
        api_error = Exception("API connection failed")
        self.mock_client.api.get_gvc.side_effect = api_error

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.collection.get("test-gvc")

        self.assertEqual(context.exception, api_error)

    def test_list_operation_propagates_api_errors(self):
        """Test that list() operation propagates API client errors"""
        # Arrange
        api_error = Exception("Network timeout")
        self.mock_client.api.get_gvc.side_effect = api_error

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.collection.list()

        self.assertEqual(context.exception, api_error)

    def test_list_operation_handles_missing_items_key(self):
        """Test that list() handles API response without 'items' key"""
        # Arrange
        api_response = {"data": [], "total": 0}  # No 'items' key
        self.mock_client.api.get_gvc.return_value = api_response

        # Act & Assert
        with self.assertRaises(KeyError):
            self.collection.list()

    def test_prepare_model_with_state_parameter_sets_state(self):
        """Test that prepare_model correctly sets state parameter"""
        # Arrange
        attrs_dict = {"name": "stateful-gvc", "id": "gvc-state"}
        test_state = {"deployment": "active", "version": "1.2.3"}

        # Act
        result = self.collection.prepare_model(attrs_dict, state=test_state)

        # Assert
        self.assertIsInstance(result, GVC)
        self.assertEqual(result.state, test_state)


if __name__ == "__main__":
    unittest.main()  # type: ignore
