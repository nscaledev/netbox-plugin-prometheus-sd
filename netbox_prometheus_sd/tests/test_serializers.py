from django.test import TestCase
from unittest.mock import MagicMock

from ..api.serializers import (
    PrometheusDeviceSerializer,
    PrometheusIPAddressSerializer,
    PrometheusServiceSerializer,
    PrometheusVirtualMachineSerializer,
)
from ..api.utils import LabelDict, extract_cluster
from . import utils

from ..api.utils import NETBOX_RELEASE_CURRENT, NETBOX_RELEASE_41

class DictSubsetMixin:
    """Mixin to provide assertDictContainsSubset which was removed in Python 3.12."""

    def assertDictContainsSubset(self, subset, dictionary, msg=None):
        """Check that all key/value pairs in subset are in dictionary."""
        for key, value in subset.items():
            self.assertIn(key, dictionary, msg=msg)
            self.assertEqual(dictionary[key], value, msg=msg)


class PrometheusVirtualMachineSerializerTests(DictSubsetMixin, TestCase):
    def test_vm_minimal_to_target(self):

        instance = utils.build_minimal_vm("vm-01.example.com")
        data = PrometheusVirtualMachineSerializer(many=True, instance=[instance]).data[
            0
        ]

        self.assertEqual(data["targets"], ["vm-01.example.com"])
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_id": str(instance.id)}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_model": "VirtualMachine"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_status": "active"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_cluster": "DC1"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_cluster_group": "VMware"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_cluster_type": "On Prem"}, data["labels"]
            )
        )

    def test_vm_full_to_target(self):
        instance = utils.build_vm_full("vm-full-01.example.com")
        data_list = PrometheusVirtualMachineSerializer(
            many=True, instance=[instance]
        ).data

        self.assertEqual(data_list[0]["targets"], ["vm-full-01.example.com:4242"])
        self.assertTrue(
            utils.dictContainsSubset(
                {"__metrics_path__": "/not/metrics"}, data_list[0]["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset({"__scheme__": "https"}, data_list[0]["labels"])
        )
        self.assertEqual(data_list[0]["targets"], ["vm-full-01.example.com:4242"])

        self.assertEqual(data_list[1]["targets"], ["vm-full-01.example.com:4243"])
        for data in data_list:
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_id": str(instance.id)}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_model": "VirtualMachine"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_status": "active"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_tenant": "Acme Corp."}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_tenant_slug": "acme"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_site": "Campus A"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_site_slug": "campus-a"}, data["labels"]
                )
            )
            if NETBOX_RELEASE_CURRENT > NETBOX_RELEASE_41:
                self.assertTrue(
                    utils.dictContainsSubset(
                        {"__meta_netbox_cluster_scope": "Campus A"}, data["labels"]
                    )
                )
                self.assertTrue(
                    utils.dictContainsSubset(
                        {"__meta_netbox_cluster_scope_slug": "campus-a"}, data["labels"]
                    )
                )
            self.assertTrue(
                utils.dictContainsSubset({"__meta_netbox_role": "VM"}, data["labels"])
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_role_slug": "vm"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_platform": "Ubuntu 20.04"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_platform_slug": "ubuntu-20.04"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_primary_ip": "2001:db8:1701::2"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_primary_ip4": "192.168.0.1"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_primary_ip6": "2001:db8:1701::2"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_custom_field_simple": "Foobar 123"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_custom_field_int": "42"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_custom_field_bool": "True"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_custom_field_json": "{'foo': ['bar', 'baz']}"},
                    data["labels"],
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_custom_field_multi_selection": "['foo', 'baz']"},
                    data["labels"],
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {
                        "__meta_netbox_custom_field_contact": "[{'id': 1, 'url': 'http://localhost:8000/api/tenancy/contacts/1/',"
                        + " 'display': 'Foo', 'name': 'Foo'}]"
                    },
                    data["labels"],
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {
                        "__meta_netbox_custom_field_text_long": "This is\r\na  pretty\r\nlog\r\nText"
                    },
                    data["labels"],
                )
            )


