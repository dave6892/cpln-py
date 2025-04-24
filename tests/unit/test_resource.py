# import unittest
# from unittest.mock import MagicMock
# from cpln.models.resource import Model, Collection


# class TestModel(unittest.TestCase):
#     def setUp(self):
#         self.attrs = {
#             'id': 'test-id-123456789012',
#             'name': 'Test Model'
#         }
#         self.client = MagicMock()
#         self.collection = MagicMock()
#         self.model = Model(
#             attrs=self.attrs,
#             client=self.client,
#             collection=self.collection
#         )

#     def test_init(self):
#         """Test model initialization"""
#         self.assertEqual(self.model.attrs, self.attrs)
#         self.assertEqual(self.model.client, self.client)
#         self.assertEqual(self.model.collection, self.collection)
#         self.assertEqual(self.model.state, {})

#     def test_init_defaults(self):
#         """Test model initialization with defaults"""
#         model = Model()
#         self.assertEqual(model.attrs, {})
#         self.assertIsNone(model.client)
#         self.assertIsNone(model.collection)
#         self.assertEqual(model.state, {})

#     def test_id(self):
#         """Test id property"""
#         self.assertEqual(self.model.id, 'test-id-123456789012')

#     def test_short_id(self):
#         """Test short_id property"""
#         self.assertEqual(self.model.short_id, 'test-id-1234')

#     def test_label(self):
#         """Test label property"""
#         self.assertEqual(self.model.label, 'Test Model')

#     def test_repr(self):
#         """Test string representation"""
#         expected = f"<Model: {self.model.short_id} - {self.model.label}>"
#         self.assertEqual(repr(self.model), expected)

#     def test_eq(self):
#         """Test equality comparison"""
#         other = Model(attrs={'id': 'test-id-123456789012'})
#         self.assertEqual(self.model, other)

#     def test_hash(self):
#         """Test hashing"""
#         expected_hash = hash(f"Model:{self.model.id}")
#         self.assertEqual(hash(self.model), expected_hash)

#     def test_reload(self):
#         """Test reload method"""
#         new_attrs = {'id': 'test-id-123456789012', 'name': 'Updated Model'}
#         self.collection.get.return_value = Model(attrs=new_attrs)
#         self.model.reload()
#         self.assertEqual(self.model.attrs, new_attrs)


# class TestCollection(unittest.TestCase):
#     def setUp(self):
#         self.client = MagicMock()
#         self.collection = Collection(client=self.client)

#     def test_init(self):
#         """Test collection initialization"""
#         self.assertEqual(self.collection.client, self.client)

#     def test_call(self):
#         """Test __call__ method raises TypeError"""
#         with self.assertRaises(TypeError):
#             self.collection()

#     def test_list_not_implemented(self):
#         """Test list method raises NotImplementedError"""
#         with self.assertRaises(NotImplementedError):
#             self.collection.list()

#     def test_get_not_implemented(self):
#         """Test get method raises NotImplementedError"""
#         with self.assertRaises(NotImplementedError):
#             self.collection.get('key')

#     def test_create_not_implemented(self):
#         """Test create method raises NotImplementedError"""
#         with self.assertRaises(NotImplementedError):
#             self.collection.create()

#     def test_prepare_model_with_model(self):
#         """Test prepare_model with Model instance"""
#         model = Model()
#         prepared = self.collection.prepare_model(model)
#         self.assertEqual(prepared, model)
#         self.assertEqual(prepared.client, self.client)
#         self.assertEqual(prepared.collection, self.collection)

#     def test_prepare_model_with_dict(self):
#         """Test prepare_model with dictionary"""
#         class TestModel(Model):
#             pass

#         class TestCollection(Collection):
#             model = TestModel

#         collection = TestCollection(client=self.client)
#         attrs = {'id': 'test-id', 'name': 'Test Model'}
#         prepared = collection.prepare_model(attrs)
#         self.assertIsInstance(prepared, TestModel)
#         self.assertEqual(prepared.attrs, attrs)
#         self.assertEqual(prepared.client, self.client)
#         self.assertEqual(prepared.collection, collection)

#     def test_prepare_model_invalid_type(self):
#         """Test prepare_model with invalid type"""
#         with self.assertRaises(Exception):
#             self.collection.prepare_model("invalid")


# if __name__ == '__main__':
#     unittest.main()
