from uuid import uuid4

from birdbath.processors import BaseModelAnonymiser

from salute.people.models import Person


class PersonAnonymiser(BaseModelAnonymiser):
    model = Person
    anonymise_fields = [
        "legal_name",
        "preferred_name",
        "last_name",
        "primary_email",
        "tsa_id",
    ]

    clear_fields = ["default_email", "alternate_email", "phone_number", "alternate_phone_number"]

    def generate_legal_name(self, field, obj):
        return self.faker.first_name()

    def generate_preferred_name(self, field, obj):
        return self.faker.first_name()

    def generate_last_name(self, field, obj):
        return self.faker.last_name()

    def generate_primary_email(self, field, obj):
        return self.faker.email()

    def generate_tsa_id(self, field, obj):
        return uuid4()
