class WorkloadApiMixin:

    def get_workload(self,
        gvc: str,
        workload_id: str = None,
    ):
        """Get a workload by its ID."""
        endpoint = f'gvc/{gvc}/workload'
        if workload_id:
            endpoint += f'/{workload_id}'
        return self._get(endpoint)

    def delete_workload(self,
        gvc: str,
        workload_id: str,
    ):
        """Delete a workload by its ID."""
        endpoint = f'gvc/{gvc}/workload/{workload_id}'
        return self._delete(endpoint)
