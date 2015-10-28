from django.conf.urls import url

from v2 import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^select/$', views.select, name='select'),
]
