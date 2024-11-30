
from datetime import timedelta, datetime, date
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max, Sum, F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now, localtime, localdate
import pandas as pd
from .models import DailyLog, LeaveRequest
from .forms import PersonnelForm

# Dynamic User Model
User = get_user_model()

# View Definitions
def homepage(request):
    return render(request, 'homepage.html')


def yetkili_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('yetkili_paneli')
        else:
            return render(request, 'yetkili_login.html', {'error': 'Invalid credentials or unauthorized user.'})

    return render(request, 'yetkili_login.html')


@login_required
def yetkili_paneli(request):
    if not request.user.is_staff:
        return redirect('homepage')

    def format_remaining_leave(total_minutes):
        days = total_minutes // (8 * 60)
        hours = (total_minutes % (8 * 60)) // 60
        return f"{days} gün {hours} saat"

    if request.method == 'POST':
        form = PersonnelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('yetkili_paneli')

    form = PersonnelForm()
    personnel = User.objects.filter(is_staff=False)
    today = date.today()

    personnel_data = []
    for person in personnel:
        total_leave_minutes = 15 * 8 * 60

        logs = DailyLog.objects.filter(user=person).values("date").distinct()
        for log_date in logs:
            daily_logs = DailyLog.objects.filter(user=person, date=log_date["date"])

            total_work_time_seconds = 0
            for log in daily_logs:
                if log.check_in_time and log.check_out_time:
                    total_work_time_seconds += (log.check_out_time - log.check_in_time).seconds

            total_work_minutes = total_work_time_seconds // 60
            missing_time_minutes = max(0, 8 * 60 - total_work_minutes)
            total_leave_minutes -= missing_time_minutes

        formatted_remaining_leave = format_remaining_leave(total_leave_minutes)
        less_than_3_days = "Evet" if total_leave_minutes < 3 * 8 * 60 else "Hayır"

        today_logs = DailyLog.objects.filter(user=person, date=today)
        first_check_in = None
        for log in today_logs:
            if log.check_in_time and (not first_check_in or log.check_in_time < first_check_in):
                first_check_in = log.check_in_time
        today_late = "Evet" if first_check_in and first_check_in.hour >= 8 else "Hayır"

        personnel_data.append({
            "id": person.id,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "username": person.username,
            "remaining_leave": formatted_remaining_leave,
            "less_than_3_days": less_than_3_days,
            "today_late": today_late,
        })

    leave_requests = LeaveRequest.objects.select_related('user').all()

    return render(request, 'yetkili_paneli.html', {
        'personnel': personnel_data,
        'form': form,
        'leave_requests': leave_requests,
    })


def personel_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and not user.is_staff:
            login(request, user)
            return redirect('personel_paneli')
        else:
            return render(request, 'personel_login.html', {'error': 'Invalid credentials or unauthorized user.'})
    return render(request, 'personel_login.html')


@login_required
def personel_paneli(request):
    context = {
        'user': request.user,
        'example_data': 'Some data here',
    }
    return render(request, 'personel_paneli.html', context)


@login_required
def remove_personnel(request, pk):
    if not request.user.is_staff:
        return redirect('homepage')

    personnel = get_object_or_404(User, pk=pk)
    if not personnel.is_staff:
        personnel.delete()
    return redirect('yetkili_paneli')


def user_logout(request):
    logout(request)
    return redirect('/')


