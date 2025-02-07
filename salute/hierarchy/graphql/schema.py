import strawberry as sb
from strawberry_django.permissions import IsAuthenticated

from salute.hierarchy.constants import SECTION_TYPE_INFO

from .graph_types import SectionTypeInfo


@sb.type
class HierarchyQuery:
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
