import unittest
from unittest.mock import MagicMock

from cpln.models.gvcs import GVC, GVCCollection


class TestGVC(unittest.TestCase):
    def setUp(self):
        self.attrs = {"name": "test-gvc", "description": "Test GVC Description"}
        self.client = MagicMock()
        self.collection = MagicMock()
        self.gvc = GVC(attrs=self.attrs, client=self.client, collection=self.collection)

    def test_get(self):
        """Test get method"""
        expected_response = {"name": "test-gvc"}
        self.client.api.get_gvc.return_value = expected_response
        result = self.gvc.get()
        self.assertEqual(result, expected_response)
        self.client.api.get_gvc.assert_called_once_with(self.attrs["name"])

    def test_create(self):
        """Test create method"""
        self.gvc.create()
        self.client.api.create_gvc.assert_called_once_with(
            self.attrs["name"], self.attrs["description"]
        )

    def test_delete(self):
        """Test delete method"""
        self.gvc.delete()
        self.client.api.delete_gvc.assert_called_once_with(self.attrs["name"])


class TestGVCCollection(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.collection = GVCCollection(client=self.client)

    def test_get(self):
        """Test get method"""
        name = "test-gvc"
        expected_gvc = {"name": name}
        self.client.api.get_gvc.return_value = expected_gvc
        result = self.collection.get(name)
        self.assertIsInstance(result, GVC)
        self.assertEqual(result.attrs, expected_gvc)
        self.client.api.get_gvc.assert_called_once_with(name)

    def test_list(self):
        """Test list method"""
        response = {"items": [{"name": "gvc1"}, {"name": "gvc2"}]}
        self.client.api.get_gvc.return_value = response
        result = self.collection.list()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], GVC)
        self.assertIsInstance(result[1], GVC)
        self.assertEqual(result[0].attrs["name"], "gvc1")
        self.assertEqual(result[1].attrs["name"], "gvc2")
        self.client.api.get_gvc.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
