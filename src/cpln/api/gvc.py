class GVCApiMixin:
    def get_gvc(self,
        name: str = None
    ):
        endpoint = 'gvc'
        if name:
            endpoint += f'/{name}'
        return self._get(endpoint)
