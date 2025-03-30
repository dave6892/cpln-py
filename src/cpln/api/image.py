class ImageApiMixin:

    def get_image(self,
        image_id: str = None
    ):
        endpoint = 'image'
        if image_id:
            endpoint += f'/{image_id}'
        return self._get(endpoint)

    def delete_image(self, image_id):
        return self._delete(f'image/{image_id}')
