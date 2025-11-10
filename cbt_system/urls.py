from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from exam.admin import admin_site
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- ADMIN CUSTOM SITE ---
    path('panel/', admin_site.urls),

    # --- MAIN APP ROUTES (EXAM SYSTEM) ---
    path('', include(('exam.urls', 'exam'), namespace='exam')),

    # --- AUTHENTICATION (fallback jika dibutuhkan global login/logout) ---
    path('login/', auth_views.LoginView.as_view(template_name='exam/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

# --- STATIC & MEDIA FILES (untuk development mode) ---
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
