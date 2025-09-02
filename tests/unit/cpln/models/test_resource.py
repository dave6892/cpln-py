"""Tests for base resource classes following unit testing best practices."""

import unittest
from unittest.mock import MagicMock

from cpln.models.resource import Collection, Model


class TestModelInitialization(unittest.TestCase):
    """Test Model base class initialization and basic properties"""

    def test_model_initialization_with_all_parameters_sets_attributes_correctly(self):
        """Test that Model initializes correctly with all parameters"""
        # Arrange
        test_attrs = {"id": "test-id-123456789012", "name": "Test Model"}
        test_client = MagicMock()
        test_collection = MagicMock()
        test_state = {"active": True, "version": "1.0"}

        # Act
        model = Model(
            attrs=test_attrs,
            client=test_client,
            collection=test_collection,
            state=test_state,
        )

        # Assert
        self.assertEqual(model.attrs, test_attrs)
        self.assertEqual(model.client, test_client)
        self.assertEqual(model.collection, test_collection)
        self.assertEqual(model.state, test_state)

    def test_model_initialization_with_minimal_parameters_uses_defaults(self):
        """Test that Model initializes correctly with minimal parameters (defaults)"""
        # Act
        model = Model()

        # Assert
        self.assertEqual(model.attrs, {})
        self.assertIsNone(model.client)
        self.assertIsNone(model.collection)
        self.assertEqual(model.state, {})

    def test_model_initialization_with_none_attrs_creates_empty_dict(self):
        """Test that Model handles None attrs parameter correctly"""
        # Act
        model = Model(attrs=None)

        # Assert
        self.assertEqual(model.attrs, {})
        self.assertIsInstance(model.attrs, dict)

    def test_model_initialization_with_none_state_creates_empty_dict(self):
        """Test that Model handles None state parameter correctly"""
        # Act
        model = Model(state=None)

        # Assert
        self.assertEqual(model.state, {})
        self.assertIsInstance(model.state, dict)


class TestModelProperties(unittest.TestCase):
    """Test Model properties and computed attributes"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "id": "test-id-123456789012345",
            "name": "Production Resource",
        }
        self.model = Model(attrs=self.test_attrs)

    def test_model_id_property_returns_id_from_attrs(self):
        """Test that id property returns the ID from attrs using id_attribute"""
        # Act
        result = self.model.id

        # Assert
        self.assertEqual(result, "test-id-123456789012345")

    def test_model_id_property_with_missing_id_returns_none(self):
        """Test that id property returns None when ID is missing"""
        # Arrange
        model_without_id = Model(attrs={"name": "No ID Resource"})

        # Act
        result = model_without_id.id

        # Assert
        self.assertIsNone(result)

    def test_model_short_id_property_returns_truncated_id(self):
        """Test that short_id property returns first 12 characters of ID"""
        # Act
        result = self.model.short_id

        # Assert
        self.assertEqual(result, "test-id-1234")  # First 12 characters

    def test_model_short_id_property_with_short_id_returns_full_id(self):
        """Test that short_id returns full ID when ID is 12 characters or less"""
        # Arrange
        short_id_model = Model(attrs={"id": "short123"})

        # Act
        result = short_id_model.short_id

        # Assert
        self.assertEqual(result, "short123")

    def test_model_short_id_property_with_none_id_returns_none(self):
        """Test that short_id returns None when ID is None"""
        # Arrange
        no_id_model = Model(attrs={"name": "No ID"})

        # Act
        result = no_id_model.short_id

        # Assert
        self.assertIsNone(result)

    def test_model_label_property_returns_name_from_attrs(self):
        """Test that label property returns the name from attrs using label_attribute"""
        # Act
        result = self.model.label

        # Assert
        self.assertEqual(result, "Production Resource")

    def test_model_label_property_with_missing_name_returns_none(self):
        """Test that label property returns None when name is missing"""
        # Arrange
        model_without_name = Model(attrs={"id": "test-123"})

        # Act
        result = model_without_name.label

        # Assert
        self.assertIsNone(result)


class TestModelStringRepresentation(unittest.TestCase):
    """Test Model string representation methods"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {"id": "model-id-123456789012", "name": "Test Model"}
        self.model = Model(attrs=self.test_attrs)

    def test_model_repr_includes_class_name_short_id_and_label(self):
        """Test that __repr__ includes class name, short_id, and label"""
        # Act
        result = repr(self.model)

        # Assert
        expected = "<Model: model-id-123 - Test Model>"
        self.assertEqual(result, expected)

    def test_model_repr_with_none_short_id_shows_none(self):
        """Test that __repr__ handles None short_id gracefully"""
        # Arrange
        model_no_id = Model(attrs={"name": "No ID Model"})

        # Act
        result = repr(model_no_id)

        # Assert
        expected = "<Model: None - No ID Model>"
        self.assertEqual(result, expected)

    def test_model_repr_with_none_label_shows_none(self):
        """Test that __repr__ handles None label gracefully"""
        # Arrange
        model_no_name = Model(attrs={"id": "test-123"})

        # Act
        result = repr(model_no_name)

        # Assert
        expected = "<Model: test-123 - None>"
        self.assertEqual(result, expected)


