from django.shortcuts import get_object_or_404, render, redirect
from django.db import transaction
from .models import Alumno, Equipamiento, Funcionario
from .forms import EquipamientoForm, EnviarServicioTecnicoForm, AsignarEquipamientoForm, CambiarEstadoEquipamientoForm
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import QueryDict
from django.db.models import Q
from urllib.parse import urlencode
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

def asignar_equipamiento(request, pk):
    equipamiento = get_object_or_404(Equipamiento, pk=pk)
    if request.method == 'POST':
        form = AsignarEquipamientoForm(request.POST)
        if form.is_valid():
            tipo_asignacion = form.cleaned_data['tipo_asignacion']
            id_asignacion = form.cleaned_data['id_asignacion']
            if tipo_asignacion == 'alumno':
                alumno = get_object_or_404(Alumno, pk=id_asignacion)
                equipamiento.asignado_a = alumno
            elif tipo_asignacion == 'funcionario':
                funcionario = get_object_or_404(Funcionario, pk=id_asignacion)
                equipamiento.asignado_a = funcionario
            equipamiento.save()
            messages.success(request, 'Equipamiento asignado con éxito.')
            return redirect('detalle_equipamiento', pk=pk)
    else:
        form = AsignarEquipamientoForm()
    return render(request, 'equipamiento/asignar_equipamiento.html', {'form': form, 'equipamiento': equipamiento})

def detalle_equipamiento(request, pk):
    equipamiento = get_object_or_404(Equipamiento, pk=pk)
    persona_asignada = None
    detalles_persona = {}

    if equipamiento.asignado_a_content_type and equipamiento.asignado_a_object_id:
        persona_model = equipamiento.asignado_a_content_type.model_class()
        persona_asignada = persona_model.objects.get(pk=equipamiento.asignado_a_object_id)

        if isinstance(persona_asignada, Alumno):
            detalles_persona = {
                'tipo': 'Alumno',
                'curso': persona_asignada.curso.nombre if persona_asignada.curso else 'N/A'
            }
        elif isinstance(persona_asignada, Funcionario):
            detalles_persona = {
                'tipo': 'Funcionario',
                'rol': persona_asignada.get_rol_display()
            }

    if request.method == 'POST':
        form = CambiarEstadoEquipamientoForm(request.POST, instance=equipamiento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estado del equipamiento actualizado con éxito.')
            return redirect('detalle_equipamiento', pk=pk)
    else:
        form = CambiarEstadoEquipamientoForm(instance=equipamiento)

    context = {
        'equipamiento': equipamiento,
        'persona_asignada': persona_asignada,
        'detalles_persona': detalles_persona,
        'form': form,
    }
    return render(request, 'equipamiento/detalle_equipamiento.html', context)

def servicio_tecnico(request):
    equipos_servicio_tecnico = Equipamiento.objects.filter(estado=EstadoEquipamiento.EN_REPARACION)
    return render(request, 'equipamiento/servicio_tecnico.html', {'equipos_servicio_tecnico': equipos_servicio_tecnico})

def enviar_servicio_tecnico(request, equipamiento_id):
    equipamiento = get_object_or_404(Equipamiento, pk=equipamiento_id)

    if request.method == 'POST':
        form = EnviarServicioTecnicoForm(request.POST)
        if form.is_valid():
            descripcion = form.cleaned_data['descripcion']
            tipo_problema = form.cleaned_data['tipo_problema']
            equipo_reemplazo = form.cleaned_data['equipo_reemplazo']
            fecha_recepcion = form.cleaned_data['fecha_recepcion']

            equipamiento.estado_anterior = equipamiento.estado
            equipamiento.estado = EstadoEquipamiento.EN_REPARACION
            equipamiento.equipo_reemplazo = equipo_reemplazo
            equipamiento.fecha_recepcion = fecha_recepcion
            equipamiento.save()

            messages.success(request, 'Equipamiento enviado a servicio técnico con éxito.')
            return redirect('detalle_equipamiento', pk=equipamiento.id)
    else:
        form = EnviarServicioTecnicoForm()

    return render(request, 'equipamiento/enviar_servicio_tecnico.html', {'form': form, 'equipamiento': equipamiento})

def agregar_equipamiento(request):
    if request.method == "POST":
        form = EquipamientoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipamiento agregado con éxito al inventario.")
            return redirect('listar_equipamientos')
    else:
        form = EquipamientoForm()
    return render(request, "equipamiento/agregar_equipamiento.html", {'form': form})

def listar_equipamientos(request):
    query = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    anio = request.GET.get('anio', '')
    tipo = request.GET.get('tipo', '')
    asignado_a = request.GET.get('asignado_a', '')

    equipamientos = Equipamiento.objects.all()

    if tipo:
        equipamientos = equipamientos.filter(tipo=tipo)
    if query:
        equipamientos = equipamientos.filter(Q(modelo__icontains=query) | Q(serie__icontains=query))
    if estado:
        equipamientos = equipamientos.filter(estado=estado)
    if anio:
        equipamientos = equipamientos.filter(anio_adquisicion=anio)
    if asignado_a:
        equipamientos = equipamientos.filter(
            Q(asignado_a_content_type__model=asignado_a) | Q(asignado_a=None)
        )

    total_equipamientos = equipamientos.count()

    paginator = Paginator(equipamientos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'equipamientos': page_obj,
        'query': query,
        'estado': estado,
        'anio': anio,
        'tipo': tipo,
        'asignado_a': asignado_a,
        'query_params': query_params.urlencode(),
        'total_equipamientos': total_equipamientos,
    }

    if tipo:
        clear_filters_url = reverse('listar_equipamientos') + f'?tipo={tipo}'
    else:
        clear_filters_url = reverse('listar_equipamientos')

    context['clear_filters_url'] = clear_filters_url

    return render(request, 'equipamiento/listar_equipamientos.html', context)

def editar_equipamiento(request, id):
    equipamiento = get_object_or_404(Equipamiento, pk=id)

    if request.method == "POST":
        form = EquipamientoForm(request.POST, instance=equipamiento)
        if form.is_valid():
            equipamiento_anterior = Equipamiento.objects.get(pk=id)
            equipamiento_anterior.pk = None
            equipamiento_anterior.save()
            form.save()
            messages.success(request, f"Equipamiento {equipamiento.modelo} actualizado con éxito.")
            return redirect('listar_equipamientos')
    else:
        form = EquipamientoForm(instance=equipamiento)

    return render(request, "equipamiento/editar_equipamiento.html", {'form': form, 'equipamiento': equipamiento})

@transaction.atomic
def eliminar_equipamiento(request, id):
    equipamiento = get_object_or_404(Equipamiento, pk=id)
    if request.method == "POST":
        equipamiento.delete()
        messages.success(request, f"Equipamiento {equipamiento.modelo} eliminado con éxito.")
        return redirect('listar_equipamientos')
    return render(request, "equipamiento/confirmar_eliminacion.html", {'equipamiento': equipamiento})

def home(request):
    return render(request, 'equipamiento/home.html')
