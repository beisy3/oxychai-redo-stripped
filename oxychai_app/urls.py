from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static
#from .views import hotel_image_view, success

urlpatterns = [
    path("", views.newCalendar, name="index"),
    path("logout/", views.log_out),
    path("findScheduled/", views.findScheduled),
    path('signIn/', views.login_page),
    path('findPersonalInfo/', views.findPersonalInfo),
    path('allExtras/', views.allExtras),
    path('updateExtraDetails/', views.updateExtraDetails),
    path('resetPassword/', views.resetPassword),
    path('monthGenerator/', views.monthGenerator),
    path('newCalendar/', views.newCalendar),
    path('appointmentsPatientInfo/', views.appointmentsPatientInfo),
    path('allPatientsSearch/', views.allPatientsSearch),
    path('layoutFind/', views.layoutFind),
    path('bookAppointmentInd/', views.bookAppointmentInd),
    path('changeLayout/', views.changeLayout),
    path('addPayment/', views.addPayment),
    path('getBalance/', views.getBalance),
    path('cancelAppointment/', views.cancelAppointment),
    path('changeAppStatus/', views.changeAppStatus),
    path('registerNew/', views.RegisterNew),
    path('changePanelPosition/', views.changePanelPosition),
    path('searchPatients/', views.searchPatients),
    path('editDetails/', views.editDetails),
    path('saveLayout/', views.saveLayout, name='saveLayout'),
    path('layoutDelete/', views.layoutDelete, name='layoutDelete'),
    path('patientProfile/', views.patientProfile, name='patientProfile'),
    path('todayLayout/', views.todayLayout, name='todayLayout'),
    path('deleteLayout/', views.deleteLayout, name='deleteLayout'),
    path('allPatients/', views.allPatients, name='allPatients'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)