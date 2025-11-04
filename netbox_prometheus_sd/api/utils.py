import json
from netaddr import IPNetwork
from packaging import version
from netbox.settings import VERSION

VERSION = VERSION.split("-")[0]

NETBOX_RELEASE_CURRENT = version.parse(VERSION)
NETBOX_RELEASE_40 = version.parse("4.0.11")
NETBOX_RELEASE_41 = version.parse("4.1.11")


class LabelDict(dict):
    """Wrapper around dict to render labels"""

    _PROM_TRANSLATION = str.maketrans({ord(char): "_" for char in " -/\\!"})
    _PROM_PREFIX = "__meta_netbox_"

    @staticmethod
    def promsafestr(labelval: str):
        return labelval.translate(LabelDict._PROM_TRANSLATION)

    def get_labels(self):
        """Prefix and replace invalid key chars for prometheus labels"""
        return {
            f"{self._PROM_PREFIX}{self.promsafestr(str(key))}": val
            for key, val in self.items()
        }


def extract_description(obj, labels: LabelDict):
    """Extract description"""
    if hasattr(obj, "description") and obj.description:
        labels["description"] = obj.description


def extract_location(obj, labels: LabelDict):
    """Extract location"""
    if hasattr(obj, "location") and obj.location:
        labels["location"] = obj.location.name
        labels["location_slug"] = obj.location.slug


def extract_tags(obj, labels):
    if not hasattr(obj, "tags") or obj.tags is None:
        return

    tags = list(obj.tags.all())
    if not tags:
        return

    labels["tags"] = ",".join(t.name for t in tags)
    labels["tag_slugs"] = ",".join(t.slug for t in tags)


def extract_tenant(obj, labels: LabelDict):
    """Extract tenant and group"""
    if hasattr(obj, "tenant") and obj.tenant:
        labels["tenant"] = obj.tenant.name
        labels["tenant_slug"] = obj.tenant.slug

        if obj.tenant.group:
            labels["tenant_group"] = obj.tenant.group.name
            labels["tenant_group_slug"] = obj.tenant.group.slug


def extract_cluster(obj, labels: LabelDict):
    if hasattr(obj, "cluster") and obj.cluster is not None:
        labels["cluster"] = obj.cluster.name
        if obj.cluster.group:
            labels["cluster_group"] = obj.cluster.group.name
        if obj.cluster.type:
            labels["cluster_type"] = obj.cluster.type.name
        try: # Netbox >4.2
            if obj.cluster.scope:
                labels["scope"] = obj.cluster.scope.name
                labels["scope_slug"] = obj.cluster.scope.slug
        except AttributeError: # Netbox <4.2
            if obj.cluster.site:
                labels["site"] = obj.cluster.site.name
                labels["site_slug"] = obj.cluster.site.slug

    # Has precedence over cluster scope
    if hasattr(obj, "scope") and obj.scope is not None:
        labels["scope"] = obj.scope.name
        labels["scope_slug"] = obj.scope.slug

    # Still Return site labels for Devices
    if hasattr(obj, "site") and obj.site is not None:
        labels["site"] = obj.site.name
        labels["site_slug"] = obj.site.slug


def extract_primary_ip(obj, labels: LabelDict):
    if getattr(obj, "primary_ip", None) is not None:
        labels["primary_ip"] = str(IPNetwork(obj.primary_ip.address).ip)

    if getattr(obj, "primary_ip4", None) is not None:
        labels["primary_ip4"] = str(IPNetwork(obj.primary_ip4.address).ip)

    if getattr(obj, "primary_ip6", None) is not None:
        labels["primary_ip6"] = str(IPNetwork(obj.primary_ip6.address).ip)


def extract_oob_ip(obj, labels: LabelDict):
    if getattr(obj, "oob_ip", None) is not None:
        labels["oob_ip"] = str(IPNetwork(obj.oob_ip.address).ip)


def extracts_platform(obj, label: LabelDict):
    if hasattr(obj, "platform") and obj.platform is not None:
        label["platform"] = obj.platform.name
        label["platform_slug"] = obj.platform.slug


