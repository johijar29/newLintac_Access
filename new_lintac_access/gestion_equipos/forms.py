from django import forms
from django.contrib.contenttypes.models import ContentType
from .models import Equipamiento, Alumno, Funcionario, Ubicacion

class EquipamientoForm(forms.ModelForm):
    comentarios = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    class Meta:
        model = Equipamiento
        exclude = []
        widgets = {
            'anio_adquisicion': forms.NumberInput(attrs={'type': 'number', 'min': 1900, 'max': 2099, 'step': 1}),
            'estado': forms.Select(attrs={'class': 'custom-select'}),
        }
        labels = {
            'estado': 'Estado actual',
            'ubicacion': 'Ubicación actual',
        }

    def __init__(self, *args, **kwargs):
        super(EquipamientoForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        if 'instance' in kwargs and kwargs['instance']:
            equipamiento = kwargs['instance']
            self.fields['ubicacion'].queryset = Ubicacion.objects.filter(sede=equipamiento.ubicacion.sede)

class AsignarEquipamientoForm(forms.Form):
    equipamiento_id = forms.ModelChoiceField(
        queryset=Equipamiento.objects.none(),
        label="Equipamiento",
        empty_label="Seleccione un Equipamiento",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tipo_asignacion = forms.ChoiceField(
        choices=[('alumno', 'Alumno'), ('funcionario', 'Funcionario')],
        label="Asignar A",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    id_asignacion = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(AsignarEquipamientoForm, self).__init__(*args, **kwargs)
        self.fields['equipamiento_id'].queryset = Equipamiento.objects.filter(
            content_type__isnull=True, 
            object_id__isnull=True
        )

    def clean(self):
        cleaned_data = super().clean()
        tipo_asignacion = cleaned_data.get("tipo_asignacion")
        id_asignacion = cleaned_data.get("id_asignacion")

        if tipo_asignacion == 'alumno':
            if not Alumno.objects.filter(id=id_asignacion).exists():
                self.add_error('id_asignacion', 'El ID de Alumno no es válido.')
        elif tipo_asignacion == 'funcionario':
            if not Funcionario.objects.filter(id=id_asignacion).exists():
                self.add_error('id_asignacion', 'El ID de Funcionario no es válido.')

        return cleaned_data

class EnviarServicioTecnicoForm(forms.Form):
    descripcion = forms.CharField(label='Descripción', widget=forms.Textarea(attrs={'class': 'form-control'}))
    tipo_problema = forms.ChoiceField(label='Tipo de Problema', choices=[('fisico', 'Daño Físico'), ('software', 'Problema de Software')], widget=forms.Select(attrs={'class': 'form-control'}))
    equipo_reemplazo = forms.CharField(label='Equipo de Reemplazo', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    fecha_recepcion = forms.DateField(label='Fecha de Recepción', required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

class CambiarEstadoEquipamientoForm(forms.ModelForm):
    class Meta:
        model = Equipamiento
        fields = ['estado']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'})
        }
