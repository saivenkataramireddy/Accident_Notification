from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

@csrf_exempt
def serviceworker(request):
    sw_path = BASE_DIR / "serviceworker.js"
    return HttpResponse(
        sw_path.read_text(),
        content_type="application/javascript"
    )

urlpatterns = [
    path("admin/", admin.site.urls),


    # your app urls
    path("", include("Alert_system.urls")),
]
