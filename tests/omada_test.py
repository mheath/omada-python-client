import pytest
import requests
import unittest
import urllib3

from omada import Omada
from .util import configLogging, loadConfig

class TestOmada(unittest.TestCase):
    def setUp(self):
        configLogging()
        self.config = loadConfig()

        omadaCfg = self.config['omada']
        
        session = requests.Session()
        session.verify = omadaCfg.get("verify", False)
        if not session.verify:
            urllib3.disable_warnings(category = urllib3.exceptions.InsecureRequestWarning)

        self.omada = Omada(omadaCfg.get("host"), omadaCfg.get("site", "Default"), session)
        self.omada.login(omadaCfg.get("username"), omadaCfg.get("password"))

    def test_logout(self):
        self.omada.logout()
        self.assertFalse(self.omada.is_logged_in())

    def test_is_logged_in(self):
        self.assertTrue(self.omada.is_logged_in())

    def test_current_user(self):
        currentUser = self.omada.get_current_user()
        self.assertEqual(self.config['omada'].get("username"), currentUser['name'])

    def test_get_clients(self):
        clients = self.omada.get_clients()
        self.assertTrue(len(clients) > 0)

    def test_get_client(self):
        clients = self.omada.get_clients()
        mac = clients[0]['mac']

        client = self.omada.get_client(mac)
        self.assertEqual(clients[0]['mac'], client['mac'])
        self.assertEqual(clients[0]['name'], client['name'])
        self.assertEqual(clients[0]['ip'], client['ip'])

    def test_page_clients(self):
        self._page_clients(5)

    def test_single_page_clients(self):
        self._page_clients(1)

    def _page_clients(self, page_size):
        paged_clients = self.omada.page_clients(page_size = page_size)

        row_count = 0

        self.assertTrue(paged_clients.has_next)
        while paged_clients.has_next:
            clients = paged_clients.next()
            self.assertTrue(len(clients) <= page_size)
            row_count += len(clients)
            total_rows = paged_clients.total_rows
            print(f"Row count {row_count} total rows {total_rows}")
            self.assertIsNotNone(total_rows)
            self.assertTrue(row_count <= total_rows)
            
        print(f"Final row count {row_count} pager total rows {paged_clients.total_rows}")
        self.assertEqual(row_count, paged_clients.total_rows)

    def test_update_client(self):
        clients = self.omada.get_clients()
        mac = clients[0]['mac']

        originalName = clients[0]['name']
        testName = f"Omada Python Client Test (was: {originalName})"
        self.omada.update_client(mac, {'name': testName})

        updatedClient = self.omada.get_client(mac)
        self.assertEqual(testName, updatedClient['name'])

        self.omada.update_client(mac, {'name': originalName})
        restoredClient = self.omada.get_client(mac)

        self.assertEqual(originalName, restoredClient['name'])

    def test_get_devices(self):
        devices = self.omada.get_devices()
        self.assertTrue(len(devices) > 0)

    def test_get_switch(self):
        device = self._find_first_switch()
        if device is None:
            self.skipTest("No switch present")
        else:
            mac = device['mac']
            switch = self.omada.get_switch(mac)
            self.assertEqual('switch', switch['type'])
            self.assertEqual(mac, switch['mac'])

    def test_get_switch_ports(self):
        device = self._find_first_switch()
        if device is None:
            self.skipTest("No switch present")
        else:
            mac = device['mac']
            switch = self.omada.get_switch(mac)
            ports = self.omada.get_switch_ports(mac)
            self.assertEqual(len(ports), switch['deviceMisc']['portNum'])

    def _find_first_switch(self):
        devices = self.omada.get_devices()
        
        for device in devices:
            if device['type'] == 'switch':
                return device

    def test_get_ap(self):
        device = self._find_first_ap()
        if device is None:
            self.skipTest("No AP present")
        else:
            mac = device['mac']
            ap = self.omada.get_ap(mac)
            self.assertEqual('ap', ap['type'])
            self.assertEqual(mac, ap['mac'])

    def _find_first_ap(self):
        devices = self.omada.get_devices()
        
        for device in devices:
            if device['type'] == 'ap':
                return device

    def test_get_alerts(self):
        alerts = self.omada.get_alerts()
        self.assertIsNotNone(alerts)

        with pytest.raises(ValueError):
            self.omada.get_alerts(level = "Foo")

        with pytest.raises(ValueError):
            self.omada.get_alerts(module = "Bar")

if __name__ == '__main__':
    unittest.main()