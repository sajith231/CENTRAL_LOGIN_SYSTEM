from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import WebProject

def web_home(request):
    """
    Display list of all web projects
    URL: /weblist/
    """
    projects = WebProject.objects.all()
    context = {
        'projects': projects
    }
    return render(request, "webapp_list.html", context)

def webproject_create(request):
    """
    Create a new web project
    URL: /webproject/create/
    Methods: GET (show form), POST (save data)
    """
    if request.method == 'POST':
        project_name = request.POST.get('project_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if project_name:
            WebProject.objects.create(
                project_name=project_name,
                description=description if description else None
            )
            messages.success(request, 'Web project created successfully!')
            return redirect('WebApp:webapp_list')
        else:
            messages.error(request, 'Project name is required!')
    
    return render(request, "webproject_create.html")

def webproject_edit(request, pk):
    """
    Edit an existing web project
    URL: /webproject/edit/<id>/
    Methods: GET (show form), POST (update data)
    """
    project = get_object_or_404(WebProject, pk=pk)
    
    if request.method == 'POST':
        project_name = request.POST.get('project_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if project_name:
            project.project_name = project_name
            project.description = description if description else None
            project.save()
            messages.success(request, 'Web project updated successfully!')
            return redirect('WebApp:webapp_list')
        else:
            messages.error(request, 'Project name is required!')
    
    context = {
        'project': project
    }
    return render(request, "webproject_edit.html", context)

def webproject_delete(request, pk):
    """
    Delete a web project
    URL: /webproject/delete/<id>/
    Method: GET (via confirmation modal link)
    """
    project = get_object_or_404(WebProject, pk=pk)
    project_name = project.project_name
    project.delete()
    messages.success(request, f'Web project "{project_name}" deleted successfully!')
    return redirect('WebApp:webapp_list')