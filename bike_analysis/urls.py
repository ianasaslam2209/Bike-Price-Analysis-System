from django.contrib import admin
from django.urls import path
from bikes import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',            views.home,          name='home'),
    path('search/',     views.search,        name='search'),
    path('analytics/',  views.analytics,     name='analytics'),
    path('compare/',    views.compare,       name='compare'),
    path('bike/<int:pk>/', views.bike_detail, name='bike_detail'),
    # Auth
    path('signup/',  views.signup_view,  name='signup'),
    path('login/',   views.login_view,   name='login'),
    path('logout/',  views.logout_view,  name='logout'),
    # Admin-only
    path('import-csv/',         views.import_csv,   name='import_csv'),
    path('admin-records/',      views.admin_records, name='admin_records'),
    path('bike/<int:pk>/edit/', views.bike_edit,    name='bike_edit'),
    path('bike/<int:pk>/delete/', views.bike_delete, name='bike_delete'),
    path('bike/add/',           views.bike_add,     name='bike_add'),
]
