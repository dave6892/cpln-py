from .api import APIClient
from .models import (
    GVCCollection,
    ImageCollection,
    WorkloadCollection
)
from .utils import kwargs_from_env


class CPLNClient:
    """
    A client for communicating with a Control Plane Server.

    Example:
        ```
        >>> import cpln
        >>> client = cpln.CPLNClient(base_url='https://api.cpln.io')
        ```

    Args:
        base_url (str): URL to the Control Plane server.
    """

    def __init__(self, *args, **kwargs):
        self.api = APIClient(*args, **kwargs)

    @classmethod
    def from_env(cls, **kwargs):
        """
        Return a client configured from environment variables.

        The environment variables used are the same as those used by the
        cpln command-line client. They are:

        .. envvar:: `CPLN_TOKEN`
        Authorization token for accessing the use of the API.

        .. envvar:: `CPLN_ORG`
        The orgnanization namespace of your control plane service.

        Args:
            version (str): The version of the API to use. Set to ``auto`` to
                automatically detect the server's version. Default: ``auto``
            timeout (int): Default timeout for API calls, in seconds.
            max_pool_size (int): The maximum number of connections
                to save in the pool.
            environment (dict): The environment to read environment variables
                from. Default: the value of ``os.environ``

        Example:

            >>> import cpln
            >>> client = cpln.from_env()
        """
        return cls(**kwargs_from_env(**kwargs))

    @property
    def gvcs(self):
        """
        A collection of GVCs in the Control Plane.
        """
        return GVCCollection(client=self)

    @property
    def images(self):
        """
        A collection of images in the Control Plane.
        """
        return ImageCollection(client=self)

    @property
    def workloads(self):
        """
        A collection of workloads in the Control Plane.
        """
        return WorkloadCollection(client=self)


from_env = CPLNClient.from_env
