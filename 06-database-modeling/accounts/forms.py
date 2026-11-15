from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


# 회원가입용 Form
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()

        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'gender',
            'age',
            'weekly_reading_hours',
            'annual_reading_count',
            'profile_image',
        )


# 회원정보 수정용 Form
class CustomUserChangeForm(UserChangeForm):
    # 회원정보 수정 화면에서 비밀번호 해시 관련 항목 제외
    password = None

    class Meta(UserChangeForm.Meta):
        model = get_user_model()

        fields = (
            'email',
            'first_name',
            'last_name',
            'gender',
            'age',
            'weekly_reading_hours',
            'annual_reading_count',
            'profile_image',
        )