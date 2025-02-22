from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from salute.api.schema import schema
from salute.api.views import SaluteAsyncGraphQLView

admin.site.site_title = "Salute"
admin.site.site_header = "Salute Backend"
admin.site.index_title = "System administration"

urlpatterns = [
    path("salute-backend/", admin.site.urls),
    path("graphql/", csrf_exempt(SaluteAsyncGraphQLView.as_view(schema=schema)), name="graphql"),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
