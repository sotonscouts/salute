from birdbath.processors import BaseModelAnonymiser

from salute.hierarchy.models import District, Group, Locality, Section


class DistrictAnonymiser(BaseModelAnonymiser):
    model = District
    anonymise_fields = ["unit_name", "shortcode"]

    def generate_unit_name(self, field, obj):
        return self.faker.city()

    def generate_shortcode(self, field, obj):
        return f"S{self.faker.random_int(1, 999999)}"


class LocalityAnonymiser(BaseModelAnonymiser):
    model = Locality
    anonymise_fields = ["name"]

    def generate_name(self, field, obj):
        return self.faker.city()


class GroupAnonymiser(BaseModelAnonymiser):
    model = Group
    anonymise_fields = ["unit_name", "shortcode", "location_name"]

    def generate_location_name(self, field, obj):
        return self.faker.city()

    def generate_shortcode(self, field, obj):
        return f"S{self.faker.random_int(1, 999999)}"


class GroupSectionAnonymiser(BaseModelAnonymiser):
    model = Section
    anonymise_fields = ["unit_name", "shortcode"]
    clear_fields = ["nickname", "site"]

    def generate_shortcode(self, field, obj):
        return f"S{self.faker.random_int(1, 999999)}"

    def get_queryset(self):
        return super().get_queryset().filter(group__isnull=False)


class DistrictSectionAnonymiser(BaseModelAnonymiser):
    model = Section
    anonymise_fields = ["unit_name", "shortcode", "nickname"]

    def generate_shortcode(self, field, obj):
        return f"S{self.faker.random_int(1, 999999)}"

    def generate_nickname(self, field, obj):
        return self.faker.word()

    def get_queryset(self):
        return super().get_queryset().filter(district__isnull=False)
