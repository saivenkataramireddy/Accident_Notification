from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction, OperationalError
import requests, json, time
from django.conf import settings


from .models import (
    Alert,
    UserLocation,
    Notification,
    UserProfile,
    PoliceStation,
    Hospital,
    AlertAssignment
)
from .utils import calculate_distance


@login_required
def home(request):
    unread_count = request.user.notifications.filter(is_read=False).count()
    return render(request, "index.html", {
        "unread_count": unread_count
    })


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            profile, _ = UserProfile.objects.get_or_create(
                user=user, defaults={"role": "user"}
            )

            if profile.role == "police":
                return redirect("police_dashboard")
            elif profile.role == "hospital":
                return redirect("hospital_dashboard")
            else:
                return redirect("home")

        messages.error(request, "Invalid username or password")

    return render(request, "login.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # ✅ CHECK IF USERNAME EXISTS
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return render(request, "register.html")

        # ✅ CREATE USER
        user = User.objects.create_user(
            username=username,
            password=password
        )

        # ✅ CREATE PROFILE
        UserProfile.objects.get_or_create(
            user=user,
            defaults={"role": "user"}
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    return render(request, "register.html")


def logout_view(request):
    logout(request)
    return redirect("login")




@login_required
def send_alert(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        lat = float(request.POST.get("latitude"))
        lon = float(request.POST.get("longitude"))
        address = request.POST.get("address", "")
        description = request.POST.get("description", "")

        # ✅ 1. Create Alert (NO status field here)
        alert = Alert.objects.create(
            user=request.user,
            latitude=lat,
            longitude=lon,
            address=address,
            description=description
        )

        # ✅ 2. Assign police (hospital optional)
        police, hospital = get_nearest_police_and_hospital(lat, lon)

        assignment = AlertAssignment.objects.create(
            alert=alert,
            police=police,
            hospital=hospital,
            status="assigned"
        )

        # ✅ 3. Notify police
        Notification.objects.create(
            user=police.user,
            title="🚨 New Emergency Case",
            message=address,
            latitude=lat,
            longitude=lon,
            address=address
        )

        return JsonResponse({"status": "success"})

    except Exception as e:
        print("SEND ALERT ERROR:", e)
        return JsonResponse({"error": str(e)}, status=500)



@login_required
def reverse_geocode(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "json",
        "lat": lat,
        "lon": lon
    }

    headers = {
        "User-Agent": "AccidentAlertSystem/1.0"
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return JsonResponse({
            "address": data.get("display_name", "Unknown location")
        })

    return JsonResponse({"error": "Unable to fetch location"}, status=400)

@login_required
def notifications(request):
    notifications = request.user.notifications.order_by("-created_at")
    return render(request, "notifications.html", {
        "notifications": notifications
    })


@login_required
def unread_notifications_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({"count": count})

@login_required
def update_location(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        # 🔹 Case 1: JSON request
        if request.content_type == "application/json":
            data = json.loads(request.body.decode("utf-8"))
            lat = data.get("lat")
            lon = data.get("lon")

        # 🔹 Case 2: FormData request
        else:
            lat = request.POST.get("latitude") or request.POST.get("lat")
            lon = request.POST.get("longitude") or request.POST.get("lon")

        if lat is None or lon is None:
            return JsonResponse({"error": "Invalid data"}, status=400)

        lat = float(lat)
        lon = float(lon)

        for _ in range(3):  # retry to avoid sqlite lock
            try:
                with transaction.atomic():
                    UserLocation.objects.update_or_create(
                        user=request.user,
                        defaults={
                            "latitude": lat,
                            "longitude": lon,
                        },
                    )
                return JsonResponse({"status": "ok"})
            except OperationalError:
                time.sleep(0.2)

        return JsonResponse({"error": "db locked"}, status=500)

    except Exception as e:
        print("Update location error:", e)
        return JsonResponse({"error": "Bad request"}, status=400)


@login_required
def get_live_locations(request):
    locations = UserLocation.objects.select_related("user")

    data = []
    for loc in locations:
        data.append({
            "username": loc.user.username,
            "latitude": loc.latitude,
            "longitude": loc.longitude
        })

    return JsonResponse({"locations": data})

@login_required
def map_view(request):
    return render(request, "map.html")

@login_required
def alerts_api(request):
    alerts = Alert.objects.all().order_by("-created_at")[:50]

    data = []
    for alert in alerts:
        data.append({
            "id": alert.id,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "address": alert.address,
        })

    return JsonResponse({"alerts": data})




def send_push(user, title, message):
    payload = {
        "title": title,
        "body": message
    }

@require_POST
@login_required
def clear_notifications(request):
    request.user.notifications.all().delete()
    return redirect('notifications')


@login_required
def nearby_emergency_services(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return JsonResponse({"error": "Missing coordinates"}, status=400)

    query = f"""
    [out:json];
    (
      node["amenity"="police"](around:5000,{lat},{lon});
      node["amenity"="hospital"](around:5000,{lat},{lon});
    );
    out body;
    """

    headers = {
        "User-Agent": "AccidentAlertSystem/1.0 (contact@example.com)"
    }

    response = requests.post(
        "https://overpass-api.de/api/interpreter",
        data=query,
        headers=headers,
        timeout=15
    )

    # ✅ CHECK STATUS FIRST
    if response.status_code != 200:
        return JsonResponse({
            "error": "Overpass API failed",
            "status": response.status_code,
            "response": response.text[:500]
        }, status=500)

    # ✅ SAFE JSON PARSE
    try:
        data = response.json()
    except ValueError:
        return JsonResponse({
            "error": "Invalid JSON from Overpass API",
            "raw": response.text[:500]
        }, status=500)

    results = []
    for item in data.get("elements", []):
        results.append({
            "name": item.get("tags", {}).get("name", "Unknown"),
            "type": item.get("tags", {}).get("amenity"),
            "latitude": item.get("lat"),
            "longitude": item.get("lon"),
            "address": item.get("tags", {}).get("addr:full", "")
        })

    return JsonResponse({"services": results})



@login_required
def police_dashboard(request):
    profile = request.user.userprofile

    if profile.role != "police":
        return redirect("home")

    police = PoliceStation.objects.get(user=request.user)

    alerts = AlertAssignment.objects.select_related(
        "alert", "alert__user"
    ).filter(police=police).order_by("-created_at")

    return render(request, "police_dashboard.html", {
        "alerts": alerts
    })


@login_required
def police_broadcast(request, assignment_id):
    assignment = AlertAssignment.objects.select_related("alert").get(id=assignment_id)

    if request.user.userprofile.role != "police":
        return redirect("home")

    message = request.POST.get("message")
    lat = assignment.alert.latitude
    lon = assignment.alert.longitude

    nearby_users = UserLocation.objects.exclude(user=request.user)

    for loc in nearby_users:
        if calculate_distance(lat, lon, loc.latitude, loc.longitude) <= 5:
            Notification.objects.create(
                user=loc.user,
                title="🚔 Police Alert",
                message=message,
                latitude=lat,
                longitude=lon,
                address=assignment.alert.address
            )

    messages.success(request, "Alert broadcast sent")
    return redirect("police_dashboard")

@login_required
def resolve_alert(request, assignment_id):
    assignment = AlertAssignment.objects.get(id=assignment_id)

    if request.user.userprofile.role != "police":
        return redirect("home")

    assignment.status = "resolved"
    assignment.save()

    assignment.alert.status = "resolved"
    assignment.alert.save()

    Notification.objects.create(
        user=assignment.alert.user,
        title="✅ Case Resolved",
        message="Police have resolved your complaint",
        latitude=assignment.alert.latitude,
        longitude=assignment.alert.longitude,
        address=assignment.alert.address
    )

    return redirect("police_dashboard")


@login_required
def hospital_dashboard(request):
    profile = request.user.userprofile

    if profile.role != "hospital":
        return redirect("home")

    hospital = Hospital.objects.get(user=request.user)

    assignments = AlertAssignment.objects.select_related(
        "alert", "alert__user"
    ).filter(hospital=hospital).order_by("-created_at")

    return render(request, "hospital_dashboard.html", {
        "assignments": assignments,
        "hospital": hospital
    })


def get_nearest_police_and_hospital(lat, lon):
    police_list = PoliceStation.objects.all()
    hospital_list = Hospital.objects.all()

    if not police_list.exists() or not hospital_list.exists():
        raise Exception("No police or hospital registered")

    nearest_police = min(
        police_list,
        key=lambda p: calculate_distance(lat, lon, p.latitude, p.longitude)
    )

    nearest_hospital = min(
        hospital_list,
        key=lambda h: calculate_distance(lat, lon, h.latitude, h.longitude)
    )

    return nearest_police, nearest_hospital


def hospital_register(request):
    # Optional: block logged-in users
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        secret = request.POST.get("secret_code")

        # 🔐 ADD THIS HERE
        if secret != settings.HOSPITAL_SECRET_CODE:
            messages.error(request, "Invalid authorization code")
            return render(request, "hospital_register.html")

        username = request.POST["username"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, "hospital_register.html")

        user = User.objects.create_user(username=username, password=password)

        UserProfile.objects.create(user=user, role="hospital")

        Hospital.objects.create(
            user=user,
            hospital_name=request.POST["hospital_name"],
            latitude=request.POST["latitude"],
            longitude=request.POST["longitude"],
            phone=request.POST["phone"]
        )

        messages.success(request, "Hospital account created")
        return redirect("login")

    return render(request, "hospital_register.html")
def police_register(request):
    # Optional: block logged-in users
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        secret = request.POST.get("secret_code")

        # 🔐 ADD THIS HERE
        if secret != settings.POLICE_SECRET_CODE:
            messages.error(request, "Invalid authorization code")
            return render(request, "police_register.html")

        username = request.POST["username"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, "police_register.html")

        user = User.objects.create_user(username=username, password=password)

        UserProfile.objects.create(user=user, role="police")

        PoliceStation.objects.create(
            user=user,
            station_name=request.POST["station_name"],
            latitude=request.POST["latitude"],
            longitude=request.POST["longitude"],
            phone=request.POST["phone"]
        )

        messages.success(request, "Police account created")
        return redirect("login")

    return render(request, "police_register.html")
