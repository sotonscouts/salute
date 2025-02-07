import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import IsAuthenticated

from salute.hierarchy import models as hierarchy_models
from salute.hierarchy.constants import SECTION_TYPE_INFO

from .graph_types import District, Group, SectionTypeInfo


@sb.type
class HierarchyQuery:
    @sd.field(description="Get the district", extensions=[IsAuthenticated()])
    def district(self, info: sb.Info) -> District:
        return hierarchy_models.District.objects.get()  # type: ignore[return-value]

    @sd.field(description="Get a group by ID", extensions=[IsAuthenticated()])
    def group(self, group_id: sb.relay.GlobalID, info: sb.Info) -> Group:
        return hierarchy_models.Group.objects.get(id=group_id.node_id)  # type: ignore[return-value]

    @sb.field(
        description="Get all possible section types",
        # For unknown reasons, this returns an empty list without fail_silently=False
        extensions=[IsAuthenticated(fail_silently=False)],
    )
    def section_types(self, info: sb.Info) -> list[SectionTypeInfo]:
        return [
            SectionTypeInfo(
                value=section_type,
                **info,
            )
            for section_type, info in SECTION_TYPE_INFO.items()
        ]
