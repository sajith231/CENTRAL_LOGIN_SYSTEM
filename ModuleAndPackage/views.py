from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from MobileApp.models import MobileProject
from .models import Module

def module_list(request):
    modules = Module.objects.select_related('project').all()
    return render(request, "module_list.html", {
        "modules": modules
    })

def add_module_page(request):
    projects = MobileProject.objects.all()
    return render(request, "add_module.html", {
        "projects": projects
    })

def add_module(request):
    if request.method == "POST":
        project_id = request.POST.get("project")
        module_name = request.POST.get("module_name")

        if not project_id or not module_name:
            messages.error(request, "All fields are required")
            return redirect("ModuleAndPackage:add_module_page")

        project = MobileProject.objects.get(id=project_id)

        Module.objects.create(
            project=project,
            module_name=module_name
        )

        messages.success(request, "Module added successfully")
        return redirect("ModuleAndPackage:module_list")

    return redirect("ModuleAndPackage:module_list")



def edit_module(request, pk):
    module = get_object_or_404(Module, pk=pk)

    if request.method == "POST":
        new_name = request.POST.get("module_name")
        if new_name:
            module.module_name = new_name
            module.save()
            messages.success(request, "Module updated successfully")
            return redirect("ModuleAndPackage:module_list")

    return render(request, "edit_module.html", {"module": module})


def delete_module(request, pk):
    module = get_object_or_404(Module, pk=pk)
    module.delete()
    messages.success(request, "Module deleted successfully")
    return redirect("ModuleAndPackage:module_list")
