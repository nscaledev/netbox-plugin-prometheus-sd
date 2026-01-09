from django.test import TestCase

from dcim.models import Device
from ipam.models import Service
from tenancy.models import Tenant
from utilities.testing import ChangeLoggedFilterSetTests

from . import utils
from ..filtersets import ServiceFilterSet, DeviceFilterSet


class ServiceTestCase(TestCase, ChangeLoggedFilterSetTests):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
        """Netbox requires us to define test data in this method, otherwise the ORM won't pick them."""
        for i in range(1, 4):
            utils.build_device_full(f"firewall-full-0{i}", i)
            utils.build_vm_full(f"vm-full-0{i}.example.com", i)

    def test_device_tenant(self):
        tenant = Tenant.objects.all()[0]

        params = {"tenant_id": [tenant.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 6)
        params = {"tenant": [tenant.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 6)

    def test_vm_tenant(self):
        tenant = Tenant.objects.all()[0]

        params = {"tenant_id": [tenant.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 6)
        params = {"tenant": [tenant.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 6)


class DeviceFilterSetTestCase(TestCase):
    """Test cases for DeviceFilterSet cluster name filter.

    Note: We don't inherit ChangeLoggedFilterSetTests because NetBox's own
    DeviceFilterSet is missing some filters (vc_master_for_id) which would
    cause that test to fail.
    """
    queryset = Device.objects.all()
    filterset = DeviceFilterSet

    @classmethod
    def setUpTestData(cls):
        """Create test devices with and without clusters."""
        # Devices with clusters
        utils.build_device_with_cluster("device-cluster-01", cluster_name="SYS2-STA1")
        utils.build_device_with_cluster("device-cluster-02", cluster_name="SYS2-STA1")
        utils.build_device_with_cluster("device-cluster-03", cluster_name="SYS3-STA2")
        # Device without cluster
        utils.build_minimal_device("device-no-cluster-01")

    def test_filter_by_cluster_name_exact(self):
        """Test filtering devices by exact cluster name."""
        params = {'cluster': ['SYS2-STA1']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_filter_by_cluster_name_case_insensitive(self):
        """Test filtering devices by cluster name is case-insensitive."""
        params = {'cluster': ['sys2-sta1']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {'cluster': ['Sys2-Sta1']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_filter_by_cluster_name_multiple(self):
        """Test filtering devices by multiple cluster names."""
        params = {'cluster': ['SYS2-STA1', 'SYS3-STA2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_filter_by_cluster_name_no_match(self):
        """Test filtering devices by non-existent cluster name returns empty."""
        params = {'cluster': ['NONEXISTENT']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
