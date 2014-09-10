from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from rango.models import Category, Page, UserProfile

class CategoryForm(forms.ModelForm):
    name = forms.CharField(max_length=128, help_text="Please enter the category name.")
    views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
    likes = forms.IntegerField(widget=forms.HiddenInput(), initial=0)

    class Meta:
        model = Category
        fields = ('name', 'views', 'likes')

class PageForm(forms.ModelForm):
    title = forms.CharField(max_length=128, help_text="Please enter the title of the page.")
    url = forms.URLField(max_length=200, help_text="Please enter the url of the page.")
    views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)

    class Meta:
        model = Page
        fields = ('title', 'url', 'views')

    def clean(self):
        cleaned_data = self.cleaned_data
        url = cleaned_data.get('url')
        if url and not url.startswith('http://'):
            url = 'http://' + url
            cleaned_data['url'] = url

        return cleaned_data

class UserForm(UserCreationForm):
    username = forms.CharField(help_text="Please enter a username", widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    email = forms.EmailField(help_text="Please enter your email", required=True, widget=forms.TextInput(attrs={'placeholder': 'E-mail address'}))
    first_name = forms.CharField(help_text="Please enter your first name", required=True, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(help_text="Please enter your last name", required=True, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), help_text="Please enter a password")
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), help_text="Please enter a password")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User._default_manager.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError('Email you are using already exists')

    def save(self, commit=True):
        user = super(UserForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.is_active = False
            user.save()

        return user

class UserProfileForm(forms.ModelForm):
    website = forms.URLField(help_text="Please enter your website", required=False, widget=forms.PasswordInput(attrs={'placeholder': 'Website'}))
    picture = forms.ImageField(help_text="Select a profile image to upload", required=False)

    class Meta:
        model = UserProfile
        fields = ('website', 'picture')