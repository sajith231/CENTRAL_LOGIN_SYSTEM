from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from MobileApp.models import MobileControl
from ModuleAndPackage.models import Package
from .models import DemoMobileLicense
def demo_license_list(request):
    demos = DemoMobileLicense.objects.select_related(
        "original_license",
        "original_license__project"
    ).prefetch_related(
        "original_license__active_devices"
    )

    for d in demos:
        og = d.original_license

        if og:
            d.total_lic = og.login_limit
            d.reg_dev = og.active_devices.count()
            d.bal_lic = og.login_limit - d.reg_dev
            d.devices = og.active_devices.all()
        else:
            d.total_lic = d.demo_login_limit
            d.reg_dev = 0
            d.bal_lic = d.demo_login_limit
            d.devices = []   # no devices yet

    return render(request, "demo_mobile_licensing.html", {"demos": demos})




def add_mobile_demo_licencing(request):
    og_licenses = MobileControl.objects.all()

    if request.method == "POST":
        og_id = request.POST.get("og_license")
        demo_limit = request.POST.get("demo_login_limit", 1)

        og = get_object_or_404(MobileControl, id=og_id)
        demo_key = f"DEMO-{og.license_key}"

        if DemoMobileLicense.objects.filter(demo_license=demo_key).exists():
            messages.error(request, "Demo license already exists!")
            return redirect("DemoLicensing:demo_add")

        DemoMobileLicense.objects.create(
            original_license=og,
            demo_login_limit=demo_limit
        )

        messages.success(request, f"Demo License {demo_key} created")
        return redirect("DemoLicensing:demo_list")

    return render(request, "add_demo_license.html", {"og_licenses": og_licenses})


def edit_demo_license(request, pk):
    demo = get_object_or_404(DemoMobileLicense, pk=pk)

    if request.method == "POST":
        demo.demo_login_limit = request.POST.get("demo_login_limit")
        demo.status = True if request.POST.get("status") == "on" else False
        demo.save()
        messages.success(request, "Demo license updated")
        return redirect("DemoLicensing:demo_list")

    return render(request, "edit_demo_license.html", {"demo": demo})


def delete_demo_license(request, pk):
    demo = get_object_or_404(DemoMobileLicense, pk=pk)
    demo.delete()
    messages.success(request, "Demo license deleted")
    return redirect("DemoLicensing:demo_list")



from MobileApp.models import MobileProject
from ModuleAndPackage.models import Package

def add_manual_demo_license(request):
    projects = MobileProject.objects.all()

    if request.method == "POST":
        company = request.POST.get("company")
        project_id = request.POST.get("project")
        package_id = request.POST.get("package")
        demo_limit = request.POST.get("demo_login_limit", 1)

        project = get_object_or_404(MobileProject, id=project_id)
        package = get_object_or_404(Package, id=package_id)

        DemoMobileLicense.objects.create(
            company_name=company,
            project=project,
            package=package,
            demo_login_limit=demo_limit
        )

        messages.success(request, "Manual demo license created")
        return redirect("DemoLicensing:demo_list")

    return render(request, "add_manual_demo_license.html", {"projects": projects})




def get_packages(request, project_id):
    packages = Package.objects.filter(project_id=project_id).values("id", "package_name")
    return JsonResponse(list(packages), safe=False)