class PrometheusDeviceSerializerTests(DictSubsetMixin, TestCase):
    def test_device_minimal_to_target(self):
        instance = utils.build_minimal_device("firewall-01")
        data = PrometheusDeviceSerializer(many=True, instance=[instance]).data[0]

        self.assertEqual(data["targets"], ["firewall-01"])
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_id": str(instance.id)}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_model": "Device"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_role": "Firewall"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_role_slug": "firewall"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_device_type": "SRX"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_device_type_slug": "srx"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_site": "Site"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_site_slug": "site"}, data["labels"]
            )
        )

        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_device_manufacturer": "juniper"}, data["labels"]
            )
        )

    def test_device_config_context_no_array(self):
        instance = utils.build_device_config_context_no_array("firewall-no-array-01")
        data = PrometheusDeviceSerializer(many=True, instance=[instance]).data[0]

        self.assertEqual(data["targets"], ["firewall-no-array-01:4242"])

    def test_device_config_context_invalid_1(self):
        instance = utils.build_device_config_context_invalid_1("firewall-invalid-01")
        data = PrometheusDeviceSerializer(many=True, instance=[instance]).data[0]

        self.assertEqual(data["targets"], ["firewall-invalid-01"])

    def test_device_config_context_invalid_2(self):
        instance = utils.build_device_config_context_invalid_2("firewall-invalid-02")
        data = PrometheusDeviceSerializer(many=True, instance=[instance]).data[0]

        self.assertEqual(data["targets"], ["firewall-invalid-02"])

    def test_device_config_context_mix_valid_invalid(self):
        instance = utils.build_device_config_context_mix_invalid_valid(
            "firewall-valid-invalid-01"
        )
        data = PrometheusDeviceSerializer(many=True, instance=[instance]).data[0]

        self.assertEqual(data["targets"], ["firewall-valid-invalid-01:4242"])

    def test_device_full_to_target(self):
        instance = utils.build_device_full("firewall-full-01")
        data = PrometheusDeviceSerializer(many=True, instance=[instance]).data[0]

        self.assertEqual(data["targets"], ["firewall-full-01"])
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_id": str(instance.id)}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_model": "Device"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_platform": "Junos"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_platform_slug": "junos"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_primary_ip": "2001:db8:1701::2"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_primary_ip4": "192.168.0.1"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_primary_ip6": "2001:db8:1701::2"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_oob_ip": "10.0.0.1"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_rack": "R01B01"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_site": "Site"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_site_slug": "site"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_description": "Device Description"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_location": "First Floor"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_location_slug": "first-floor"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_tenant": "Acme Corp."}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_tenant_slug": "acme"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_custom_field_simple": "Foobar 123"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_rack_u_position": "1.0"}, data["labels"]
            )
        )


class PrometheusIPAddressSerializerTests(DictSubsetMixin, TestCase):
    def test_ip_minimal_to_target(self):
        instance = utils.build_minimal_ip("10.10.10.10/24")
        data = PrometheusIPAddressSerializer(many=True, instance=[instance]).data[0]

        self.assertEqual(data["targets"], ["10.10.10.10"])
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_id": str(instance.id)}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_status": "active"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_model": "IPAddress"}, data["labels"]
            )
        )

    def test_ip_full_to_target(self):
        instance = utils.build_full_ip(
            address="10.10.10.10/24", dns_name="foo.example.com"
        )
        data = PrometheusIPAddressSerializer(many=True, instance=[instance]).data[0]

        self.assertEqual(
            data["targets"],
            ["foo.example.com"],
            "IP with DNS name should use DNS name as target",
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_id": str(instance.id)}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset({"__meta_netbox_status": "active"}, data["labels"])
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_model": "IPAddress"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_ip": "10.10.10.10"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_tenant": "Starfleet"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_tenant_slug": "starfleet"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_tenant_group": "Federation"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_tenant_group_slug": "federation"}, data["labels"]
            )
        )
        self.assertTrue(
            utils.dictContainsSubset(
                {"__meta_netbox_custom_field_simple": "Foobar 123"}, data["labels"]
            )
        )


class PrometheusServiceSerializerTests(DictSubsetMixin, TestCase):
    def test_device_service_full_to_target(self):
        device = utils.build_device_full("firewall-full-01")
        instance = device.services.first()
        data_list = PrometheusServiceSerializer(many=True, instance=[instance]).data

        self.assertEqual(data_list[0]["targets"], ["ssh"])
        for data in data_list:
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_id": str(instance.id)}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_display": "ssh (TCP/22)"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset({"__meta_netbox_ports": "22"}, data["labels"])
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_parent": "firewall-full-01"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_tenant": "Acme Corp."}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_tenant_slug": "acme"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset({"__meta_netbox_site": "Site"}, data["labels"])
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_site_slug": "site"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_primary_ip": "2001:db8:1701::2"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_primary_ip4": "192.168.0.1"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_primary_ip6": "2001:db8:1701::2"}, data["labels"]
                )
            )

    def test_vm_service_full_to_target(self):
        vm = utils.build_vm_full("vm-full-01.example.com")
        instance = vm.services.first()
        data_list = PrometheusServiceSerializer(many=True, instance=[instance]).data

        self.assertEqual(data_list[0]["targets"], ["ssh"])
        for data in data_list:
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_id": str(instance.id)}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_display": "ssh (TCP/22)"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset({"__meta_netbox_ports": "22"}, data["labels"])
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_parent": "vm-full-01.example.com"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_tenant": "Acme Corp."}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_tenant_slug": "acme"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_site": "Campus A"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_site_slug": "campus-a"}, data["labels"]
                )
            )
            if NETBOX_RELEASE_CURRENT > NETBOX_RELEASE_41:
                self.assertTrue(
                    utils.dictContainsSubset(
                        {"__meta_netbox_cluster_scope": "Campus A"}, data["labels"]
                    )
                )
                self.assertTrue(
                    utils.dictContainsSubset(
                        {"__meta_netbox_cluster_scope_slug": "campus-a"}, data["labels"]
                    )
                )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_primary_ip": "2001:db8:1701::2"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_primary_ip4": "192.168.0.1"}, data["labels"]
                )
            )
            self.assertTrue(
                utils.dictContainsSubset(
                    {"__meta_netbox_primary_ip6": "2001:db8:1701::2"}, data["labels"]
                )
            )


