from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# Import custom admin site dari exam app
from exam.admin import admin_site

urlpatterns = [
    # Ganti admin.site.urls dengan admin_site.urls

    path('admin/', admin_site.urls),
    path('', include(('exam.urls', 'exam'), namespace='exam')),
    path('teacher/', include('exam.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='exam/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)