import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasPerm

from salute.api.extensions import HasPermOrScope
from salute.api.scopes import ApiScope
from salute.hierarchy import models as hierarchy_models
from salute.hierarchy.constants import SECTION_TYPE_INFO

from .graph_types import (
    District,
    DistrictOrGroupSection,
    Group,
    SectionTypeInfo,
)


@sb.type
class HierarchyQuery:
    @sd.field(
        description="Get the district",
        extensions=[
            HasPermOrScope(
                "district.view",
                ApiScope.HIERARCHY_READ,
                message="You don't have permission to view the district.",
            ),
        ],
    )
    def district(self, info: sb.Info) -> District:
        return hierarchy_models.District.objects.filter()  # type: ignore[return-value]

    @sd.field(
        description="Get a group by ID",
        extensions=[HasPerm("group.view", message="You don't have permission to view that group.")],
        deprecation_reason="Use the `groups` field instead.",
    )
    def group(self, group_id: sb.relay.GlobalID, info: sb.Info) -> Group:
        return hierarchy_models.Group.objects.filter(id=group_id.node_id)  # type: ignore[return-value]

    groups: sd.relay.DjangoListConnection[Group] = sd.connection(
        description="List groups",
        extensions=[
            HasPermOrScope(
                "group.list",
                ApiScope.HIERARCHY_READ,
                message="You don't have permission to list groups.",
                fail_silently=False,
            )
        ],
    )

    @sd.field(
        description="Get a section by ID",
        extensions=[HasPerm("section.view", message="You don't have permission to view that section.")],
        deprecation_reason="Use the `sections` field instead.",
    )
    def section(self, section_id: sb.relay.GlobalID, info: sb.Info) -> DistrictOrGroupSection:
        return hierarchy_models.Section.objects.filter(id=section_id.node_id)  # type: ignore[return-value]

    sections: sd.relay.DjangoListConnection[DistrictOrGroupSection] = sd.connection(
        description="List sections",
        extensions=[
            HasPermOrScope(
                "section.list",
                ApiScope.HIERARCHY_READ,
                message="You don't have permission to list sections.",
                fail_silently=False,
            )
        ],
    )

    @sb.field(
        description="Get all possible section types",
        extensions=[
            HasPermOrScope(
                "section_type.list",
                ApiScope.HIERARCHY_READ,
                message="You don't have permission to list section types.",
                fail_silently=False,
            )
        ],
    )
    def section_types(self, info: sb.Info) -> list[SectionTypeInfo]:
        return [
            SectionTypeInfo(
                value=section_type,
                display_name=info["display_name"],
                operating_category=info["operating_category"],
                min_age=info["min_age"],
                max_age=info["max_age"],
            )
            for section_type, info in SECTION_TYPE_INFO.items()
        ]
