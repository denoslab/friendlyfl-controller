from django import forms


class SiteForm(forms.Form):
    name = forms.CharField(label='Site Name', max_length=100)
    description = forms.CharField(label='Site Description', widget=forms.Textarea)

