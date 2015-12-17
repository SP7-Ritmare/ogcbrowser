from django.conf.urls import patterns, include, url
from base.views import HomePageView, get_nodes, get_node, get_wmsurl

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', HomePageView.as_view(), name='home'),

    # RESTFul
    url(r'^api/nodes$', get_nodes, name='get_nodes'),
    url(r'^api/nodes/(?P<id>\d+)$', get_node, name='get_node'),
    url(r'^api/wmsurl$', get_wmsurl, name='get_wmsurl'),

    # url(r'^ogcbrowser/', include('ogcbrowser.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
