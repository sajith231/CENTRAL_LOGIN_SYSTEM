from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from MobileApp.models import MobileProject
from .models import Module
from django.http import JsonResponse

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




from .models import Module, Package
from MobileApp.models import MobileProject

def package_list(request):
    packages = Package.objects.all().prefetch_related("modules", "project")
    return render(request, "packages.html", {"packages": packages})


def add_package_page(request):
    projects = MobileProject.objects.all()
    return render(request, "add_packages.html", {"projects": projects})


def save_package(request):
    if request.method == "POST":
        project_id = request.POST.get("project")
        package_name = request.POST.get("package_name")
        days_limit = request.POST.get("days_limit", "0")
        selected_modules = request.POST.getlist("modules")

        project = MobileProject.objects.get(id=project_id)
        package = Package.objects.create(
            project=project, 
            package_name=package_name,
            days_limit=int(days_limit) if days_limit else 0
        )

        # Add multiple modules
        package.modules.set(selected_modules)
        package.save()

        return redirect("ModuleAndPackage:package_list")

    return redirect("ModuleAndPackage:package_list")


def edit_package(request, pk):
    package = get_object_or_404(Package, pk=pk)
    projects = MobileProject.objects.all()
    modules = Module.objects.filter(project=package.project)

    if request.method == "POST":
        package.package_name = request.POST.get("package_name")
        days_limit = request.POST.get("days_limit", "0")
        selected_modules = request.POST.getlist("modules")

        package.days_limit = int(days_limit) if days_limit else 0
        package.modules.set(selected_modules)
        package.save()

        return redirect("ModuleAndPackage:package_list")

    return render(request, "edit_package.html", {
        "package": package,
        "projects": projects,
        "modules": modules
    })


def delete_package(request, pk):
    package = get_object_or_404(Package, pk=pk)
    package.delete()
    return redirect("ModuleAndPackage:package_list")


def get_modules(request, project_id):
    modules = Module.objects.filter(project_id=project_id).values("id", "module_name")
    return JsonResponse(list(modules), safe=False)


def get_packages(request, project_id):
    packages = Package.objects.filter(project_id=project_id).values("id", "package_name")
    return JsonResponse(list(packages), safe=False)