from .models import CustomUser
from django import forms
from .models import DailyLog

class PersonnelForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'password', 'remaining_leave_days']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash the password
        if commit:
            user.save()
        return user

class WorkHoursForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['check_in_time', 'check_out_time']  # 'date' alanını dahil etmeyin

