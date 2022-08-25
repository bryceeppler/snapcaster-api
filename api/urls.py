from pydoc import describe
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

# will have to change these to .as_view once I implement class based views
urlpatterns = [
    path('bulk/', views.getBulkPrice.as_view()),
    path('', views.getPrice.as_view(),),
    path('ping/', views.ping.as_view(),),
]

urlpatterns = format_suffix_patterns(urlpatterns)
