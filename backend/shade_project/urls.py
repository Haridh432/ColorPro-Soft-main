from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

from django.views.static import serve
from django.urls import re_path
from django.http import JsonResponse
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/token/', obtain_auth_token, name='api-token'),
]

# Always serve media files (reports PDFs, etc.)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Static Next.js Frontend Serve (only if frontend_build exists)
_frontend_dir = os.path.join(settings.BASE_DIR, 'frontend_build')


def nextjs_serve(request, path):
    # If frontend_build doesn't exist, show a helpful response
    if not os.path.isdir(_frontend_dir):
        if request.path.startswith('/api/') or request.path.startswith('/admin/'):
            pass  # Should not reach here, but just in case
        return JsonResponse({
            'message': 'ColorPro API is running.',
            'api': '/api/',
            'admin': '/admin/',
            'note': 'Frontend runs on http://localhost:3000 in dev mode. '
                    'Run "npm run build" in the frontend/ folder to serve it from here.',
        })

    if path == "":
        path = "index.html"
    elif not hasattr(path, "split") or "." not in path.split("/")[-1]:
        if os.path.exists(os.path.join(_frontend_dir, path + ".html")):
            path = path + ".html"
        elif os.path.exists(os.path.join(_frontend_dir, path, "index.html")):
            path = os.path.join(path, "index.html")
    return serve(request, path, document_root=_frontend_dir)


urlpatterns += [
    re_path(r'^(?P<path>.*)$', nextjs_serve),
]
