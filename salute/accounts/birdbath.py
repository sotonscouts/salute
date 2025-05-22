from birdbath.processors import BaseModelDeleter

from salute.accounts.models import User


class DeleteAllMyUsersProcessor(BaseModelDeleter):
    model = User

    def get_queryset(self):
        return super().get_queryset().filter(is_superuser=False)
