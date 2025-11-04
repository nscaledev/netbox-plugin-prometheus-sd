from ipam.models import IPAddress, Service
from virtualization.models import VirtualMachine
from dcim.models.devices import Device


try:  # Netbox >= 3.5
    from netbox.api.viewsets import BaseViewSet
    from netbox.api.viewsets.mixins import CustomFieldsMixin
    from rest_framework.mixins import ListModelMixin

    # Netbox Models ViewSet with list only
    class NetboxPrometheusSDModelViewSet(
        CustomFieldsMixin, ListModelMixin, BaseViewSet
    ):
        pass

except ImportError:
    try:  # 3.2 >= Netbox < 3.5
        from netbox.api.viewsets import (
            NetBoxModelViewSet as NetboxPrometheusSDModelViewSet,
        )
    except ImportError:  # Netbox < 3.2
        from extras.api.views import (
            CustomFieldModelViewSet as NetboxPrometheusSDModelViewSet,
        )

from .utils import NETBOX_RELEASE_CURRENT, NETBOX_RELEASE_41

# Filtersets have been renamed, we support both
# https://github.com/netbox-community/netbox/commit/1024782b9e0abb48f6da65f8248741227d53dbed#diff-d9224204dab475bbe888868c02235b8ef10f07c9201c45c90804d395dc161c40
try:
    from ipam.filtersets import IPAddressFilterSet
    from dcim.filtersets import DeviceFilterSet
    from virtualization.filtersets import VirtualMachineFilterSet
except ImportError:
    from ipam.filters import IPAddressFilterSet
    from dcim.filters import DeviceFilterSet
    from virtualization.filters import VirtualMachineFilterSet


from ..filtersets import ServiceFilterSet
from .serializers import (
    PrometheusIPAddressSerializer,
    PrometheusDeviceSerializer,
    PrometheusVirtualMachineSerializer,
    PrometheusServiceSerializer,
)


class ServiceViewSet(NetboxPrometheusSDModelViewSet):
    queryset = (
        Service.objects.select_related(
            "device",
            "device__tenant",
            "device__tenant__group",
            "device__site",
            "device__location",
            "device__rack",
            "device__platform",
            "virtual_machine",
            "virtual_machine__tenant",
            "virtual_machine__tenant__group",
            "virtual_machine__cluster",
            "virtual_machine__cluster__group",
            "virtual_machine__cluster__type",
        )
        .prefetch_related(
            "ipaddresses",
            "tags",
            "device__primary_ip4__nat_outside",
            "device__primary_ip6__nat_outside",
            "device__contacts__contact",
            "device__contacts__role",
            "virtual_machine__primary_ip4__nat_outside",
            "virtual_machine__primary_ip6__nat_outside",
            "virtual_machine__contacts__contact",
            "virtual_machine__contacts__role",
        )
    )
    filterset_class = ServiceFilterSet
    serializer_class = PrometheusServiceSerializer
    pagination_class = None


class VirtualMachineViewSet(NetboxPrometheusSDModelViewSet):
    virtualmachine_queryset = VirtualMachine.objects.select_related(
        "cluster__group",
        "cluster__type",
        "role",
        "tenant",
        "tenant__group",
        "platform",
    )

    if NETBOX_RELEASE_CURRENT <= NETBOX_RELEASE_41:
        virtualmachine_queryset = virtualmachine_queryset.select_related(
            "cluster__site"
        )

    prefetch_fields = [
        "tags",
        "services",
        "primary_ip4__nat_outside",
        "primary_ip6__nat_outside",
    ]
    if hasattr(VirtualMachine, "contacts"):
        prefetch_fields.extend(["contacts__contact", "contacts__role"])

    queryset = virtualmachine_queryset.prefetch_related(*prefetch_fields)
    filterset_class = VirtualMachineFilterSet
    serializer_class = PrometheusVirtualMachineSerializer
    pagination_class = None


class DeviceViewSet(NetboxPrometheusSDModelViewSet):
    device_queryset = Device.objects.select_related(
        "device_type__manufacturer",
        "tenant",
        "tenant__group",
        "platform",
        "site",
        "location",
        "rack",
        "parent_bay",
        "virtual_chassis__master",
    )

    device_only_fields = [
        "id",
        "name",
        "status",
        "description",
        "position",
        "custom_field_data",
        "site__id",
        "site__name",
        "site__slug",
        "location__id",
        "location__name",
        "location__slug",
        "rack__id",
        "rack__name",
        "platform__id",
        "platform__name",
        "platform__slug",
        "tenant__id",
        "tenant__name",
        "tenant__slug",
        "tenant__group__id",
        "tenant__group__name",
        "tenant__group__slug",
        "device_type__id",
        "device_type__model",
        "device_type__slug",
        "device_type__manufacturer__id",
        "device_type__manufacturer__slug",
        "virtual_chassis__id",
        "virtual_chassis__master__id",
        "virtual_chassis__master__name",
        "primary_ip4__id",
        "primary_ip4__address",
        "primary_ip6__id",
        "primary_ip6__address",
        "oob_ip__id",
        "oob_ip__address",
    ]

    if hasattr(Device, "role"):
        device_queryset = device_queryset.select_related("role")
        device_only_fields.extend(
            ["role__id", "role__name", "role__slug"]
        )
    else:
        device_queryset = device_queryset.select_related("device_role")
        device_only_fields.extend(
            ["device_role__id", "device_role__name", "device_role__slug"]
        )

    prefetch_fields = [
        "tags",
        "services",
        "primary_ip4__nat_outside",
        "primary_ip6__nat_outside",
    ]
    if hasattr(Device, "contacts"):
        prefetch_fields.extend(["contacts__contact", "contacts__role"])

    queryset = (
        device_queryset.only(*device_only_fields).prefetch_related(*prefetch_fields)
    )
    filterset_class = DeviceFilterSet
    serializer_class = PrometheusDeviceSerializer
    pagination_class = None


class IPAddressViewSet(NetboxPrometheusSDModelViewSet):
    queryset = IPAddress.objects.select_related("tenant", "tenant__group").prefetch_related("tags")
    serializer_class = PrometheusIPAddressSerializer
    filterset_class = IPAddressFilterSet
    pagination_class = None
