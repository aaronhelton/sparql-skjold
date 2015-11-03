from django.conf.urls import url

from thesaurus import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^term/$', views.term, name='term'),
]
