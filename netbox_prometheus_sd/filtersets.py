# Filtersets have been renamed, we support both
# https://github.com/netbox-community/netbox/commit/1024782b9e0abb48f6da65f8248741227d53dbed#diff-d9224204dab475bbe888868c02235b8ef10f07c9201c45c90804d395dc161c40
from django.db.models import Q
from django.utils.translation import gettext as _

from utilities.filters import (
    MultiValueCharFilter,
    MultiValueNumberFilter,
    NumericArrayFilter,
)

try:
    from ipam.filtersets import ServiceFilterSet as NetboxServiceFilterSet
except ImportError:
    from ipam.filters import ServiceFilterSet as NetboxServiceFilterSet

try:
    from dcim.filtersets import DeviceFilterSet as NetboxDeviceFilterSet
except ImportError:
    from dcim.filters import DeviceFilterSet as NetboxDeviceFilterSet


class ServiceFilterSet(NetboxServiceFilterSet):
    """Filter set to support tenancy over the device/VM foreign key.

    Tenancy in Netbox is very incosistent and the relationship on its own is defined across many different models. This
    means that supporting all layers is nearly impossible without a stronger upstream support. For this reason only the
    "first level" tenancy is supported by this filter set.
    """

    tenant_id = MultiValueNumberFilter(
        method="filter_by_tenant_id",
        label=_("Tenant (ID)"),
    )

    tenant = MultiValueCharFilter(
        method="filter_by_tenant_slug",
        label=_("Tenant (slug)"),
    )

    # fix to make the test_missing_filters pass
    # see: https://github.com/netbox-community/netbox/blob/master/netbox/utilities/testing/filtersets.py#L98
    ports = NumericArrayFilter(field_name="ports", lookup_expr="contains")

    def filter_by_cluster_tenant_id(self, queryset, name, value):
        return queryset.filter(
            Q(device__cluster__tenant_id__in=value)
            | Q(virtual_machine__cluster__tenant_id__in=value)
        )

    def filter_by_cluster_tenant_slug(self, queryset, name, value):
        return queryset.filter(
            Q(device__cluster__tenant__slug__in=value)
            | Q(virtual_machine__cluster__tenant__slug__in=value)
        )

    def filter_by_tenant_id(self, queryset, name, value):
        return queryset.filter(
            Q(device__tenant_id__in=value) | Q(virtual_machine__tenant_id__in=value)
        )

    def filter_by_tenant_slug(self, queryset, name, value):
        return queryset.filter(
            Q(device__tenant__slug__in=value)
            | Q(virtual_machine__tenant__slug__in=value)
        )


class DeviceFilterSet(NetboxDeviceFilterSet):
    """Extends NetBox's DeviceFilterSet to add cluster name filter.

    NetBox's DeviceFilterSet only has cluster_id, not cluster (name).
    This adds the missing cluster name filter for consistency with other filters.
    Cluster model doesn't have a slug field, so we filter by name (case-insensitive).
    """

    cluster = MultiValueCharFilter(
        method='filter_by_cluster_name',
        label=_('Cluster (name)'),
    )

    def filter_by_cluster_name(self, queryset, name, value):
        q = Q()
        for v in value:
            q |= Q(cluster__name__iexact=v)
        return queryset.filter(q)
