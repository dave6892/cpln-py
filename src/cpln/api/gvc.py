class GVCApiMixin:
    def get_gvc(self,
        name: str = None
    ):
        endpoint = 'gvc'
        if name:
            endpoint += f'/{name}'
        return self._get(endpoint)

    def create_gvc(self,
        name: str,
        description: str = None
    ):
        raise ValueError('Not implemented! The payload to do this is annoyingly long, so somebody else do it.')

    def delete_gvc(self,
        name: str
    ):
        return self._delete(f'gvc/{name}')
