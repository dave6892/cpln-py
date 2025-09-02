"""Tests for Image models following unit testing best practices."""

import unittest
from unittest.mock import MagicMock, call, patch

from cpln.models.images import Image, ImageCollection


class TestImageInitialization(unittest.TestCase):
    """Test Image model initialization and basic properties"""

    def test_image_initialization_with_all_parameters_sets_attributes_correctly(self):
        """Test that Image initializes correctly with all parameters"""
        # Arrange
        test_attrs = {
            "name": "test-image",
            "id": "img-123",
            "repository": "nginx",
            "tag": "latest",
        }
        test_client = MagicMock()
        test_collection = MagicMock()
        test_state = {"active": True}

        # Act
        image = Image(
            attrs=test_attrs,
            client=test_client,
            collection=test_collection,
            state=test_state,
        )

        # Assert
        self.assertEqual(image.attrs, test_attrs)
        self.assertEqual(image.client, test_client)
        self.assertEqual(image.collection, test_collection)
        self.assertEqual(image.state, test_state)

    def test_image_initialization_with_minimal_parameters_uses_defaults(self):
        """Test that Image initializes correctly with minimal parameters"""
        # Act
        image = Image()

        # Assert
        self.assertEqual(image.attrs, {})
        self.assertIsNone(image.client)
        self.assertIsNone(image.collection)
        self.assertEqual(image.state, {})

    def test_image_initialization_with_none_attrs_creates_empty_dict(self):
        """Test that Image handles None attrs parameter correctly"""
        # Act
        image = Image(attrs=None)

        # Assert
        self.assertEqual(image.attrs, {})
        self.assertIsInstance(image.attrs, dict)


class TestImagePropertiesAndBehavior(unittest.TestCase):
    """Test Image model properties and inherited behavior from Model base class"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "name": "production-nginx",
            "id": "img-prod-123456",
            "repository": "nginx",
            "tag": "1.21.6",
            "digest": "sha256:abc123def456",
            "size": 145000000,
        }
        self.test_client = MagicMock()
        self.test_collection = MagicMock()
        self.image = Image(
            attrs=self.test_attrs,
            client=self.test_client,
            collection=self.test_collection,
        )

    def test_image_id_property_returns_id_from_attrs(self):
        """Test that id property returns the ID from attrs"""
        # Act
        result = self.image.id

        # Assert
        self.assertEqual(result, "img-prod-123456")

    def test_image_short_id_property_returns_truncated_id(self):
        """Test that short_id property returns first 12 characters of ID"""
        # Act
        result = self.image.short_id

        # Assert
        self.assertEqual(result, "img-prod-123")  # First 12 characters

    def test_image_short_id_with_none_id_returns_none(self):
        """Test that short_id returns None when ID is None"""
        # Arrange
        self.image.attrs.pop("id")  # type: ignore  # Remove id from attrs

        # Act
        result = self.image.short_id

        # Assert
        self.assertIsNone(result)

    def test_image_label_property_returns_name_from_attrs(self):
        """Test that label property returns the name from attrs"""
        # Act
        result = self.image.label

        # Assert
        self.assertEqual(result, "production-nginx")

    def test_image_attribute_access_returns_attrs_values(self):
        """Test that dynamic attribute access returns values from attrs"""
        # Act & Assert
        self.assertEqual(self.image.name, "production-nginx")
        self.assertEqual(self.image.repository, "nginx")
        self.assertEqual(self.image.tag, "1.21.6")
        self.assertEqual(self.image.digest, "sha256:abc123def456")
        self.assertEqual(self.image.size, 145000000)

    def test_image_attribute_access_with_missing_key_raises_attribute_error(self):
        """Test that accessing missing attributes raises AttributeError"""
        # Act & Assert
        with self.assertRaises(AttributeError) as context:
            _ = self.image.nonexistent_attribute

        self.assertIn(
            "'Image' has no attribute 'nonexistent_attribute'", str(context.exception)
        )

    def test_image_repr_includes_short_id_and_label(self):
        """Test that string representation includes short_id and label"""
        # Act
        result = repr(self.image)

        # Assert
        self.assertIn("Image", result)
        self.assertIn("img-prod-123", result)
        self.assertIn("production-nginx", result)

    def test_image_equality_comparison_with_same_id_returns_true(self):
        """Test that Images with same ID are considered equal"""
        # Arrange
        other_image = Image(attrs={"id": "img-prod-123456", "name": "other-nginx"})

        # Act & Assert
        self.assertEqual(self.image, other_image)

    def test_image_equality_comparison_with_different_id_returns_false(self):
        """Test that Images with different IDs are not considered equal"""
        # Arrange
        other_image = Image(attrs={"id": "different-id", "name": "production-nginx"})

        # Act & Assert
        self.assertNotEqual(self.image, other_image)

    def test_image_hash_is_consistent_with_equality(self):
        """Test that hash is consistent with equality comparison"""
        # Arrange
        other_image = Image(attrs={"id": "img-prod-123456", "name": "other-nginx"})

        # Act & Assert
        self.assertEqual(hash(self.image), hash(other_image))


class TestImageOperations(unittest.TestCase):
    """Test Image CRUD operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "name": "api-nginx",
            "id": "img-api-789",
            "repository": "nginx",
            "tag": "alpine",
        }
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.image = Image(
            attrs=self.test_attrs,
            client=self.mock_client,
            collection=self.mock_collection,
        )

    def test_get_operation_calls_client_api_with_image_name(self):
        """Test that get() calls the client API with correct image name"""
        # Arrange
        expected_response = {
            "name": "api-nginx",
            "repository": "nginx",
            "tag": "alpine",
            "metadata": {"createdAt": "2024-01-01T00:00:00Z"},
        }
        self.mock_client.api.get_image.return_value = expected_response

        # Act
        result = self.image.get()

        # Assert
        self.assertEqual(result, expected_response)
        self.mock_client.api.get_image.assert_called_once_with("api-nginx")

    def test_get_operation_with_missing_name_handles_key_error_gracefully(self):
        """Test that get() handles missing name attribute gracefully"""
        # Arrange
        image_without_name = Image(
            attrs={"repository": "nginx", "tag": "latest"}, client=self.mock_client
        )

        # Act & Assert
        with self.assertRaises(KeyError):
            image_without_name.get()

    @patch("builtins.print")
    def test_delete_operation_calls_client_api_and_prints_messages(self, mock_print):
        """Test that delete() calls client API and prints appropriate messages"""
        # Act
        self.image.delete()

        # Assert
        self.mock_client.api.delete_image.assert_called_once_with("api-nginx")
        # Verify print statements were called
        expected_calls = [call(f"Deleting Image: {self.image}"), call("Deleted!")]
        mock_print.assert_has_calls(expected_calls)

    def test_reload_operation_updates_attrs_from_collection_get(self):
        """Test that reload() fetches fresh data and updates attrs"""
        # Arrange
        updated_attrs = {
            "name": "api-nginx",
            "repository": "nginx",
            "tag": "alpine-updated",
            "status": "active",
        }
        mock_updated_image = MagicMock()
        mock_updated_image.attrs = updated_attrs
        self.mock_collection.get.return_value = mock_updated_image

        # Act
        self.image.reload()

        # Assert
        self.mock_collection.get.assert_called_once_with("img-api-789")
        self.assertEqual(self.image.attrs, updated_attrs)