@login_required
def check_in(request):
    if request.method == 'POST':
        try:
            existing_log = DailyLog.objects.filter(user=request.user, check_out_time=None).first()

            if existing_log:
                formatted_time = localtime(existing_log.check_in_time).strftime('%Y-%m-%d %H:%M:%S')
                return JsonResponse({'message': f'Zaten Şu Zamanda Giriş Yapılmış: {formatted_time}'}, status=200)

            new_log = DailyLog.objects.create(user=request.user, check_in_time=now())
            formatted_time = localtime(new_log.check_in_time).strftime('%Y-%m-%d %H:%M:%S')
            return JsonResponse({'message': f'Personel Girişi Yapıldı: {formatted_time}'}, status=200)
        except Exception as e:
            return JsonResponse({'message': f'Error during check-in: {str(e)}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)


@login_required
def check_out(request):
    if request.method == 'POST':
        try:
            log = DailyLog.objects.get(user=request.user, check_out_time=None)
            log.check_out_time = now()
            log.save()
            formatted_time = localtime(log.check_out_time).strftime('%Y-%m-%d %H:%M:%S')
            return JsonResponse({'message': f'Personel Çıkışı Yapıldı: {formatted_time}'})
        except DailyLog.DoesNotExist:
            return JsonResponse({'message': 'Personel İçin Aktif Giriş Kaydı Bulunamadı.'}, status=400)
        except Exception as e:
            return JsonResponse({'message': f'Error during check-out: {str(e)}'}, status=500)
    return JsonResponse({'message': 'Invalid request method.'}, status=405)


def home(request):
    return HttpResponse("Ana Sayfaya Hoşgeldiniz!")


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('personel_paneli')
        else:
            return render(request, 'login.html', {'error': 'Hatalı kullanıcı adı veya şifre.'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
def approve_leave_request(request, request_id):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok.'}, status=403)

    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    user = leave_request.user
    days_requested = leave_request.days_requested

    try:
        current_total_hours = (user.remaining_leave_days * 8) + user.remaining_leave_hours
        additional_hours = days_requested * 8
        new_total_hours = current_total_hours + additional_hours

        new_days = new_total_hours // 8
        new_hours = new_total_hours % 8

        user.remaining_leave_days = new_days
        user.remaining_leave_hours = new_hours
        user.save()

        formatted_remaining_leave = f"{new_days} gün {new_hours} saat"
        leave_request.delete()

        return JsonResponse({
            'success': True,
            'message': f'İzin talebi onaylandı. Yeni kalan izin: {formatted_remaining_leave}',
            'user_id': user.id,
            'new_remaining_leave': formatted_remaining_leave
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Hata: {str(e)}'}, status=500)


@login_required
def reject_leave_request(request, request_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    leave_request = get_object_or_404(LeaveRequest, id=request_id)

    if request.method == 'POST':
        leave_request.delete()
        return JsonResponse({'success': True, 'message': 'Leave request rejected successfully.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@login_required
def work_hours_entry(request, pk):
    person = get_object_or_404(User, pk=pk)

    total_leave_minutes = 15 * 8 * 60
    logs = DailyLog.objects.filter(user=person).values("date").distinct()
    summary_data = []

    for log_date in logs:
        daily_logs = DailyLog.objects.filter(user=person, date=log_date["date"])

        total_work_time_seconds = 0
        first_check_in = None
        last_check_out = None

        for entry in daily_logs:
            if entry.check_in_time and entry.check_out_time:
                work_duration = (entry.check_out_time - entry.check_in_time).seconds
                total_work_time_seconds += work_duration
                if not first_check_in or entry.check_in_time < first_check_in:
                    first_check_in = entry.check_in_time
                if not last_check_out or entry.check_out_time > last_check_out:
                    last_check_out = entry.check_out_time

        total_work_time_minutes = total_work_time_seconds // 60
        total_hours = total_work_time_minutes // 60
        total_minutes = total_work_time_minutes % 60
        formatted_total_work_time = f"{total_hours}:{total_minutes:02d}"

        missing_time = max(0, 8 * 60 - total_work_time_minutes)
        missing_hours = missing_time // 60
        missing_minutes = missing_time % 60
        formatted_missing_time = f"{missing_hours}:{missing_minutes:02d}"

        late = "Evet" if first_check_in and first_check_in.hour >= 8 else "Hayır"
        late_duration = "-"
        if late == "Evet" and first_check_in:
            late_minutes = ((first_check_in.hour - 8) * 60) + first_check_in.minute
            late_duration_hours = late_minutes // 60
            late_duration_minutes = late_minutes % 60
            late_duration = f"{late_duration_hours}:{late_duration_minutes:02d}"

        total_leave_minutes -= missing_time
        remaining_days = total_leave_minutes // (8 * 60)
        remaining_hours = (total_leave_minutes % (8 * 60)) // 60
        formatted_remaining_leave = f"{remaining_days} gün {remaining_hours} saat"

        less_than_3_days = "Evet" if remaining_days < 3 else "Hayır"

        summary_data.append({
            "date": log_date["date"],
            "first_check_in": first_check_in,
            "last_check_out": last_check_out,
            "total_work_time": formatted_total_work_time,
            "missing_hours": formatted_missing_time,
            "late": late,
            "late_duration": late_duration,
            "remaining_leave": formatted_remaining_leave,
            "less_than_3_days": less_than_3_days,
        })

    work_logs = DailyLog.objects.filter(user=person).order_by("check_in_time")

    return render(request, "work_hours_entry.html", {
        "person": person,
        "summary_data": summary_data,
        "work_logs": work_logs,
    })


@login_required
def download_report(request, pk):
    person = get_object_or_404(User, pk=pk)
    daily_logs = DailyLog.objects.filter(user=person).order_by("check_in_time")

    summary_data = []
    total_leave_minutes = 15 * 8 * 60

    grouped_logs = {}
    for log in daily_logs:
        date_key = log.date
        if date_key not in grouped_logs:
            grouped_logs[date_key] = []
        grouped_logs[date_key].append(log)

    for date, logs in grouped_logs.items():
        first_check_in = min([log.check_in_time for log in logs if log.check_in_time])
        last_check_out = max([log.check_out_time for log in logs if log.check_out_time])

        total_work_time_seconds = sum(
            (log.check_out_time - log.check_in_time).total_seconds()
            for log in logs
            if log.check_in_time and log.check_out_time
        )
        total_work_time = timedelta(seconds=total_work_time_seconds)
        missing_time = max(timedelta(hours=8) - total_work_time, timedelta(seconds=0))

        total_leave_minutes -= int(missing_time.total_seconds() / 60)
        remaining_days = total_leave_minutes // (8 * 60)
        remaining_hours = (total_leave_minutes % (8 * 60)) // 60
        formatted_remaining_leave = f"{remaining_days} gün {remaining_hours} saat"

        late = "Evet" if first_check_in and first_check_in.hour >= 8 else "Hayır"
        late_duration = "-"
        if late == "Evet":
            late_minutes = (first_check_in.hour - 8) * 60 + first_check_in.minute
            late_duration = f"{late_minutes // 60}:{late_minutes % 60:02d}"

        less_than_3_days = "Evet" if remaining_days < 3 else "Hayır"

        summary_data.append({
            "Tarih": date.strftime("%d-%m-%Y"),
            "İlk Giriş": first_check_in.strftime("%H:%M") if first_check_in else "-",
            "Son Çıkış": last_check_out.strftime("%H:%M") if last_check_out else "-",
            "Toplam Çalışma Süresi": f"{int(total_work_time.seconds // 3600)}:{(total_work_time.seconds % 3600) // 60:02d}",
            "Toplam Eksik": f"{int(missing_time.seconds // 3600)}:{(missing_time.seconds % 3600) // 60:02d}",
            "Geç Kalma": late,
            "Geç Kalma Süresi": late_duration,
            "Toplam Kalan İzin": formatted_remaining_leave,
            "Kalan İzin 3 Günden Az Mı?": less_than_3_days,
        })

    detailed_data = [
        {
            "Tarih": log.date.strftime("%d-%m-%Y"),
            "Giriş Saati": log.check_in_time.strftime("%H:%M") if log.check_in_time else "-",
            "Çıkış Saati": log.check_out_time.strftime("%H:%M") if log.check_out_time else "-",
        }
        for log in daily_logs
    ]

    summary_df = pd.DataFrame(summary_data)
    detailed_df = pd.DataFrame(detailed_data)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{person.first_name}_{person.last_name}_report.xlsx"'

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Günlük Özet", index=False)
        detailed_df.to_excel(writer, sheet_name="Ayrıntılı Çalışma Saatleri", index=False)

    return response


def work_hours_summary(request, user_id):
    logs = (
        DailyLog.objects.filter(user_id=user_id)
        .values("date")
        .annotate(
            first_check_in=Min("check_in_time"),
            last_check_out=Max("check_out_time"),
            total_hours=Sum(F("check_out_time") - F("check_in_time")),
        )
    )

    summary_data = []
    for log in logs:
        total_work_time = log["total_hours"]
        total_work_hours = total_work_time.total_seconds() / 3600 if total_work_time else 0
        missing_hours = max(0, 8 - total_work_hours)

        first_check_in_time = log["first_check_in"]
        late = "Evet" if first_check_in_time and first_check_in_time.hour >= 8 else "Hayır"

        summary_data.append({
            "date": log["date"],
            "first_check_in": first_check_in_time,
            "last_check_out": log["last_check_out"],
            "total_work_hours": round(total_work_hours, 2),
            "missing_hours": round(missing_hours, 2),
            "late": late,
        })

    return render(request, "work_hours_summary.html", {"summary_data": summary_data})


@login_required
def leave_request(request):
    if request.method == "POST":
        days_requested = int(request.POST.get("days", 0))
        if days_requested < 1 or days_requested > 30:
            return JsonResponse({"error": "Lütfen 1 ile 30 arasında bir değer girin."}, status=400)

        LeaveRequest.objects.create(user=request.user, days_requested=days_requested)
        return JsonResponse({"message": f"{days_requested} gün izin talebiniz başarıyla oluşturuldu."}, status=200)

    return JsonResponse({"error": "Geçersiz istek yöntemi."}, status=400)
