from django.urls import path
from . import views

urlpatterns = [

    # 🔐 AUTH
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # 📝 ROLE REGISTRATION
    path("register/police/", views.police_register, name="police_register"),
    path("register/hospital/", views.hospital_register, name="hospital_register"),

    # 🏢 DASHBOARDS
    path("dashboard/police/", views.police_dashboard, name="police_dashboard"),
    path("dashboard/hospital/", views.hospital_dashboard, name="hospital_dashboard"),

    # 🚨 ALERT SYSTEM
    path("send-alert/", views.send_alert, name="send_alert"),
    path("alerts/", views.alerts_api, name="alerts_api"),

    # 🔔 NOTIFICATIONS
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/count/", views.unread_notifications_count, name="notif_count"),
    path("notifications/clear/", views.clear_notifications, name="clear_notifications"),

    # 📍 LOCATION & MAP
    path("update-location/", views.update_location, name="update_location"),
    path("live-locations/", views.get_live_locations, name="live_locations"),
    path("map/", views.map_view, name="map"),
    path("reverse-geocode/", views.reverse_geocode, name="reverse_geocode"),
    path("nearby-services/", views.nearby_emergency_services, name="nearby_services"),
    path("police/broadcast/<int:assignment_id>/", views.police_broadcast, name="police_broadcast"),
    path("police/resolve/<int:assignment_id>/", views.resolve_alert, name="resolve_alert"),

]
