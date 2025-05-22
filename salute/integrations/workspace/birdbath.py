from birdbath.processors import BaseModelAnonymiser

from salute.integrations.workspace.models import WorkspaceAccount, WorkspaceAccountAlias


class WorkspaceAccountAnonymiser(BaseModelAnonymiser):
    model = WorkspaceAccount
    anonymise_fields = ["google_id", "primary_email", "given_name", "family_name"]
    clear_fields = ["external_ids", "org_unit_path"]

    def generate_primary_email(self, field, obj):
        return self.faker.email(domain="examplescouts.com")

    def generate_given_name(self, field, obj):
        return self.faker.first_name()

    def generate_family_name(self, field, obj):
        return self.faker.last_name()


class WorkspaceAccountAliasAnonymiser(BaseModelAnonymiser):
    model = WorkspaceAccountAlias
    anonymise_fields = ["address"]

    def generate_address(self, field, obj):
        return self.faker.email(domain="examplescouts.com")
