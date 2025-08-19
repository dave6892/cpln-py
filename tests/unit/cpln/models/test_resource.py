from unittest import TestCase, main
from unittest.mock import MagicMock

from cpln.client import CPLNClient
from cpln.models.resource import Collection, Model


class TestModel(TestCase):
    def setUp(self) -> None:
        self.attrs = {
            "id": "test-id-123456789012",
            "name": "Test Model",
            "new_attr": "initial value",
        }
        self.client = MagicMock()
        self.collection = MagicMock()
        self.model = Model(
            client=self.client, attrs=self.attrs, collection=self.collection
        )

    def test_init(self) -> None:
        """Test model initialization"""
        self.assertEqual(self.model.attrs, self.attrs)
        self.assertEqual(self.model.client, self.client)
        self.assertEqual(self.model.collection, self.collection)
        self.assertEqual(self.model.state, {})

    def test_init_defaults(self) -> None:
        """Test model initialization with defaults"""
        client: CPLNClient = MagicMock()
        model: Model = Model(client=client)
        self.assertEqual(model.attrs, {})
        self.assertEqual(model.client, client)
        self.assertIsNone(model.collection)
        self.assertEqual(model.state, {})

    def test_id(self) -> None:
        """Test id property"""
        self.assertEqual(self.model.id, "test-id-123456789012")

    def test_short_id(self) -> None:
        """Test short_id property"""
        self.assertEqual(self.model.short_id, "test-id-1234")

    def test_label(self) -> None:
        """Test label property"""
        self.assertEqual(self.model.label, "Test Model")

    def test_repr(self) -> None:
        """Test string representation"""
        expected: str = f"<Model: {self.model.short_id} - {self.model.label}>"
        self.assertEqual(repr(self.model), expected)

    def test_eq(self) -> None:
        """Test equality comparison"""
        other: Model = Model(client=self.client, attrs={"id": "test-id-123456789012"})
        self.assertEqual(self.model, other)

    def test_hash(self) -> None:
        """Test hashing"""
        expected_hash: int = hash(f"Model:{self.model.id}")
        self.assertEqual(hash(self.model), expected_hash)

    def test_reload(self) -> None:
        """Test reload method"""
        new_attrs: dict[str, str] = {
            "id": "test-id-123456789012",
            "name": "Updated Model",
        }
        self.collection.get.return_value = Model(client=self.client, attrs=new_attrs)
        self.model.reload()
        self.assertEqual(self.model.attrs, new_attrs)

    def test_attribute_access(self) -> None:
        """Test attribute access through __getattr__"""
        # Test accessing existing attribute
        self.assertEqual(self.model.name, "Test Model")
        self.assertEqual(self.model.new_attr, "initial value")

        # Test accessing non-existent attribute
        with self.assertRaises(AttributeError) as context:
            _ = self.model.non_existent
        self.assertEqual(
            str(context.exception), "'Model' has no attribute 'non_existent'"
        )

    def test_attribute_setting(self) -> None:
        """Test attribute setting through __setattr__"""
        # Test setting new attribute
        self.model.attrs["another_attr"] = "new value"
        self.assertEqual(self.model.attrs["another_attr"], "new value")

        # Test updating existing attribute
        self.model.attrs["name"] = "Updated Name"
        self.assertEqual(self.model.attrs["name"], "Updated Name")

        # Test setting id attribute (should work as it's stored in attrs)
        self.model.attrs["id"] = "new-id"
        self.assertEqual(self.model.attrs["id"], "new-id")

    def test_attribute_deletion(self) -> None:
        """Test attribute deletion through __delattr__"""
        # Test deleting existing attribute
        del self.model.attrs["name"]
        self.assertNotIn("name", self.model.attrs)

        # Test deleting non-existent attribute
        with self.assertRaises(AttributeError) as context:
            del self.model.attrs["non_existent"]
        self.assertEqual(
            str(context.exception), "'Model' has no attribute 'non_existent'"
        )

    def test_protected_attributes(self) -> None:
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


class TestCollection(TestCase):
    def setUp(self) -> None:
        self.client = MagicMock()
        self.collection = Collection(client=self.client)

    def test_init(self) -> None:
        """Test collection initialization"""
        self.assertEqual(self.collection.client, self.client)

    def test_call(self) -> None:
        """Test __call__ method raises TypeError"""
        with self.assertRaises(TypeError):
            self.collection()

    def test_list_not_implemented(self) -> None:
        """Test list method raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.collection.list()

    def test_get_not_implemented(self) -> None:
        """Test get method raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.collection.get("key")

    def test_create_not_implemented(self) -> None:
        """Test create method raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.collection.create()

    def test_prepare_model_with_model(self) -> None:
        """Test prepare_model with Model instance"""
        model: Model = Model(client=self.client)
        prepared: Model = self.collection.prepare_model(model)
        self.assertEqual(prepared, model)
        self.assertEqual(prepared.client, self.client)
        self.assertEqual(prepared.collection, self.collection)

    def test_prepare_model_with_dict(self) -> None:
        """Test prepare_model with dictionary"""

        class TestModel(Model):
            pass

        class TestCollection(Collection):
            model = TestModel

        collection: TestCollection = TestCollection(client=self.client)
        attrs: dict[str, str] = {"id": "test-id", "name": "Test Model"}
        prepared: Model = collection.prepare_model(attrs)
        self.assertIsInstance(prepared, TestModel)
        self.assertEqual(prepared.attrs, attrs)
        self.assertEqual(prepared.client, self.client)
        self.assertEqual(prepared.collection, collection)

    def test_prepare_model_invalid_type(self) -> None:
        """Test prepare_model with invalid type"""
        with self.assertRaises(ValueError):
            self.collection.prepare_model("invalid")


if __name__ == "__main__":
    main()
