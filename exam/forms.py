from django import forms
from .models import Question, Choice, Exam, QuestionBank, Subject, CustomUser
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'question_type', 'text', 'explanation', 'points', 'difficulty',
            'is_active', 'image', 'audio', 'video', 'exam', 'question_bank'
        ]
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Enter question text...'}),
            'explanation': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Explanation (optional)...'}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'exam': forms.Select(attrs={'class': 'form-control'}),
            'question_bank': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['exam'].empty_label = "Select Exam (Optional)"
        self.fields['question_bank'].empty_label = "Select Question Bank (Optional)"
        if user and user.user_type == 'teacher':
            self.fields['exam'].queryset = Exam.objects.filter(created_by=user)
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(created_by=user)
        else:
            self.fields['exam'].queryset = Exam.objects.all()
            self.fields['question_bank'].queryset = QuestionBank.objects.all()


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter choice text...'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.HiddenInput(),
        }


ChoiceFormSet = forms.inlineformset_factory(
    Question, Choice, form=ChoiceForm, extra=4, can_delete=True, max_num=6
)

class BulkQuestionForm(forms.Form):
    question_bank = forms.ModelChoiceField(
        queryset=QuestionBank.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Question Bank (Optional)"
    )
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Exam (Optional)"
    )
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload CSV file with questions. Format: question_text,choice1,choice2,choice3,choice4,correct_answer_index',
        widget=forms.FileInput(attrs={
            'class': 'form-control', 
            'accept': '.csv',
            'required': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BulkQuestionForm, self).__init__(*args, **kwargs)
        
        if user and user.user_type == 'teacher':
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(created_by=user)
            self.fields['exam'].queryset = Exam.objects.filter(created_by=user)
        else:
            # Jika bukan teacher, tampilkan semua (untuk admin)
            self.fields['question_bank'].queryset = QuestionBank.objects.all()
            self.fields['exam'].queryset = Exam.objects.all()

class QuestionBankForm(forms.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ['name', 'description', 'subject', 'is_shared']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter question bank name...',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter description (optional)...'
            }),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'is_shared': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(QuestionBankForm, self).__init__(*args, **kwargs)
        # Pastikan subject queryset ada
        self.fields['subject'].queryset = Subject.objects.all()
        
        # Untuk teacher, filter subjects berdasarkan department mereka jika ada
        if user and user.user_type == 'teacher':
            # Anda bisa menambahkan logika filter di sini jika diperlukan
            pass

class ExamForm(forms.ModelForm):
    # Field tambahan non-model
    auto_generate_token = forms.BooleanField(
        required=False,
        initial=True,
        label="Auto-generate token",
        help_text="Automatically generate 6-digit access token when exam is published"
    )
    custom_token = forms.CharField(
        max_length=6,
        required=False,
        label="Custom Token",
        help_text="Optional: Enter custom 6-digit token (letters and numbers only)",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., A1B2C3',
            'style': 'text-transform: uppercase; font-family: monospace;',
            'class': 'token-input'
        })
    )
    token_expiry = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text="Optional: Set when the token should expire"
    )

    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'exam_type', 'subject',
            'duration_minutes', 'start_time', 'end_time', 'result_publish_time',
            'passing_score', 'max_attempts', 'shuffle_questions', 'shuffle_choices',
            'show_result_immediately', 'allow_back_navigation', 'require_webcam',
            'require_microphone', 'enable_proctoring', 'allowed_departments',
            'allowed_users', 'status', 'auto_generate_token', 'custom_token', 'token_expiry'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'result_publish_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'status': 'Token will be auto-generated when status is set to "Published".',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial nilai token
        if self.instance and self.instance.access_token:
            self.fields['auto_generate_token'].initial = False
            self.fields['custom_token'].initial = self.instance.access_token
        else:
            self.fields['auto_generate_token'].initial = True

    def clean_custom_token(self):
        token = self.cleaned_data.get('custom_token', '').strip().upper()
        if token:
            if len(token) != 6:
                raise forms.ValidationError("Token must be exactly 6 characters long.")
            if not token.isalnum():
                raise forms.ValidationError("Token can only contain letters and numbers.")
            if Exam.objects.filter(access_token=token).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("This token is already in use.")
        return token

    def clean(self):
        cleaned_data = super().clean()
        auto_generate = cleaned_data.get('auto_generate_token')
        custom_token = cleaned_data.get('custom_token')
        status = cleaned_data.get('status')

        if status == 'published' and not auto_generate and not custom_token:
            raise forms.ValidationError(
                "Please enable auto-generate token or provide a custom token for published exams."
            )
        return cleaned_data

    def save(self, commit=True):
        exam = super().save(commit=False)
        auto_generate = self.cleaned_data.get('auto_generate_token', True)
        custom_token = self.cleaned_data.get('custom_token', '').strip().upper()

        if custom_token:
            exam.access_token = custom_token
        elif auto_generate and exam.status == 'published' and not exam.access_token:
            exam.generate_token()
        elif not auto_generate and not custom_token and exam.status == 'published':
            exam.access_token = None

        exam.token_expiry = self.cleaned_data.get('token_expiry')
        if commit:
            exam.save()
            self.save_m2m()
        return exam