class TestModelEqualityAndHashing(unittest.TestCase):
    """Test Model equality comparison and hashing"""

    def setUp(self):
        """Set up common test fixtures"""
        self.model1 = Model(attrs={"id": "same-id-123", "name": "Model One"})
        self.model2 = Model(attrs={"id": "same-id-123", "name": "Model Two"})
        self.model3 = Model(attrs={"id": "different-id-456", "name": "Model Three"})

    def test_model_equality_with_same_id_returns_true(self):
        """Test that models with same ID are considered equal"""
        # Act & Assert
        self.assertEqual(self.model1, self.model2)

    def test_model_equality_with_different_id_returns_false(self):
        """Test that models with different IDs are not equal"""
        # Act & Assert
        self.assertNotEqual(self.model1, self.model3)

    def test_model_equality_with_none_ids_are_equal(self):
        """Test that models with None IDs are considered equal"""
        # Arrange
        model_no_id1 = Model(attrs={"name": "No ID 1"})
        model_no_id2 = Model(attrs={"name": "No ID 2"})

        # Act & Assert
        self.assertEqual(model_no_id1, model_no_id2)

    def test_model_equality_with_different_types_returns_false(self):
        """Test that model is not equal to objects of different types"""
        # Act & Assert
        self.assertNotEqual(self.model1, "not-a-model")
        self.assertNotEqual(self.model1, {"id": "same-id-123"})
        self.assertNotEqual(self.model1, 123)

    def test_model_hash_consistency_with_equality(self):
        """Test that equal models have equal hashes"""
        # Act & Assert
        self.assertEqual(hash(self.model1), hash(self.model2))

    def test_model_hash_includes_class_name_and_id(self):
        """Test that hash includes class name and ID"""
        # Act
        result = hash(self.model1)
        expected = hash("Model:same-id-123")

        # Assert
        self.assertEqual(result, expected)

    def test_model_hash_with_none_id_handles_gracefully(self):
        """Test that hash handles None ID gracefully"""
        # Arrange
        model_no_id = Model(attrs={"name": "No ID"})

        # Act
        result = hash(model_no_id)
        expected = hash("Model:None")

        # Assert
        self.assertEqual(result, expected)


