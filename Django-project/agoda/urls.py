"""
URL configuration for agoda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,re_path, include
from crawler.views import crawl_form, POST_crawl, getCSV, draw_plot, plot, recommendation, AgodaDataList, login_view, register_view, logout_view
from rest_framework.routers import DefaultRouter
from crawler import views

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings  # 加入這行才可以在docker運行時讀取css
from django.conf.urls.static import static  # 加入這行才可以在docker運行時讀取css
from django_prometheus import urls as prometheus_urls

# 設定swagger
schema_view = get_schema_view(
   openapi.Info(
      title="Agoda crawler API",
      default_version='v1',
      description=None,
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="ecco272727@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# 設定api 的路徑
router = DefaultRouter()
router.register(r'Agoda', views.AgodaViewSet)

# api-auth是登入路徑，後面三行是設定swagger
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(prometheus_urls)),
    path("login/", login_view, name='login'),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("crawl_form/", crawl_form, name='crawl_form'),
    path('POST_crawl/',POST_crawl, name='POST_crawl'),
    # path('hotels/',hotels, name='hotels'),
    path('getCSV/', getCSV, name='getCSV'),
    path('draw_plot/', draw_plot, name='draw_plot'),
    path('plot/', plot, name='plot'),
    path('recommendation/', recommendation, name='recommendation'),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-search/', AgodaDataList.as_view(), name='agoda-data-list'),  # API回應
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),  # swagger
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # swagger
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # swagger
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # 加入這行才可以在docker運行時讀取css