class SimpleQuestionForm(forms.ModelForm):
    """Form sederhana untuk quick question creation"""
    class Meta:
        model = Question
        fields = ['question_type', 'text', 'points', 'difficulty']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter question text...'
            }),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1,
                'value': 1
            }),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
        }

class TrueFalseQuestionForm(forms.ModelForm):
    """Form khusus untuk soal True/False"""
    TRUE_FALSE_CHOICES = [
        (True, 'True'),
        (False, 'False'),
    ]
    
    correct_answer = forms.ChoiceField(
        choices=TRUE_FALSE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Correct Answer'
    )
    
    class Meta:
        model = Question
        fields = ['text', 'explanation', 'points', 'difficulty']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter True/False question...'
            }),
            'explanation': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'Explanation (optional)...'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1,
                'value': 1
            }),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
        }

class EssayQuestionForm(forms.ModelForm):
    """Form khusus untuk soal Essay"""
    class Meta:
        model = Question
        fields = ['text', 'explanation', 'points', 'difficulty']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter essay question...'
            }),
            'explanation': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'Expected answer or grading criteria...'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1,
                'value': 5
            }),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
        }

# Form untuk filter dan pencarian
class QuestionFilterForm(forms.Form):
    QUESTION_TYPE_CHOICES = [
        ('', 'All Types'),
        ('MC', 'Multiple Choice'),
        ('TF', 'True/False'),
        ('FB', 'Fill in Blank'),
        ('ESS', 'Essay'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('', 'All Difficulties'),
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    question_type = forms.ChoiceField(
        choices=QUESTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    question_bank = forms.ModelChoiceField(
        queryset=QuestionBank.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="All Question Banks"
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search questions...'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(QuestionFilterForm, self).__init__(*args, **kwargs)
        
        if user and user.user_type == 'teacher':
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(created_by=user)

class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'user_type', 'is_active', 'is_staff']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'user_type': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
        }

class AdminCreateUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'password1', 'password2',
            'first_name', 'last_name', 'email',
            'phone', 'date_of_birth', 'profile_picture',
            'user_type', 'department'
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded-lg p-2'
            }),
            'first_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'phone': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'user_type': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("⚠ Username sudah dipakai. Coba yang lain.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("⚠ Email ini sudah terdaftar.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if password and len(password) < 8:
            raise forms.ValidationError("⚠ Password minimal 8 karakter.")
        return password

from django import forms
from django.core.exceptions import ValidationError
from exam.models import CustomUser

class AdminUserEditForm(forms.ModelForm):
    # Password opsional → user bisa biarkan kosong
    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Leave blank to keep current password"})
    )
    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat password"})
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'profile_picture', 'user_type', 'is_active', 'is_staff'
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg bg-[#fafafa]'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = CustomUser.objects.filter(username=username).exclude(id=self.instance.id)
        if qs.exists():
            raise ValidationError("Username already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            qs = CustomUser.objects.filter(email=email).exclude(id=self.instance.id)
            if qs.exists():
                raise ValidationError("Email already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 or p2:
            if p1 != p2:
                raise ValidationError("Passwords do not match.")
            if len(p1) < 8:
                raise ValidationError("Password must be at least 8 characters.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get("password1")
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user