def extract_services(obj, labels: LabelDict):
    if not hasattr(obj, "services") or obj.services is None:
        return

    services = list(obj.services.all())
    if services:
        labels["services"] = ",".join(srv.name for srv in services)


def extract_contacts(obj, labels: LabelDict):
    contacts_rel = getattr(obj, "contacts", None)
    if contacts_rel is None:
        return

    for assignment in contacts_rel.all():
        contact = getattr(assignment, "contact", None)
        if contact is None:
            continue

        priority = assignment.priority
        labels[f"contact_{priority}_name"] = contact.name
        if contact.email:
            labels[f"contact_{priority}_email"] = contact.email
        if contact.comments:
            labels[f"contact_{priority}_comments"] = contact.comments
        role = getattr(assignment, "role", None)
        if role is not None:
            labels[f"contact_{priority}_role"] = role.name


def extract_rack(obj, labels: LabelDict):
    """Extract rack"""
    if hasattr(obj, "rack") and obj.rack:
        labels["rack"] = obj.rack.name


def extract_custom_fields(obj, labels: LabelDict):
    if hasattr(obj, "custom_field_data") and obj.custom_field_data is not None:
        for key, value in obj.custom_field_data.items():
            if key.lower() != "environment":
                continue
            normalized_key = "custom_field_" + key.lower()

            # Primitive values (str, int, bool, etc.) become strings
            if isinstance(value, (str, int, float, bool)) or value is None:
                labels[normalized_key] = "" if value is None else str(value)
                continue

            # Lists, tuples, sets, dicts, and other complex objects are JSON encoded
            labels[normalized_key] = json.dumps(value, separators=(",", ":"))


def extract_prometheus_sd_config(obj, labels):
    prometheus_sd_config = getattr(obj, "_injected_prometheus_sd_config", {})

    metrics_path = prometheus_sd_config.get("metrics_path", None)
    if metrics_path and isinstance(metrics_path, str):
        labels["__metrics_path__"] = metrics_path

    scheme = prometheus_sd_config.get("scheme", None)
    if scheme and isinstance(scheme, str):
        labels["__scheme__"] = scheme


def extract_parent(obj, labels: LabelDict):
    labels["parent"] = obj.parent.name
    extract_primary_ip(obj.parent, labels)
    extract_oob_ip(obj.parent, labels)
    extract_tenant(obj.parent, labels)
    extract_cluster(obj.parent, labels)
    extract_contacts(obj.parent, labels)


def extract_service_ips(obj, labels: LabelDict):
    if not hasattr(obj, "ipaddresses") or obj.ipaddresses is None:
        return

    ipaddresses = list(obj.ipaddresses.all())
    if ipaddresses:
        labels["ipaddresses"] = ",".join(
            str(ipaddr.address.ip) for ipaddr in ipaddresses
        )


def extract_service_ports(obj, labels: LabelDict):
    if hasattr(obj, "ports") and obj.ports is not None and len(obj.ports):
        labels["ports"] = ",".join([str(port) for port in obj.ports])


def extract_rack_u_position(obj, labels: LabelDict):
    """Extract rack U poistion"""
    if hasattr(obj, "position") and obj.position:
        labels["rack_u_position"] = str(obj.position)


# def extract_full_location(obj, labels: LabelDict):
#     """
#     Extracts the full location of a given object, including site, location, ancestors, and rack (if present).
#
#     Args:
#         obj: The object from which to extract the location.
#         labels: A dictionary of labels, into which the full location will be stored.
#
#     Returns:
#         None
#     """
#     parts = [obj.site.name]
#     parts.extend(str(ancestor) for ancestor in obj.location.get_ancestors(include_self=True))
#     parts.append(obj.location.name)
#     location_path = "/".join(parts)
#     if obj.rack is not None:
#         location_path = f"{location_path}/{obj.rack.name}"
#
#     labels["full_location"] = location_path
