from types import SimpleNamespace

from django.test import TestCase
from netaddr import IPNetwork

from . import utils as test_helpers
from ..api import utils


class DummyManager:
    """Minimal stand-in for queryset manager that returns a list."""

    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return list(self._items)


class DummyLocation:
    def __init__(self, name, ancestors=None):
        self.name = name
        self._ancestors = list(ancestors or [])

    def get_ancestors(self):
        return list(self._ancestors)


def make_ip_stub(address):
    return SimpleNamespace(address=address)


def make_ip_obj(address):
    network = IPNetwork(address)
    return SimpleNamespace(address=SimpleNamespace(ip=network.ip))


class UtilsTests(TestCase):
    def test_dictContainsSubset(self):
        subset = {"name": "Foo", "age": 25}
        fullset = {"name": "Foo", "age": 25, "city": "Bar"}
        self.assertTrue(test_helpers.dictContainsSubset(subset, fullset))

        subset = {"name": "Foo", "age": 25, "city": "Bar"}
        fullset = {"name": "Foo", "age": 25}
        self.assertFalse(test_helpers.dictContainsSubset(subset, fullset))

        subset = {"name": "Foo", "age": 25}
        fullset = {"name": "Foo", "age": 30, "city": "Bar"}
        self.assertFalse(test_helpers.dictContainsSubset(subset, fullset))

    def test_extract_description(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(description="Device description")

        utils.extract_description(obj, labels)

        self.assertEqual(labels["description"], "Device description")

    def test_extract_location(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(
            location=SimpleNamespace(name="Room 101", slug="room-101")
        )

        utils.extract_location(obj, labels)

        self.assertEqual(labels["location"], "Room 101")
        self.assertEqual(labels["location_slug"], "room-101")

    def test_extract_tags(self):
        labels = utils.LabelDict()
        tags = [
            SimpleNamespace(name="Production", slug="production"),
            SimpleNamespace(name="Core", slug="core"),
        ]
        obj = SimpleNamespace(tags=DummyManager(tags))

        utils.extract_tags(obj, labels)

        self.assertEqual(labels["tags"], "Production,Core")
        self.assertEqual(labels["tag_slugs"], "production,core")

    def test_extract_tenant_with_group(self):
        labels = utils.LabelDict()
        group = SimpleNamespace(name="Tenant Group", slug="tenant-group")
        tenant = SimpleNamespace(name="Tenant A", slug="tenant-a", group=group)
        obj = SimpleNamespace(tenant=tenant)

        utils.extract_tenant(obj, labels)

        self.assertEqual(labels["tenant"], "Tenant A")
        self.assertEqual(labels["tenant_slug"], "tenant-a")
        self.assertEqual(labels["tenant_group"], "Tenant Group")
        self.assertEqual(labels["tenant_group_slug"], "tenant-group")

    def test_extract_tenant_without_group(self):
        labels = utils.LabelDict()
        tenant = SimpleNamespace(name="Tenant B", slug="tenant-b", group=None)
        obj = SimpleNamespace(tenant=tenant)

        utils.extract_tenant(obj, labels)

        self.assertIn("tenant", labels)
        self.assertNotIn("tenant_group", labels)

    def test_extract_cluster_with_scope(self):
        labels = utils.LabelDict()
        scope = SimpleNamespace(name="Campus", slug="campus")
        cluster = SimpleNamespace(
            name="ClusterA",
            group=SimpleNamespace(name="GroupA"),
            type=SimpleNamespace(name="TypeA"),
            scope=scope,
            site=None,
        )
        obj = SimpleNamespace(cluster=cluster)

        utils.extract_cluster(obj, labels)

        self.assertEqual(labels["cluster"], "ClusterA")
        self.assertEqual(labels["cluster_group"], "GroupA")
        self.assertEqual(labels["cluster_type"], "TypeA")
        self.assertEqual(labels["scope"], "Campus")
        self.assertEqual(labels["scope_slug"], "campus")

    def test_extract_cluster_with_site_fallback(self):
        labels = utils.LabelDict()
        cluster = SimpleNamespace(
            name="ClusterB",
            group=None,
            type=None,
            site=SimpleNamespace(name="Legacy Site", slug="legacy-site"),
        )
        obj = SimpleNamespace(cluster=cluster, site=SimpleNamespace(name="Device Site", slug="device-site"))

        utils.extract_cluster(obj, labels)

        self.assertEqual(labels["cluster"], "ClusterB")
        self.assertEqual(labels["site"], "Device Site")
        self.assertEqual(labels["site_slug"], "device-site")

    def test_extract_cluster_with_scope_attribute_on_object(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(
            cluster=None,
            scope=SimpleNamespace(name="Object Scope", slug="object-scope"),
        )

        utils.extract_cluster(obj, labels)

        self.assertEqual(labels["scope"], "Object Scope")
        self.assertEqual(labels["scope_slug"], "object-scope")

    def test_extract_primary_ip(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(
            primary_ip=make_ip_stub("192.0.2.1/24"),
            primary_ip4=make_ip_stub("10.0.0.1/24"),
            primary_ip6=make_ip_stub("2001:db8::1/64"),
        )

        utils.extract_primary_ip(obj, labels)

        self.assertEqual(labels["primary_ip"], "192.0.2.1")
        self.assertEqual(labels["primary_ip4"], "10.0.0.1")
        self.assertEqual(labels["primary_ip6"], "2001:db8::1")

    def test_extract_oob_ip(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(oob_ip=make_ip_stub("198.51.100.10/24"))

        utils.extract_oob_ip(obj, labels)

        self.assertEqual(labels["oob_ip"], "198.51.100.10")

    def test_extracts_platform(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(platform=SimpleNamespace(name="Junos", slug="junos"))

        utils.extracts_platform(obj, labels)

        self.assertEqual(labels["platform"], "Junos")
        self.assertEqual(labels["platform_slug"], "junos")

    def test_extract_services(self):
        labels = utils.LabelDict()
        services = [
            SimpleNamespace(name="ssh"),
            SimpleNamespace(name="snmp"),
        ]
        obj = SimpleNamespace(services=DummyManager(services))

        utils.extract_services(obj, labels)

        self.assertEqual(labels["services"], "ssh,snmp")

    def test_extract_contacts(self):
        labels = utils.LabelDict()
        contacts = [
            SimpleNamespace(
                priority=1,
                contact=SimpleNamespace(
                    name="Alice", email="alice@example.com", comments="Primary"
                ),
                role=SimpleNamespace(name="Owner"),
            ),
            SimpleNamespace(
                priority=2,
                contact=SimpleNamespace(
                    name="Bob", email="", comments=""
                ),
                role=None,
            ),
        ]
        obj = SimpleNamespace(contacts=DummyManager(contacts))

        utils.extract_contacts(obj, labels)

        self.assertEqual(labels["contact_1_name"], "Alice")
        self.assertEqual(labels["contact_1_email"], "alice@example.com")
        self.assertEqual(labels["contact_1_comments"], "Primary")
        self.assertEqual(labels["contact_1_role"], "Owner")
        self.assertEqual(labels["contact_2_name"], "Bob")
        self.assertNotIn("contact_2_role", labels)

    def test_extract_rack(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(rack=SimpleNamespace(name="Rack-01"))

        utils.extract_rack(obj, labels)

        self.assertEqual(labels["rack"], "Rack-01")

    def test_extract_custom_fields(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(
            custom_field_data={
                "environment": "Prod",
                "simple": "value",
            }
        )

        utils.extract_custom_fields(obj, labels)

        self.assertEqual(labels["custom_field_environment"], "Prod")
        self.assertNotIn("custom_field_simple", labels)

    def test_extract_prometheus_sd_config(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(
            _injected_prometheus_sd_config={
                "metrics_path": "/metrics",
                "scheme": "https",
            }
        )

        utils.extract_prometheus_sd_config(obj, labels)

        self.assertEqual(labels["__metrics_path__"], "/metrics")
        self.assertEqual(labels["__scheme__"], "https")

    def test_extract_parent(self):
        labels = utils.LabelDict()
        parent = SimpleNamespace(
            name="device-parent",
            primary_ip=make_ip_stub("192.0.2.10/24"),
            primary_ip4=make_ip_stub("10.1.0.1/24"),
            primary_ip6=make_ip_stub("2001:db8::10/64"),
            oob_ip=make_ip_stub("198.51.100.20/24"),
            tenant=SimpleNamespace(
                name="Tenant P", slug="tenant-p", group=None
            ),
            cluster=SimpleNamespace(
                name="Parent Cluster",
                group=None,
                type=None,
                site=SimpleNamespace(name="Parent Site", slug="parent-site"),
            ),
            contacts=DummyManager([]),
        )
        obj = SimpleNamespace(parent=parent)

        utils.extract_parent(obj, labels)

        self.assertEqual(labels["parent"], "device-parent")
        self.assertEqual(labels["primary_ip"], "192.0.2.10")
        self.assertEqual(labels["site"], "Parent Site")

    def test_extract_service_ips(self):
        labels = utils.LabelDict()
        ipaddresses = [
            make_ip_obj("203.0.113.1/32"),
            make_ip_obj("203.0.113.2/32"),
        ]
        obj = SimpleNamespace(ipaddresses=DummyManager(ipaddresses))

        utils.extract_service_ips(obj, labels)

        self.assertEqual(labels["ipaddresses"], "203.0.113.1,203.0.113.2")

    def test_extract_service_ports(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(ports=[22, 443])

        utils.extract_service_ports(obj, labels)

        self.assertEqual(labels["ports"], "22,443")

    def test_extract_rack_u_position_with_value(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(position=7.0)

        utils.extract_rack_u_poistion(obj, labels)

        self.assertEqual(labels["rack_u_position"], "7.0")

    def test_extract_rack_u_position_without_value(self):
        labels = utils.LabelDict()
        obj = SimpleNamespace(position=None)

        utils.extract_rack_u_poistion(obj, labels)

        self.assertNotIn("rack_u_position", labels)

    def test_extract_full_location(self):
        labels = utils.LabelDict()
        location = DummyLocation("Room", ancestors=["Building", "Floor"])
        obj = SimpleNamespace(
            site=SimpleNamespace(name="Main"),
            location=location,
            rack=SimpleNamespace(name="Rack9"),
        )

        utils.extract_full_location(obj, labels)

        self.assertEqual(labels["full_location"], "Main/Building/Floor/Room/Rack9")
