from django.conf import settings
from django.contrib import admin
from django.urls import path
from strawberry.django.views import AsyncGraphQLView
from salute.hierarchy.graphql.schema import schema

admin.site.site_title = "Salute"
admin.site.site_header = "Salute Backend"
admin.site.index_title = "System administration"

urlpatterns = [
    path("salute-backend/", admin.site.urls),
    path("graphql/", AsyncGraphQLView.as_view(schema=schema)),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