class ExtractClusterTests(TestCase):
    """Tests for extract_cluster function handling both NetBox 4.2+ scope and older site."""

    def test_extract_cluster_basic_info(self):
        """Test that basic cluster info (name, group, type) is extracted."""
        device = utils.build_device_with_cluster("device-cluster-test", cluster_name="TestCluster")
        labels = LabelDict()
        extract_cluster(device, labels)

        self.assertEqual(labels.get("cluster"), "TestCluster")
        self.assertEqual(labels.get("cluster_group"), "VMware")
        self.assertEqual(labels.get("cluster_type"), "On Prem")

    def test_extract_cluster_scope_from_scope(self):
        """Test that scope labels are extracted from cluster scope (NetBox 4.2+)."""
        device = utils.build_device_with_cluster("device-scope-test", cluster_name="ScopeCluster")
        labels = LabelDict()
        extract_cluster(device, labels)

        # In NetBox 4.2+, cluster scope is labeled as 'cluster_scope'
        self.assertEqual(labels.get("cluster_scope"), "Cluster Site")
        self.assertEqual(labels.get("cluster_scope_slug"), "cluster-site")
        # Device's own site takes precedence for 'site' label
        self.assertEqual(labels.get("site"), "Site")
        self.assertEqual(labels.get("site_slug"), "site")

    def test_extract_cluster_no_cluster(self):
        """Test that no cluster labels are added when device has no cluster."""
        device = utils.build_minimal_device("device-no-cluster-test")
        labels = LabelDict()
        extract_cluster(device, labels)

        self.assertIsNone(labels.get("cluster"))
        self.assertIsNone(labels.get("cluster_group"))
        self.assertIsNone(labels.get("cluster_type"))

    def test_extract_cluster_device_site_overrides_cluster_site(self):
        """Test that device's own site takes precedence over cluster site."""
        device = utils.build_device_with_cluster("device-site-override", cluster_name="OverrideCluster")
        # Device's own site should override cluster site
        labels = LabelDict()
        extract_cluster(device, labels)

        # Device has its own site set in build_minimal_device ("Site", "site")
        # which should take precedence over the cluster's site
        self.assertEqual(labels.get("site"), "Site")
        self.assertEqual(labels.get("site_slug"), "site")

    def test_extract_cluster_with_scope_mock(self):
        """Test extract_cluster with mocked scope object (NetBox 4.2+ style)."""
        # Create a mock object to simulate NetBox 4.2+ cluster with scope
        mock_site = MagicMock()
        mock_site.name = "Scoped Site"
        mock_site.slug = "scoped-site"
        mock_site.__class__.__name__ = "Site"

        mock_cluster = MagicMock()
        mock_cluster.name = "MockCluster"
        mock_cluster.group = MagicMock(name="MockGroup")
        mock_cluster.group.name = "Mock Group"
        mock_cluster.type = MagicMock(name="MockType")
        mock_cluster.type.name = "Mock Type"
        mock_cluster.scope = mock_site
        # Ensure hasattr returns True for scope
        del mock_cluster.site

        mock_obj = MagicMock()
        mock_obj.cluster = mock_cluster
        # Remove site attribute from obj
        del mock_obj.site

        labels = LabelDict()
        extract_cluster(mock_obj, labels)

        self.assertEqual(labels.get("cluster"), "MockCluster")
        self.assertEqual(labels.get("cluster_group"), "Mock Group")
        self.assertEqual(labels.get("cluster_type"), "Mock Type")
        # In NetBox 4.2+, cluster scope is labeled as 'cluster_scope'
        self.assertEqual(labels.get("cluster_scope"), "Scoped Site")
        self.assertEqual(labels.get("cluster_scope_slug"), "scoped-site")
        # Since scope is a Site, site labels should also be set
        self.assertEqual(labels.get("site"), "Scoped Site")
        self.assertEqual(labels.get("site_slug"), "scoped-site")
