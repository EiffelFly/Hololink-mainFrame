from django import forms
from .models import Project
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class ProjectForm(forms.ModelForm):

    name = forms.CharField(
        label=_('Galaxy Name'),
        required = True,
        widget=forms.TextInput(
            attrs={
                'style':'',
                'autocomplete':'off',
            },
        ),
    )

    galaxy_description = forms.CharField(
        label=_('Galaxy Description'),
        required = False,
        widget=forms.Textarea(
            attrs={
                'style':'',
                'autocomplete':'off',
                'rows':3,
            },
        ),
    )

    galaxy_visibility = forms.ChoiceField(
        required=True,
        label=_('Galaxy Visibility'),
        choices=Project.PROJECT_VISIBILITY_CHOICES,
        initial='Private',
        widget=forms.RadioSelect(
            choices=Project.PROJECT_VISIBILITY_CHOICES,
            attrs={
                'class':'custom-radio-list'
            }
            
        )
    )

    

    def clean_name(self):
        name = self.cleaned_data['name']
        if Project.objects.filter(name=name).exists():
            self.add_error(
                'name',
                ValidationError(
                    _('The project name has already been used.'),
                    code='invalid'
                )
            )
        return name

    class Meta:
        model = Project
        fields = ['name', 'galaxy_description', 'galaxy_visibility']


class GalaxySettingsForm(forms.ModelForm):
    name = forms.CharField(
        label=_('Galaxy Name'),
        required = True,
        widget=forms.TextInput(
            attrs={
                'style':'',
                'autocomplete':'off',
            },
        ),
    )

    galaxy_description = forms.CharField(
        label=_('Galaxy Description'),
        required = False,
        widget=forms.Textarea(
            attrs={
                'style':'',
                'autocomplete':'off',
                'rows':3,
            },
        ),
    )

    galaxy_visibility = forms.ChoiceField(
        required=True,
        label=_('Galaxy Visibility'),
        choices=Project.PROJECT_VISIBILITY_CHOICES,
        initial='Private',
        widget=forms.RadioSelect(
            choices=Project.PROJECT_VISIBILITY_CHOICES,
            attrs={
                'class':'custom-radio-list'
            }
            
        )
    )

    class Meta:
        model = Project
        fields = ['name', 'galaxy_description', 'galaxy_visibility']