class TestImageCollectionInitialization(unittest.TestCase):
    """Test ImageCollection initialization and basic properties"""

    def test_image_collection_initialization_with_client_sets_client(self):
        """Test that ImageCollection initializes correctly with client"""
        # Arrange
        test_client = MagicMock()

        # Act
        collection = ImageCollection(client=test_client)

        # Assert
        self.assertEqual(collection.client, test_client)
        self.assertEqual(collection.model, Image)

    def test_image_collection_initialization_without_client_sets_none(self):
        """Test that ImageCollection initializes correctly without client"""
        # Act
        collection = ImageCollection()

        # Assert
        self.assertIsNone(collection.client)
        self.assertEqual(collection.model, Image)

    def test_image_collection_model_attribute_is_image_class(self):
        """Test that collection.model points to Image class"""
        # Act
        collection = ImageCollection()

        # Assert
        self.assertIs(collection.model, Image)


class TestImageCollectionOperations(unittest.TestCase):
    """Test ImageCollection operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_client = MagicMock()
        self.collection = ImageCollection(client=self.mock_client)

    def test_get_operation_returns_image_instance_with_correct_attributes(self):
        """Test that get() returns Image instance with data from API"""
        # Arrange
        image_id = "test-nginx"
        api_response = {
            "name": "test-nginx",
            "repository": "nginx",
            "tag": "latest",
            "id": "img-test-999",
            "status": "active",
        }
        self.mock_client.api.get_image.return_value = api_response

        # Act
        result = self.collection.get(image_id)

        # Assert
        self.assertIsInstance(result, Image)
        self.assertEqual(result.attrs, api_response)
        self.assertEqual(result.client, self.mock_client)
        self.assertEqual(result.collection, self.collection)
        self.mock_client.api.get_image.assert_called_once_with(image_id)

    def test_get_operation_with_empty_name_passes_empty_string(self):
        """Test that get() passes empty string name to API"""
        # Arrange
        self.mock_client.api.get_image.return_value = {
            "name": "",
            "repository": "empty",
        }

        # Act
        result = self.collection.get("")

        # Assert
        self.assertIsInstance(result, Image)
        self.mock_client.api.get_image.assert_called_once_with("")

    def test_list_operation_returns_list_of_image_instances(self):
        """Test that list() returns list of Image instances from API response"""
        # Arrange
        api_response = {
            "items": [
                {
                    "name": "nginx",
                    "repository": "nginx",
                    "tag": "latest",
                    "id": "img-1",
                },
                {"name": "apache", "repository": "httpd", "tag": "2.4", "id": "img-2"},
                {"name": "redis", "repository": "redis", "tag": "7", "id": "img-3"},
            ]
        }
        self.mock_client.api.get_image.return_value = api_response

        # Act
        result = self.collection.list()

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

        # Verify each item is a properly configured Image instance
        for i, image in enumerate(result):
            with self.subTest(image_index=i):
                self.assertIsInstance(image, Image)
                self.assertEqual(image.attrs, api_response["items"][i])
                self.assertEqual(image.client, self.mock_client)
                self.assertEqual(image.collection, self.collection)

        self.mock_client.api.get_image.assert_called_once_with()

    def test_list_operation_with_empty_items_returns_empty_list(self):
        """Test that list() handles empty items array correctly"""
        # Arrange
        api_response = {"items": []}
        self.mock_client.api.get_image.return_value = api_response

        # Act
        result = self.collection.list()

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        self.mock_client.api.get_image.assert_called_once_with()

    def test_list_operation_with_single_item_returns_single_element_list(self):
        """Test that list() handles single item response correctly"""
        # Arrange
        api_response = {
            "items": [
                {
                    "name": "solo-nginx",
                    "repository": "nginx",
                    "tag": "alpine",
                    "id": "img-solo",
                }
            ]
        }
        self.mock_client.api.get_image.return_value = api_response

        # Act
        result = self.collection.list()

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Image)
        self.assertEqual(result[0].name, "solo-nginx")

    def test_prepare_model_with_dict_creates_image_instance(self):
        """Test that prepare_model creates Image instance from dictionary"""
        # Arrange
        attrs_dict = {
            "name": "prepared-nginx",
            "repository": "nginx",
            "tag": "stable",
            "id": "img-prep",
        }

        # Act
        result = self.collection.prepare_model(attrs_dict)

        # Assert
        self.assertIsInstance(result, Image)
        self.assertEqual(result.attrs, attrs_dict)
        self.assertEqual(result.client, self.mock_client)
        self.assertEqual(result.collection, self.collection)

    def test_prepare_model_with_image_instance_updates_references(self):
        """Test that prepare_model updates existing Image instance references"""
        # Arrange
        existing_image = Image(attrs={"name": "existing-nginx"})
        # Verify initial state
        self.assertIsNone(existing_image.client)
        self.assertIsNone(existing_image.collection)

        # Act
        result = self.collection.prepare_model(existing_image)

        # Assert
        self.assertIs(result, existing_image)  # Same instance
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

                self.assertIn("Can't create Image from", str(context.exception))


class TestImageCollectionErrorHandling(unittest.TestCase):
    """Test ImageCollection error handling and edge cases"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_client = MagicMock()
        self.collection = ImageCollection(client=self.mock_client)

    def test_collection_call_raises_type_error_with_helpful_message(self):
        """Test that calling collection as function raises helpful TypeError"""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            self.collection()

        error_message = str(context.exception)
        self.assertIn("'ImageCollection' object is not callable", error_message)
        self.assertIn("pre-2.0", error_message)
        self.assertIn("docker.APIClient", error_message)

    def test_get_operation_propagates_api_errors(self):
        """Test that get() operation propagates API client errors"""
        # Arrange
        api_error = Exception("Image registry connection failed")
        self.mock_client.api.get_image.side_effect = api_error

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.collection.get("test-image")

        self.assertEqual(context.exception, api_error)

    def test_list_operation_propagates_api_errors(self):
        """Test that list() operation propagates API client errors"""
        # Arrange
        api_error = Exception("Registry timeout")
        self.mock_client.api.get_image.side_effect = api_error

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.collection.list()

        self.assertEqual(context.exception, api_error)

    def test_list_operation_handles_missing_items_key(self):
        """Test that list() handles API response without 'items' key"""
        # Arrange
        api_response = {"images": [], "total": 0}  # No 'items' key
        self.mock_client.api.get_image.return_value = api_response

        # Act & Assert
        with self.assertRaises(KeyError):
            self.collection.list()

    def test_prepare_model_with_state_parameter_sets_state(self):
        """Test that prepare_model correctly sets state parameter"""
        # Arrange
        attrs_dict = {"name": "stateful-image", "id": "img-state"}
        test_state = {"deployment": "active", "version": "1.2.3"}

        # Act
        result = self.collection.prepare_model(attrs_dict, state=test_state)

        # Assert
        self.assertIsInstance(result, Image)
        self.assertEqual(result.state, test_state)


if __name__ == "__main__":
    unittest.main()  # type: ignore
