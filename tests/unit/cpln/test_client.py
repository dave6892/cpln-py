# import os
# from typing import cast

# from cpln import CPLNClient


# def test_cpln_client_initialization(mock_cpln_client: CPLNClient) -> None:
#     base_url = cast(str, os.getenv("CPLN_BASE_URL", "https://api.cpln.io"))
#     org = cast(str, os.getenv("CPLN_ORG", "test-org"))
#     token = cast(str, os.getenv("CPLN_TOKEN", "mock-token"))

#     assert mock_cpln_client.api.config.base_url == base_url
#     assert mock_cpln_client.api.config.org == org
#     assert mock_cpln_client.api.config.token == token


# def test_cpln_client_from_env() -> None:
#     with patch("cpln.utils.kwargs_from_env") as mock_kwargs:
#         base_url = cast(str, os.getenv("CPLN_BASE_URL", "https://api.cpln.io"))
#         org = cast(str, os.getenv("CPLN_ORG", "test-org"))
#         token = cast(str, os.getenv("CPLN_TOKEN", "mock-token"))

#         mock_kwargs.return_value = {"base_url": base_url, "org": org, "token": token}
#         client = CPLNClient.from_env()
#         assert client.api.config.base_url == base_url
#         assert client.api.config.org == org
#         assert client.api.config.token == token


# def test_cpln_client_gvcs_property(mock_cpln_client: CPLNClient) -> None:
#     gvcs = mock_cpln_client.gvcs
#     assert gvcs.client == mock_cpln_client


# def test_cpln_client_images_property(mock_cpln_client: CPLNClient) -> None:
#     images = mock_cpln_client.images
#     assert images.client == mock_cpln_client


# def test_cpln_client_workloads_property(mock_cpln_client: CPLNClient) -> None:
#     workloads = mock_cpln_client.workloads
#     assert workloads.client == mock_cpln_client
