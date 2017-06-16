from django.contrib.auth import views as auth_views
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import TemplateView

admin.autodiscover()

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^plan/', include('plans.urls')),
    url(r'^accounts/login/$', auth_views.login, name="login"),
    url(r'^accounts/logout/$', auth_views.logout, {'next_page': '/'},
        name="logout"),
    url(r'^foo/', include('example.foo.urls')),
]
