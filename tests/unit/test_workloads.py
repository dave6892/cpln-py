# import unittest
# from unittest.mock import MagicMock, patch
# from cpln.models.workloads import Workload, WorkloadCollection
# from cpln.config import WorkloadConfig
# from cpln.errors import WebSocketExitCodeError


# class TestWorkload(unittest.TestCase):
#     def setUp(self):
#         self.attrs = {
#             'name': 'test-workload',
#             'spec': {
#                 'defaultOptions': {
#                     'suspend': 'false'
#                 }
#             }
#         }
#         self.client = MagicMock()
#         self.collection = MagicMock()
#         self.state = {'gvc': 'test-gvc'}
#         self.workload = Workload(
#             attrs=self.attrs,
#             client=self.client,
#             collection=self.collection,
#             state=self.state
#         )

#     def test_get(self):
#         """Test get method"""
#         expected_response = {'name': 'test-workload'}
#         self.client.api.get_workload.return_value = expected_response
#         result = self.workload.get()
#         self.assertEqual(result, expected_response)
#         self.client.api.get_workload.assert_called_once_with(
#             self.workload.config()
#         )

#     def test_delete(self):
#         """Test delete method"""
#         self.workload.delete()
#         self.client.api.delete_workload.assert_called_once_with(
#             self.workload.config()
#         )

#     def test_suspend(self):
#         """Test suspend method"""
#         self.workload.suspend()
#         self.client.api.patch_workload.assert_called_once_with(
#             config=self.workload.config(),
#             data={
#                 'spec': {
#                     'defaultOptions': {
#                         'suspend': 'true'
#                     }
#                 }
#             }
#         )

#     def test_unsuspend(self):
#         """Test unsuspend method"""
#         self.workload.unsuspend()
#         self.client.api.patch_workload.assert_called_once_with(
#             config=self.workload.config(),
#             data={
#                 'spec': {
#                     'defaultOptions': {
#                         'suspend': 'false'
#                     }
#                 }
#             }
#         )

#     def test_exec_success(self):
#         """Test exec method with success"""
#         command = "echo test"
#         location = "test-location"
#         expected_response = {'output': 'test'}
#         self.client.api.exec_workload.return_value = expected_response
#         result = self.workload.exec(command, location)
#         self.assertEqual(result, expected_response)
#         self.client.api.exec_workload.assert_called_once_with(
#             config=self.workload.config(location=location),
#             command=command
#         )

#     def test_exec_error(self):
#         """Test exec method with error"""
#         command = "invalid-command"
#         location = "test-location"
#         self.client.api.exec_workload.side_effect = WebSocketExitCodeError("Command failed")
#         with self.assertRaises(WebSocketExitCodeError):
#             self.workload.exec(command, location)

#     def test_ping_success(self):
#         """Test ping method with success"""
#         location = "test-location"
#         expected_response = {'output': 'ping'}
#         self.client.api.exec_workload.return_value = expected_response
#         result = self.workload.ping(location)
#         self.assertEqual(result, expected_response)

#     def test_ping_error(self):
#         """Test ping method with error"""
#         location = "test-location"
#         self.client.api.exec_workload.side_effect = Exception("Connection failed")
#         result = self.workload.ping(location)
#         self.assertIsNone(result)

#     def test_config(self):
#         """Test config method"""
#         location = "test-location"
#         config = self.workload.config(location)
#         self.assertIsInstance(config, WorkloadConfig)
#         self.assertEqual(config.gvc, self.state['gvc'])
#         self.assertEqual(config.workload_id, self.attrs['name'])
#         self.assertEqual(config.location, location)

#     def test_get_remote(self):
#         """Test get_remote method"""
#         location = "test-location"
#         expected_remote = "wss://test-remote"
#         self.client.api.get_remote.return_value = expected_remote
#         result = self.workload.get_remote(location)
#         self.assertEqual(result, expected_remote)
#         self.client.api.get_remote.assert_called_once_with(
#             self.workload.config(location=location)
#         )

#     def test_get_remote_wss(self):
#         """Test get_remote_wss method"""
#         location = "test-location"
#         expected_remote = "wss://test-remote"
#         self.client.api.get_remote_wss.return_value = expected_remote
#         result = self.workload.get_remote_wss(location)
#         self.assertEqual(result, expected_remote)
#         self.client.api.get_remote_wss.assert_called_once_with(
#             self.workload.config(location=location)
#         )

#     def test_get_replicas(self):
#         """Test get_replicas method"""
#         location = "test-location"
#         expected_replicas = ['replica1', 'replica2']
#         self.client.api.get_replicas.return_value = expected_replicas
#         result = self.workload.get_replicas(location)
#         self.assertEqual(result, expected_replicas)
#         self.client.api.get_replicas.assert_called_once_with(
#             self.workload.config(location=location)
#         )

#     def test_get_containers(self):
#         """Test get_containers method"""
#         location = "test-location"
#         expected_containers = ['container1', 'container2']
#         self.client.api.get_containers.return_value = expected_containers
#         result = self.workload.get_containers(location)
#         self.assertEqual(result, expected_containers)
#         self.client.api.get_containers.assert_called_once_with(
#             self.workload.config(location=location)
#         )


# class TestWorkloadCollection(unittest.TestCase):
#     def setUp(self):
#         self.client = MagicMock()
#         self.collection = WorkloadCollection(client=self.client)

#     def test_get(self):
#         """Test get method"""
#         config = WorkloadConfig(gvc='test-gvc', workload_id='test-workload')
#         expected_workload = {'name': 'test-workload'}
#         self.client.api.get_workload.return_value = expected_workload
#         result = self.collection.get(config)
#         self.assertIsInstance(result, Workload)
#         self.assertEqual(result.attrs, expected_workload)
#         self.assertEqual(result.state['gvc'], config.gvc)
#         self.client.api.get_workload.assert_called_once_with(config=config)

#     def test_list_with_gvc(self):
#         """Test list method with GVC"""
#         gvc = 'test-gvc'
#         config = WorkloadConfig(gvc=gvc)
#         response = {
#             'items': [
#                 {'name': 'workload1'},
#                 {'name': 'workload2'}
#             ]
#         }
#         self.client.api.get_workload.return_value = response
#         result = self.collection.list(gvc=gvc)
#         self.assertIsInstance(result, dict)
#         self.assertEqual(len(result), 2)
#         self.assertIn('workload1', result)
#         self.assertIn('workload2', result)
#         self.client.api.get_workload.assert_called_once_with(config=config)

#     def test_list_with_config(self):
#         """Test list method with config"""
#         config = WorkloadConfig(gvc='test-gvc')
#         response = {
#             'items': [
#                 {'name': 'workload1'},
#                 {'name': 'workload2'}
#             ]
#         }
#         self.client.api.get_workload.return_value = response
#         result = self.collection.list(config=config)
#         self.assertIsInstance(result, dict)
#         self.assertEqual(len(result), 2)
#         self.assertIn('workload1', result)
#         self.assertIn('workload2', result)
#         self.client.api.get_workload.assert_called_once_with(config=config)

#     def test_list_no_args(self):
#         """Test list method with no arguments"""
#         with self.assertRaises(ValueError):
#             self.collection.list()


# if __name__ == '__main__':
#     unittest.main()
