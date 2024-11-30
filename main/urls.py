from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('yetkili-girisi/', views.yetkili_login, name='yetkili_login'),
    path('yetkili-paneli/', views.yetkili_paneli, name='yetkili_paneli'),
    path('personel-girisi/', views.personel_login, name='personel_login'),
    path('personel-paneli/', views.personel_paneli, name='personel_paneli'),
    path('remove-personnel/<int:pk>/', views.remove_personnel, name='remove_personnel'),
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/', views.check_out, name='check_out'),
    path('home/', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('work-hours/<int:pk>/', views.work_hours_entry, name='work_hours_entry'),
    path('work-hours-summary/<int:user_id>/', views.work_hours_summary, name='work_hours_summary'),
    path('download-report/<int:pk>/', views.download_report, name='download_report'),
    path("leave-request/", views.leave_request, name="leave_request"),
    path('approve-leave-request/<int:request_id>/', views.approve_leave_request, name='approve_leave_request'),
    path('reject-leave-request/<int:request_id>/', views.reject_leave_request, name='reject_leave_request'),
]

