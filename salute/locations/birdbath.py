from birdbath.processors import BaseModelAnonymiser

from salute.locations.models import Site, SiteOperator


class ThirdPartySiteOperatorAnonymiser(BaseModelAnonymiser):
    model = SiteOperator
    anonymise_fields = ["name"]

    def generate_name(self, field, obj):
        return self.faker.company()

    def get_queryset(self):
        return super().get_queryset().exclude(name="")


class SiteAnonymiser(BaseModelAnonymiser):
    model = Site
    anonymise_fields = [
        "name",
        "building_name",
        "street_number",
        "street",
        "town",
        "county",
        "postcode",
        "latitude",
        "longitude",
    ]

    def generate_name(self, field, obj):
        return self.faker.city()

    def generate_latitude(self, field, obj):
        return self.faker.coordinate(center=52, radius=0.05)

    def generate_longitude(self, field, obj):
        return self.faker.coordinate(center=0, radius=0.05)

    def generate_building_name(self, field, obj):
        return self.faker.company()

    def generate_street_number(self, field, obj):
        return self.faker.random_int(1, 9999)

    def generate_street(self, field, obj):
        return self.faker.street_name()

    def generate_town(self, field, obj):
        return self.faker.city()

    def generate_county(self, field, obj):
        return self.faker.state()

    def generate_postcode(self, field, obj):
        return self.faker.postcode()
