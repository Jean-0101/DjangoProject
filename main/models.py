from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.http import JsonResponse
from django.utils.timezone import now, localdate

class CustomUser(AbstractUser):
    remaining_leave_days = models.IntegerField(default=0)
    remaining_leave_hours = models.IntegerField(default=0)

    # Override related_name to resolve potential conflicts with Django's auth system
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_custom_set',  # Ensure unique related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_custom_set',  # Ensure unique related_name
        blank=True,
    )

    def formatted_remaining_leave(self):
        """Return a formatted string of remaining leave."""
        return f"{self.remaining_leave_days} gün {self.remaining_leave_hours} saat"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"


class DailyLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=now, null=False, blank=False)  # Tarih alanı
    check_in_time = models.DateTimeField(null=True, blank=True)  # Giriş zamanı
    check_out_time = models.DateTimeField(null=True, blank=True)  # Çıkış zamanı

    def get_total_work_time(self):
        if self.check_in_time and self.check_out_time:
            total_seconds = (self.check_out_time - self.check_in_time).total_seconds()
            total_minutes = total_seconds // 60
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{int(hours)}:{int(minutes):02d}"
        return "0:00"

    def get_missing_time(self):
        total_work_time_minutes = 0
        if self.check_in_time and self.check_out_time:
            total_work_time_minutes = (self.check_out_time - self.check_in_time).total_seconds() // 60

        missing_time_minutes = max(0, 8 * 60 - total_work_time_minutes)
        hours = missing_time_minutes // 60
        minutes = missing_time_minutes % 60
        return f"{int(hours)}:{int(minutes):02d}"

    def is_late(self):
        if self.check_in_time and self.check_in_time.hour >= 8:
            return True
        return False

    def get_late_duration(self):
        if self.is_late() and self.check_in_time:
            late_minutes = (self.check_in_time.hour - 8) * 60 + self.check_in_time.minute
            hours = late_minutes // 60
            minutes = late_minutes % 60
            return f"{int(hours)}:{int(minutes):02d}"
        return "-"


class LeaveRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    days_requested = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.days_requested} gün"


class WorkHour(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()


# Check-in Functionality
def check_in(request):
    if request.method == 'POST':
        try:
            # Check if the user already has an active log
            existing_log = DailyLog.objects.filter(user=request.user, check_out_time=None).first()

            if existing_log:
                return JsonResponse({
                    'success': True,
                    'message': f'Already checked in at: {existing_log.check_in_time.strftime("%Y-%m-%d %H:%M")}'
                }, status=200)

            # Create a new log entry
            new_log = DailyLog.objects.create(
                user=request.user,
                date=localdate(),  # Today's date
                check_in_time=now()  # Check-in time
            )
            return JsonResponse({
                'success': True,
                'message': f'Personel Girişi Yapıldı: {new_log.check_in_time.strftime("%Y-%m-%d %H:%M")}'
            }, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error during check-in: {str(e)}'}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
