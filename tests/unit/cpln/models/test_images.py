import unittest
from unittest.mock import MagicMock

from cpln.models.images import Image, ImageCollection


class TestImage(unittest.TestCase):
    def setUp(self):
        self.attrs = {"name": "test-image", "id": "test-image-id"}
        self.client = MagicMock()
        self.collection = MagicMock()
        self.image = Image(
            attrs=self.attrs, client=self.client, collection=self.collection
        )

    def test_get(self):
        """Test get method"""
        expected_response = {"name": "test-image"}
        self.client.api.get_image.return_value = expected_response
        result = self.image.get()
        self.assertEqual(result, expected_response)
        self.client.api.get_image.assert_called_once_with(self.attrs["name"])

    def test_delete(self):
        """Test delete method"""
        self.image.delete()
        self.client.api.delete_image.assert_called_once_with(self.attrs["name"])


class TestImageCollection(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.collection = ImageCollection(client=self.client)

    def test_get(self):
        """Test get method"""
        image_id = "test-image"
        expected_image = {"name": image_id}
        self.client.api.get_image.return_value = expected_image
        result = self.collection.get(image_id)
        self.assertIsInstance(result, Image)
        self.assertEqual(result.attrs, expected_image)
        self.client.api.get_image.assert_called_once_with(image_id)

    def test_list(self):
        """Test list method"""
        response = {"items": [{"name": "image1"}, {"name": "image2"}]}
        self.client.api.get_image.return_value = response
        result = self.collection.list()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Image)
        self.assertIsInstance(result[1], Image)
        self.assertEqual(result[0].attrs["name"], "image1")
        self.assertEqual(result[1].attrs["name"], "image2")
        self.client.api.get_image.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
