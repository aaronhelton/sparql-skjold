from django.conf.urls import url

from thesaurus import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^term/$', views.term, name='term'),
    url(r'^search/$', views.search, name='search'),
    url(r'^autocomplete/$', views.autocomplete, name='autocomplete'),
]