class TestModelAttributeAccess(unittest.TestCase):
    """Test Model dynamic attribute access methods"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "id": "attr-test-123",
            "name": "Attribute Test",
            "description": "Test description",
            "tags": ["tag1", "tag2"],
        }
        self.model = Model(attrs=self.test_attrs)

    def test_model_getattr_returns_attrs_values(self):
        """Test that __getattr__ returns values from attrs dictionary"""
        # Act & Assert
        self.assertEqual(self.model.name, "Attribute Test")
        self.assertEqual(self.model.description, "Test description")
        self.assertEqual(self.model.tags, ["tag1", "tag2"])

    def test_model_getattr_with_missing_attribute_raises_attribute_error(self):
        """Test that __getattr__ raises AttributeError for missing attributes"""
        # Act & Assert
        with self.assertRaises(AttributeError) as context:
            _ = self.model.nonexistent_attr

        self.assertEqual(
            str(context.exception), "'Model' has no attribute 'nonexistent_attr'"
        )

    def test_model_setattr_stores_in_attrs_dict(self):
        """Test that __setattr__ stores non-protected attributes in attrs"""
        # Act
        self.model.new_attribute = "new value"
        self.model.existing_name = "updated name"

        # Assert
        self.assertEqual(self.model.attrs["new_attribute"], "new value")  # type: ignore
        self.assertEqual(self.model.attrs["existing_name"], "updated name")  # type: ignore
        self.assertEqual(self.model.existing_name, "updated name")

    def test_model_setattr_with_protected_attributes_sets_directly(self):
        """Test that __setattr__ sets protected attributes directly on instance"""
        # Arrange
        new_client = MagicMock()
        new_attrs = {"new": "attrs"}

        # Act
        self.model.client = new_client
        self.model.attrs = new_attrs

        # Assert
        self.assertEqual(self.model.client, new_client)
        self.assertEqual(self.model.attrs, new_attrs)

    def test_model_setattr_initializes_attrs_if_missing(self):
        """Test that __setattr__ initializes attrs dict if it doesn't exist"""
        # Arrange
        model = Model.__new__(Model)  # Create without calling __init__

        # Act
        model.test_attr = "test value"

        # Assert
        self.assertEqual(model.attrs, {"test_attr": "test value"})

    def test_model_delattr_removes_from_attrs_dict(self):
        """Test that __delattr__ removes attributes from attrs dictionary"""
        # Act
        del self.model.description

        # Assert
        self.assertNotIn("description", self.model.attrs)  # type: ignore
        with self.assertRaises(AttributeError):
            _ = self.model.description

    def test_model_delattr_with_missing_attribute_raises_attribute_error(self):
        """Test that __delattr__ raises AttributeError for missing attributes"""
        # Act & Assert
        with self.assertRaises(AttributeError) as context:
            del self.model.nonexistent_attr

        self.assertEqual(
            str(context.exception), "'Model' has no attribute 'nonexistent_attr'"
        )

    def test_model_delattr_with_protected_attributes_raises_attribute_error(self):
        """Test that __delattr__ prevents deletion of protected attributes"""
        # Arrange
        protected_attrs = ["client", "collection", "state", "attrs"]

        for attr in protected_attrs:
            with self.subTest(protected_attr=attr):
                # Act & Assert
                with self.assertRaises(AttributeError) as context:
                    delattr(self.model, attr)

                self.assertEqual(
                    str(context.exception),
                    f"Cannot delete protected attribute '{attr}'",
                )


class TestModelReloadOperation(unittest.TestCase):
    """Test Model reload functionality"""

    def setUp(self):
        """Set up common test fixtures"""
        self.original_attrs = {
            "id": "reload-test-123",
            "name": "Original Name",
            "version": "1.0",
        }
        self.mock_collection = MagicMock()
        self.model = Model(attrs=self.original_attrs, collection=self.mock_collection)

    def test_reload_operation_updates_attrs_from_collection_get(self):
        """Test that reload() fetches fresh data and updates attrs"""
        # Arrange
        updated_attrs = {
            "id": "reload-test-123",
            "name": "Updated Name",
            "version": "2.0",
        }
        mock_updated_model = MagicMock()
        mock_updated_model.attrs = updated_attrs
        self.mock_collection.get.return_value = mock_updated_model

        # Act
        self.model.reload()

        # Assert
        self.mock_collection.get.assert_called_once_with("reload-test-123")
        self.assertEqual(self.model.attrs, updated_attrs)

    def test_reload_operation_with_none_id_calls_collection_get_with_none(self):
        """Test that reload() handles None ID gracefully"""
        # Arrange
        model_no_id = Model(attrs={"name": "No ID"}, collection=self.mock_collection)
        mock_updated_model = MagicMock()
        mock_updated_model.attrs = {"name": "Updated No ID"}
        self.mock_collection.get.return_value = mock_updated_model

        # Act
        model_no_id.reload()

        # Assert
        self.mock_collection.get.assert_called_once_with(None)
        self.assertEqual(model_no_id.attrs, {"name": "Updated No ID"})


class TestCollectionInitialization(unittest.TestCase):
    """Test Collection base class initialization"""

    def test_collection_initialization_with_client_sets_client(self):
        """Test that Collection initializes correctly with client"""
        # Arrange
        test_client = MagicMock()

        # Act
        collection = Collection(client=test_client)

        # Assert
        self.assertEqual(collection.client, test_client)
        self.assertIsNone(collection.model)  # Base class has no model

    def test_collection_initialization_without_client_sets_none(self):
        """Test that Collection initializes correctly without client"""
        # Act
        collection = Collection()

        # Assert
        self.assertIsNone(collection.client)
        self.assertIsNone(collection.model)


