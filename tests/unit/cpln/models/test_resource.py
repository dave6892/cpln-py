import unittest
from unittest.mock import MagicMock

from cpln.models.resource import Collection, Model


class TestModel(unittest.TestCase):
    def setUp(self):
        self.attrs = {"id": "test-id-123456789012", "name": "Test Model"}
        self.client = MagicMock()
        self.collection = MagicMock()
        self.model = Model(
            attrs=self.attrs, client=self.client, collection=self.collection
        )

    def test_init(self):
        """Test model initialization"""
        self.assertEqual(self.model.attrs, self.attrs)
        self.assertEqual(self.model.client, self.client)
        self.assertEqual(self.model.collection, self.collection)
        self.assertEqual(self.model.state, {})

    def test_init_defaults(self):
        """Test model initialization with defaults"""
        model = Model()
        self.assertEqual(model.attrs, {})
        self.assertIsNone(model.client)
        self.assertIsNone(model.collection)
        self.assertEqual(model.state, {})

    def test_id(self):
        """Test id property"""
        self.assertEqual(self.model.id, "test-id-123456789012")

    def test_short_id(self):
        """Test short_id property"""
        self.assertEqual(self.model.short_id, "test-id-1234")

    def test_label(self):
        """Test label property"""
        self.assertEqual(self.model.label, "Test Model")

    def test_repr(self):
        """Test string representation"""
        expected = f"<Model: {self.model.short_id} - {self.model.label}>"
        self.assertEqual(repr(self.model), expected)

    def test_eq(self):
        """Test equality comparison"""
        other = Model(attrs={"id": "test-id-123456789012"})
        self.assertEqual(self.model, other)

    def test_hash(self):
        """Test hashing"""
        expected_hash = hash(f"Model:{self.model.id}")
        self.assertEqual(hash(self.model), expected_hash)

    def test_reload(self):
        """Test reload method"""
        new_attrs = {"id": "test-id-123456789012", "name": "Updated Model"}
        self.collection.get.return_value = Model(attrs=new_attrs)
        self.model.reload()
        self.assertEqual(self.model.attrs, new_attrs)

    def test_attribute_access(self):
        """Test attribute access through __getattr__"""
        # Test accessing existing attribute
        self.assertEqual(self.model.name, "Test Model")

        # Test accessing non-existent attribute
        with self.assertRaises(AttributeError) as context:
            _ = self.model.non_existent
        self.assertEqual(
            str(context.exception), "'Model' has no attribute 'non_existent'"
        )

    def test_attribute_setting(self):
        """Test attribute setting through __setattr__"""
        # Test setting new attribute
        self.model.new_attr = "new value"
        self.assertEqual(self.model.attrs["new_attr"], "new value")

        # Test updating existing attribute
        self.model.name = "Updated Name"
        self.assertEqual(self.model.attrs["name"], "Updated Name")

        # Test setting protected attribute (should still work as it's not in protected_attrs)
        self.model.id = "new-id"
        self.assertEqual(self.model.attrs["id"], "new-id")

    def test_attribute_deletion(self):
        """Test attribute deletion through __delattr__"""
        # Test deleting existing attribute
        del self.model.name
        self.assertNotIn("name", self.model.attrs)

        # Test deleting non-existent attribute
        with self.assertRaises(AttributeError) as context:
            del self.model.non_existent
        self.assertEqual(
            str(context.exception), "'Model' has no attribute 'non_existent'"
        )

    def test_protected_attributes(self):
        """Test protected attributes behavior"""
        # Test that protected attributes can be set
        self.model.attrs = {"new": "value"}
        self.assertEqual(self.model.attrs, {"new": "value"})

        # Test that protected attributes can be accessed
        self.assertEqual(self.model.attrs, {"new": "value"})

        # Test that protected attributes cannot be deleted
        with self.assertRaises(AttributeError) as context:
            del self.model.attrs
        self.assertEqual(
            str(context.exception), "Cannot delete protected attribute 'attrs'"
        )


class TestCollection(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.collection = Collection(client=self.client)

    def test_init(self):
        """Test collection initialization"""
        self.assertEqual(self.collection.client, self.client)

    def test_call(self):
        """Test __call__ method raises TypeError"""
        with self.assertRaises(TypeError):
            self.collection()

    def test_list_not_implemented(self):
        """Test list method raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.collection.list()

    def test_get_not_implemented(self):
        """Test get method raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.collection.get("key")

    def test_create_not_implemented(self):
        """Test create method raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.collection.create()

    def test_prepare_model_with_model(self):
        """Test prepare_model with Model instance"""
        model = Model()
        prepared = self.collection.prepare_model(model)
        self.assertEqual(prepared, model)
        self.assertEqual(prepared.client, self.client)
        self.assertEqual(prepared.collection, self.collection)

    def test_prepare_model_with_dict(self):
        """Test prepare_model with dictionary"""

        class TestModel(Model):
            pass

        class TestCollection(Collection):
            model = TestModel

        collection = TestCollection(client=self.client)
        attrs = {"id": "test-id", "name": "Test Model"}
        prepared = collection.prepare_model(attrs)
        self.assertIsInstance(prepared, TestModel)
        self.assertEqual(prepared.attrs, attrs)
        self.assertEqual(prepared.client, self.client)
        self.assertEqual(prepared.collection, collection)

    def test_prepare_model_invalid_type(self):
        """Test prepare_model with invalid type"""
        with self.assertRaises(ValueError):
            self.collection.prepare_model("invalid")


if __name__ == "__main__":
    unittest.main()
