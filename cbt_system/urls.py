from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from exam.admin import admin_site
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', include('exam.urls')), 
    # Admin harus selalu paling atas
    path('admin/', admin_site.urls),

    # # Versi TANPA namespace (ini yang menyelamatkan admin)
    # path('', include('exam.urls')),

    # Versi DENGAN namespace (untuk {% url 'exam:xxx' %})
    path('', include(('exam.urls', 'exam'), namespace='exam')),

    # Auth (pastikan login/logout tidak duplikat di exam.urls)
    path('login/', auth_views.LoginView.as_view(template_name='exam/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
