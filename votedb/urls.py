from django.conf.urls import url

from votedb import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^turtle/(?P<uri>http\:\/\/.+)$', views.turtle, name='turtle'),
    url(r'^session/(?P<uri>http\:\/\/.+)$', views.session_record, name='sesion_record'),
    url(r'^memberstate/(?P<uri>http\:\/\/.+)$', views.member_state, name='member_state'),
    url(r'^bymember/(?P<uri>http\:\/\/.+)$', views.by_member, name='by_member'),
    url(r'^bysession/(?P<uri>http\:\/\/.+)$', views.by_session, name='by_session'),
    url(r'^voterecord/(?P<uri>http\:\/\/.+)$', views.vote_record, name='vote_record'),
    url(r'^memberstates/$', views.member_states, name='member_states'),
]
