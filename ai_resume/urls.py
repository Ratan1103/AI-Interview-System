from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public
    path('',          views.home,          name='home'),
    path('register/', views.register_view, name='register'),
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),

    # Authenticated
    path('dashboard/',         views.dashboard,          name='dashboard'),
    path('upload-resume/',     views.upload_resume,      name='upload_resume'),
    path('configure-interview/', views.configure_interview, name='configure_interview'),
    path('interview/',         views.interview,          name='interview'),
    path('interview/end/',     views.end_interview,      name='end_interview'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
