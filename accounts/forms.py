from django import forms
from .models import Account

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter Password',
        'class': 'form-control' # can be give css style class here 
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm Password'
    }))
    
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'phone' , 'password']
    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs) #overwriting the default attributes
        self.fields['first_name'].widget.attrs['placeholder']='Enter first name'
        self.fields['last_name'].widget.attrs['placeholder']='Enter last name'
        self.fields['email'].widget.attrs['placeholder']='Enter email address'
        self.fields['phone'].widget.attrs['placeholder']='Enter phone number'
        for field in self.fields:
            self.fields[field].widget.attrs['class']='form-control' #adding css style class to all fields

    # inbuild clean method to get data from form and perform validation
    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError('password does not match')