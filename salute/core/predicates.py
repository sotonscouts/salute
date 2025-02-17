from __future__ import annotations

from typing import TYPE_CHECKING

import rules

if TYPE_CHECKING:
    from salute.accounts.models import User


@rules.predicate
def user_has_related_person(user: User) -> bool:
    return user.person is not None