class TestCollectionCallProtection(unittest.TestCase):
    """Test Collection call protection mechanism"""

    def setUp(self):
        """Set up common test fixtures"""
        self.collection = Collection()

    def test_collection_call_raises_type_error_with_helpful_message(self):
        """Test that calling collection as function raises helpful TypeError"""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            self.collection()

        error_message = str(context.exception)
        self.assertIn("'Collection' object is not callable", error_message)
        self.assertIn("pre-2.0", error_message)
        self.assertIn("docker.APIClient", error_message)

    def test_collection_call_with_arguments_raises_same_error(self):
        """Test that calling collection with arguments raises same TypeError"""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            self.collection("arg1", kwarg="value")

        error_message = str(context.exception)
        self.assertIn("'Collection' object is not callable", error_message)


class TestCollectionAbstractMethods(unittest.TestCase):
    """Test Collection abstract method implementations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.collection = Collection()

    def test_list_method_raises_not_implemented_error(self):
        """Test that list() method raises NotImplementedError"""
        # Act & Assert
        with self.assertRaises(NotImplementedError):
            self.collection.list()

    def test_get_method_raises_not_implemented_error(self):
        """Test that get() method raises NotImplementedError"""
        # Act & Assert
        with self.assertRaises(NotImplementedError):
            self.collection.get("test-key")

    def test_create_method_raises_not_implemented_error(self):
        """Test that create() method raises NotImplementedError"""
        # Act & Assert
        with self.assertRaises(NotImplementedError):
            self.collection.create()

    def test_create_method_with_attrs_raises_not_implemented_error(self):
        """Test that create() method with attrs raises NotImplementedError"""
        # Act & Assert
        with self.assertRaises(NotImplementedError):
            self.collection.create(attrs={"name": "test"})


class TestCollectionPrepareModel(unittest.TestCase):
    """Test Collection prepare_model functionality"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_client = MagicMock()
        self.collection = Collection(client=self.mock_client)

    def test_prepare_model_with_existing_model_updates_references(self):
        """Test that prepare_model updates existing Model instance references"""
        # Arrange
        existing_model = Model(attrs={"id": "existing-123", "name": "Existing"})
        test_state = {"version": "1.0"}

        # Verify initial state
        self.assertIsNone(existing_model.client)
        self.assertIsNone(existing_model.collection)
        self.assertEqual(existing_model.state, {})

        # Act
        result = self.collection.prepare_model(existing_model, state=test_state)

        # Assert
        self.assertIs(result, existing_model)  # Same instance
        self.assertEqual(result.client, self.mock_client)
        self.assertEqual(result.collection, self.collection)
        self.assertEqual(result.state, test_state)

    def test_prepare_model_with_dict_creates_model_instance(self):
        """Test that prepare_model creates Model instance from dictionary"""

        # Arrange
        class TestModel(Model):
            pass

        class TestCollection(Collection):
            model = TestModel  # type: ignore

        test_collection = TestCollection(client=self.mock_client)
        attrs_dict = {"id": "dict-test-456", "name": "From Dict"}
        test_state = {"active": True}

        # Act
        result = test_collection.prepare_model(attrs_dict, state=test_state)

        # Assert
        self.assertIsInstance(result, TestModel)
        self.assertEqual(result.attrs, attrs_dict)
        self.assertEqual(result.client, self.mock_client)
        self.assertEqual(result.collection, test_collection)
        self.assertEqual(result.state, test_state)

    def test_prepare_model_with_invalid_type_raises_value_error(self):
        """Test that prepare_model raises ValueError for invalid input types"""
        # Arrange
        invalid_inputs = ["string", 123, [], True, None]

        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                # Act & Assert
                with self.assertRaises(ValueError) as context:
                    self.collection.prepare_model(invalid_input)

                self.assertIn("Can't create Model from", str(context.exception))

    def test_prepare_model_with_none_model_class_raises_value_error(self):
        """Test that prepare_model with dict raises ValueError when model class is None"""
        # Arrange
        attrs_dict = {"id": "test-123", "name": "Test"}

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.collection.prepare_model(attrs_dict)

        self.assertIn("Can't create Model from", str(context.exception))

    def test_prepare_model_with_none_state_uses_default_empty_dict(self):
        """Test that prepare_model uses empty dict for state when None provided"""
        # Arrange
        existing_model = Model(attrs={"id": "state-test"})

        # Act
        result = self.collection.prepare_model(existing_model, state=None)

        # Assert
        self.assertEqual(result.state, {})


if __name__ == "__main__":
    unittest.main()  # type: ignore
