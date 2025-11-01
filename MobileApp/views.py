from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import MobileProject

def mobile_home(request):
    """
    Display list of all mobile projects
    URL: /mobileapp/mobilelist/
    """
    projects = MobileProject.objects.all()
    return render(request, "mobileapp_list.html", {"projects": projects})

def mobileproject_create(request):
    """
    Create a new mobile project
    URL: /mobileapp/mobileproject/create/
    """
    if request.method == 'POST':
        project_name = request.POST.get('project_name', '').strip()
        description = request.POST.get('description', '').strip()

        if project_name:
            MobileProject.objects.create(
                project_name=project_name,
                description=description or None
            )
            messages.success(request, 'Mobile project created successfully!')
            return redirect('MobileApp:mobileapp_list')
        messages.error(request, 'Project name is required!')

    return render(request, "mobileproject_create.html")

def mobileproject_edit(request, pk):
    """
    Edit an existing mobile project
    URL: /mobileapp/mobileproject/edit/<id>/
    """
    project = get_object_or_404(MobileProject, pk=pk)

    if request.method == 'POST':
        project_name = request.POST.get('project_name', '').strip()
        description = request.POST.get('description', '').strip()

        if project_name:
            project.project_name = project_name
            project.description = description or None
            project.save()
            messages.success(request, 'Mobile project updated successfully!')
            return redirect('MobileApp:mobileapp_list')
        messages.error(request, 'Project name is required!')

    return render(request, "mobileproject_edit.html", {"project": project})

def mobileproject_delete(request, pk):
    """
    Delete a mobile project
    URL: /mobileapp/mobileproject/delete/<id>/
    """
    project = get_object_or_404(MobileProject, pk=pk)
    project_name = project.project_name
    project.delete()
    messages.success(request, f'Mobile project "{project_name}" deleted successfully!')
    return redirect('MobileApp:mobileapp_list')
