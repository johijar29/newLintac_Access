from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# CHOICES
class EstadoEquipamiento(models.TextChoices):
    ASIGNADO = 'AS', _('Asignado')
    EN_REPARACION = 'ER', _('En Reparación')
    DISPONIBLE = 'DI', _('Disponible')
    REEMPLAZO = 'RE', _('Reemplazo')
    DADO_DE_BAJA = 'DB', _('Dado de Baja')

class TipoEquipamiento(models.TextChoices):
    CHROMEBOOK = 'CB', _('Chromebook')
    NOTEBOOK = 'NB', _('Notebook')
    JABRA = 'JB', _('Jabra')
    WACOM = 'WC', _('Wacom')

class EstadoGeneral(models.TextChoices):
    ACTIVO = 'AC', _('Activo')
    INACTIVO = 'IN', _('Inactivo')
    LICENCIA = 'LI', _('Con Licencia')
    RETIRADO = 'RE', _('Retirado')

class Rol(models.TextChoices):
    PROFESOR = 'PR', _('Profesor')
    PRINCIPAL = 'PL', _('Principal')
    ASISTENTE = 'AS', _('Asistente')
    ENFERMERO = 'EN', _('Enfermero')
    PORTERO = 'PO', _('Portero')

# Modelo Curso
class Curso(models.Model):
    NOMBRES_CHOICES = [
        ('1-A', '1-A'), ('1-B', '1-B'), ('2-A', '2-A'), ('2-B', '2-B'),
        ('3-A', '3-A'), ('3-B', '3-B'), ('4-A', '4-A'), ('4-B', '4-B'),
        ('5-A', '5-A'), ('5-B', '5-B'), ('6-A', '6-A'), ('6-B', '6-B'),
        ('7-A', '7-A'), ('7-B', '7-B'), ('8-A', '8-A'), ('8-B', '8-B'),
        ('9-A', '9-A'), ('9-B', '9-B'), ('10-A', '10-A'), ('10-B', '10-B'),
        ('11-A', '11-A'), ('11-B', '11-B'), ('12-A', '12-A'), ('12-B', '12-B'),
    ]
    NIVELES_CHOICES = [
        ('1ro básico', '1ro básico'), ('2do básico', '2do básico'), 
        ('3ro básico', '3ro básico'), ('4to básico', '4to básico'),
        ('5to básico', '5to básico'), ('6to básico', '6to básico'),
        ('7mo básico', '7mo básico'), ('8vo básico', '8vo básico'),
        ('1ro medio', '1ro medio'), ('2do medio', '2do medio'),
        ('3ro medio', '3ro medio'), ('4to medio', '4to medio'),
    ]
    nombre = models.CharField(max_length=5, choices=NOMBRES_CHOICES)
    nivel = models.CharField(max_length=50, choices=NIVELES_CHOICES)

    def __str__(self):
        return f"{self.nombre} - {self.nivel}"

# Modelo Sede
class Sede(models.Model):
    CHICUREO = 'CH'
    LO_BARNECHEA = 'LB'
    CODIGOS_SEDE_CHOICES = [
        (CHICUREO, 'Chicureo'), (LO_BARNECHEA, 'Lo Barnechea'),
    ]
    codigo = models.CharField(max_length=2, unique=True, choices=CODIGOS_SEDE_CHOICES)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

# Modelo Ubicacion
class Ubicacion(models.Model):
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='ubicaciones')
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} en {self.sede.nombre}"

# Modelo Persona
class Persona(models.Model):
    rut = models.CharField(max_length=12, unique=True, null=True)
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    estado = models.CharField(max_length=20, choices=EstadoGeneral.choices)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.rut}"

class Alumno(Persona):
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True)

class Funcionario(Persona):
    rol = models.CharField(max_length=20, choices=Rol.choices)

# Modelo Equipamiento
class Equipamiento(models.Model):
    tipo = models.CharField(max_length=20, choices=TipoEquipamiento.choices)
    modelo = models.CharField(max_length=100)
    serie = models.CharField(max_length=50, unique=True)
    estado = models.CharField(max_length=20, choices=EstadoEquipamiento.choices)
    anio_adquisicion = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(timezone.now().year)])
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipamientos')
    equipo_reemplazo = models.CharField(max_length=100, blank=True, null=True)
    fecha_recepcion = models.DateField(blank=True, null=True)
    
    # Relación polimórfica con personas (puede ser nula)
    asignado_a_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    asignado_a_object_id = models.PositiveIntegerField(null=True)
    asignado_a = GenericForeignKey('asignado_a_content_type', 'asignado_a_object_id')

    def __str__(self):
        return self.serie

# Modelo RegistroActividad
class RegistroActividad(models.Model):
    equipamiento = models.ForeignKey(Equipamiento, on_delete=models.CASCADE, related_name='actividades')
    tipo_actividad = models.CharField(max_length=20, choices=EstadoEquipamiento.choices)
    fecha_hora = models.DateTimeField(default=timezone.now)
    descripcion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    fotos = models.ImageField(upload_to='fotos_incidentes/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_actividad_display()} - {self.equipamiento} el {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"
