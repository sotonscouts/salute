from django.contrib import admin
from django.urls import path

admin.site.site_title = "Salute"
admin.site.site_header = "Salute Backend"
admin.site.index_title = "System administration"

urlpatterns = [
    path("salute-backend/", admin.site.urls),
]
