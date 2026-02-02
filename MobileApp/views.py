from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from app1 import models
from .models import ActiveDevice, MobileProject, MobileControl, LoginLog
from StoreShop.models import Shop
from ModuleAndPackage.models import Package
from mobile_demo_licencing.models import DemoMobileLicense
from django.db.models import Q


def mobile_home(request):
    """Display list of all mobile projects"""
    projects = MobileProject.objects.all()

    # build_absolute_uri('/') returns e.g. "http://127.0.0.1:8000/"
    # strip trailing slash so later joins are consistent
    base_url = request.build_absolute_uri('/')[:-1]

    context = {
        'projects': projects,
        'base_url': base_url,
    }
    return render(request, "mobileapp_list.html", context)


def mobileproject_create(request):
    """Create a new mobile project"""
    if request.method == 'POST':
        project_name = request.POST.get('project_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if project_name:
            MobileProject.objects.create(
                project_name=project_name,
                description=description if description else None
            )
            messages.success(request, 'Mobile project created successfully!')
            return redirect('MobileApp:mobileapp_list')
        else:
            messages.error(request, 'Project name is required!')
    
    return render(request, "mobileproject_create.html")

def mobileproject_edit(request, pk):
    """Edit an existing mobile project"""
    project = get_object_or_404(MobileProject, pk=pk)
    
    if request.method == 'POST':
        project_name = request.POST.get('project_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if project_name:
            project.project_name = project_name
            project.description = description if description else None
            project.save()  # API endpoint will auto-update
            messages.success(request, 'Mobile project updated successfully!')
            return redirect('MobileApp:mobileapp_list')
        else:
            messages.error(request, 'Project name is required!')
    
    context = {'project': project}
    return render(request, "mobileproject_edit.html", context)

def mobileproject_delete(request, pk):
    """Delete a mobile project"""
    project = get_object_or_404(MobileProject, pk=pk)
    project_name = project.project_name
    project.delete()
    messages.success(request, f'Mobile project "{project_name}" deleted successfully!')
    return redirect('MobileApp:mobileapp_list')


# MOBILE CONTROL VIEWS
from django.utils import timezone
from datetime import timedelta

def mobile_control_list(request):
    """Shows table of MobileControl entries"""
    controls = (
        MobileControl.objects
        .select_related('project', 'package')
        .prefetch_related('active_devices')
        .order_by('-updated_date')   # ✅ SORT BY LATEST UPDATE
    )


    now = timezone.now()

    for control in controls:
        # -------- DEVICE COUNTS --------
        control.registered_count = control.active_devices.count()
        control.balance_count = control.login_limit - control.registered_count

        # -------- EXPIRY / REMAINING DAYS --------
        if control.expiry_date:
            delta = control.expiry_date - now
            control.remaining_days = delta.days
            control.is_expired = delta.total_seconds() <= 0

            # Auto deactivate when expired
            if control.is_expired and control.status:
                control.status = False
                control.save(update_fields=["status"])
        else:
            # Unlimited license
            control.remaining_days = None
            control.is_expired = False

    context = {
        "controls": controls
    }
    return render(request, "mobile_control.html", context)


from StoreShop.models import Store
from branch.models import Branch   # ➕ Import Branch model
from StoreShop.models import Store
from branch.models import Branch  # 👈 add this

def add_mobile_control(request):
    projects = MobileProject.objects.all()
    shops = Shop.objects.all()
    stores = Store.objects.all()
    branches = Branch.objects.all()   # 👈 all branches
    packages = Package.objects.all()

    if request.method == 'POST':
        project_id = request.POST.get('project')
        shop_id = request.POST.get('shop')
        store_id = request.POST.get('store')
        package_id = request.POST.get('package')
        login_limit = request.POST.get('login_limit', '0').strip()

        if not project_id or not shop_id or not store_id or not package_id:
            messages.error(request, 'All fields are required.')
            return redirect("MobileApp:add_mobile_control")

        project = get_object_or_404(MobileProject, pk=project_id)
        shop = get_object_or_404(Shop, pk=shop_id)
        store = get_object_or_404(Store, pk=store_id)
        package = get_object_or_404(Package, pk=package_id)

        # Calculate expiry date if package has a limit
        expiry_date = None
        if package.days_limit > 0:
            expiry_date = timezone.now() + timedelta(days=package.days_limit)

        MobileControl.objects.create(
            project=project,
            store=store,
            shop=shop,
            customer_name=shop.name,
            client_id=shop.client_id,
            login_limit=int(login_limit),
            package=package,
            expiry_date=expiry_date
        )

        messages.success(request, 'Mobile control saved successfully!')
        return redirect('MobileApp:mobile_control')

    return render(request, "add_mobile_control.html", {
        'projects': projects,
        'shops': shops,
        'stores': stores,
        'branches': branches,   # 👈 pass branches
        'packages': packages
    })


def edit_mobile_control(request, pk):
    control = get_object_or_404(MobileControl, pk=pk)
    projects = MobileProject.objects.all()
    shops = Shop.objects.all()
    stores = Store.objects.all()
    branches = Branch.objects.all()   # 👈 pass branches here too
    packages = Package.objects.all()

    if request.method == 'POST':
        project = get_object_or_404(MobileProject, pk=request.POST.get('project'))
        shop = get_object_or_404(Shop, pk=request.POST.get('shop'))
        store = get_object_or_404(Store, pk=request.POST.get('store'))
        package = get_object_or_404(Package, pk=request.POST.get('package'))

        control.project = project
        control.shop = shop
        control.store = store
        control.customer_name = shop.name
        control.client_id = shop.client_id
        control.package = package
        
        login_limit = request.POST.get('login_limit', '0').strip()
        control.login_limit = int(login_limit)
        
        control.save()

        messages.success(request, 'Mobile control updated successfully!')
        return redirect('MobileApp:mobile_control')

    return render(request, "edit_mobile_control.html", {
        'control': control,
        'projects': projects,
        'shops': shops,
        'stores': stores,
        'branches': branches,   # 👈 here
        'packages': packages
    })





def delete_mobile_control(request, pk):
    """Delete mobile control"""
    control = get_object_or_404(MobileControl, pk=pk)
    name = str(control)
    control.delete()
    messages.success(request, f'Mobile control "{name}" deleted.')
    return redirect('MobileApp:mobile_control')





# ==================== API VIEWS ====================

def _get_client_ip(request):
    """Resolve client IP irrespective of reverse proxies."""
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _device_payload(control):
    """Reusable formatter for registered devices."""
    return list(
        control.active_devices.values(
            'device_id',
            'device_name',  # 👈 Added
            'ip_address',
            'logged_in_at',
        ).order_by('-logged_in_at')
    )

@csrf_exempt
@require_http_methods(["POST"])
def api_register_license(request, endpoint):
    """
    POST API: Registers a device against a license BEFORE login.
    Body: {
        "license_key": "ABC123",
        "device_id": "DEVICE-001",
        "device_name": "Samsung A52"
    }
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    license_key = payload.get('license_key', '').strip()
    device_id = payload.get('device_id', '').strip()
    device_name = payload.get('device_name', '').strip()

    # REQUIRED VALIDATION
    if not license_key:
        return JsonResponse({'success': False, 'error': 'license_key is required'}, status=400)

    if not device_id:
        return JsonResponse({'success': False, 'error': 'device_id is required'}, status=400)

    if not device_name:
        return JsonResponse({'success': False, 'error': 'device_name is required'}, status=400)

    try:
        project = MobileProject.objects.get(api_endpoint=endpoint)
    except MobileProject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)

    # 🔹 1) Try ORIGINAL license
    control = MobileControl.objects.filter(
        project=project,
        license_key=license_key
    ).first()

    # 🔹 2) If not found, try DEMO license
    demo = None
    if not control:
        demo = DemoMobileLicense.objects.filter(
            demo_license=license_key,
            status=True
        ).filter(
            Q(project=project) |
            Q(original_license__project=project)
        ).first()

    if not control and not demo:
        return JsonResponse({'success': False, 'error': 'Invalid license key for this project'}, status=404)

    # ================= OG LICENSE FLOW =================
    if control:
        # License expiry rule
        if control.package and control.package.days_limit > 0:
            days_limit = control.package.days_limit
            created_date = control.created_date
            expiry_date = created_date + timedelta(days=days_limit)
            now = timezone.now()

            if expiry_date <= now:
                if control.status:
                    control.status = False
                    control.save()
                return JsonResponse({
                    'success': False,
                    'error': 'This license has expired. Please contact administrator.'
                }, status=403)

        if not control.status:
            return JsonResponse({
                'success': False,
                'error': 'This license is inactive. Please contact administrator.'
            }, status=403)

        registered_count = control.active_devices.count()

        # Already registered device
        exists = control.active_devices.filter(device_id=device_id).exists()
        if exists:
            return JsonResponse({
                'success': True,
                'message': 'Device already registered',
                'license_key': license_key,
                'registered_devices': _device_payload(control),
                'registered_count': registered_count,
                'max_devices': control.login_limit,
            }, status=200)

        # Device limit check
        if registered_count >= control.login_limit:
            return JsonResponse({
                'success': False,
                'error': 'License limit reached',
                'max_devices': control.login_limit,
                'registered_count': registered_count
            }, status=403)

        # Create new active device
        ActiveDevice.objects.create(
            control=control,
            device_id=device_id,
            device_name=device_name,
            ip_address=_get_client_ip(request),
        )

        return JsonResponse({
            'success': True,
            'message': 'Device registered successfully',
            'license_key': license_key,
            'registered_devices': _device_payload(control),
            'registered_count': control.active_devices.count(),
            'max_devices': control.login_limit,
        }, status=201)

    # ================= DEMO LICENSE FLOW =================
    if demo:
        now = timezone.now()

        # Expiry check
        if demo.expires_at and demo.expires_at < now:
            demo.status = False
            demo.save(update_fields=["status"])
            return JsonResponse({
                'success': False,
                'error': 'Demo license expired'
            }, status=403)

        reg_count = demo.active_devices.count()

        # Already registered
        exists = demo.active_devices.filter(device_id=device_id).exists()
        if exists:
            return JsonResponse({
                'success': True,
                'message': 'Device already registered',
                'license_key': license_key,
                'registered_devices': list(demo.active_devices.values()),
                'registered_count': reg_count,
                'max_devices': demo.demo_login_limit,
            }, status=200)

        # Limit check
        limit = int(demo.demo_login_limit)
        if reg_count >= limit:
            return JsonResponse({
                'success': False,
                'error': f'Demo limit reached ({reg_count}/{limit})',
                'max_devices': limit,
                'registered_count': reg_count
            }, status=403)

        ActiveDevice.objects.create(
            demo_license=demo,
            device_id=device_id,
            device_name=device_name,
            ip_address=_get_client_ip(request),
        )

        return JsonResponse({
            'success': True,
            'message': 'Demo device registered',
            'license_key': license_key,
            'registered_devices': list(demo.active_devices.values()),
            'registered_count': demo.active_devices.count(),
            'max_devices': demo.demo_login_limit,
        }, status=201)




@csrf_exempt
@require_http_methods(["POST"])
def api_post_login(request, endpoint):
    """
    POST API: Logs in a device after it has been registered.
    Body: {"license_key": "ABC123", "device_id": "DEVICE-001"}
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    license_key = data.get('license_key', '').strip()
    device_id = data.get('device_id', '').strip()

    if not license_key or not device_id:
        return JsonResponse({
            'success': False,
            'error': 'license_key and device_id are required'
        }, status=400)

    try:
        project = MobileProject.objects.get(api_endpoint=endpoint)
        control = MobileControl.objects.get(project=project, license_key=license_key)
    except MobileProject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except MobileControl.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid license key for this project'}, status=404)
    
    # Check if expired based on package days_limit
    if control.package and control.package.days_limit > 0:
        days_limit = control.package.days_limit
        created_date = control.created_date
        expiry_date = created_date + timedelta(days=days_limit)
        now = timezone.now()
        
        if expiry_date <= now:
            # Auto-deactivate if expired
            if control.status:
                control.status = False
                control.save()
            return JsonResponse({
                'success': False,
                'error': 'This license has expired. Please contact administrator.'
            }, status=403)
    
    # Check if the control is active
    if not control.status:
        return JsonResponse({
            'success': False,
            'error': 'This license is inactive. Please contact administrator.'
        }, status=403)

    is_registered = control.active_devices.filter(device_id=device_id).exists()
    if not is_registered:
        return JsonResponse({
            'success': False,
            'error': 'Device is not registered for this license',
            'license_key': license_key
        }, status=403)

    LoginLog.objects.create(
        control=control,
        client_id=device_id,
        ip_address=_get_client_ip(request)
    )

    return JsonResponse({
        'success': True,
        'message': 'Login successful',
        'license_key': license_key,
        'device_id': device_id
    }, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def api_post_logout(request, endpoint):
    """
    POST API: Unregisters a specific device from a license key.
    Body: {"license_key": "ABC123", "device_id": "DEVICE-001"}
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    license_key = data.get('license_key', '').strip()
    device_id = data.get('device_id', '').strip()

    if not license_key or not device_id:
        return JsonResponse({
            'success': False,
            'error': 'license_key and device_id are required'
        }, status=400)

    try:
        project = MobileProject.objects.get(api_endpoint=endpoint)
    except MobileProject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)

    # 🔹 Try OG license first
    control = MobileControl.objects.filter(
        project=project,
        license_key=license_key
    ).first()

    # 🔹 If not found, try DEMO license
    demo = None
    if not control:
        demo = DemoMobileLicense.objects.filter(
            demo_license=license_key
        ).filter(
            Q(project=project) |
            Q(original_license__project=project)
        ).first()

    if not control and not demo:
        return JsonResponse({
            'success': False,
            'error': 'Invalid license key for this project'
        }, status=404)

    # ================= OG LICENSE LOGOUT =================
    if control:
        deleted, _ = control.active_devices.filter(device_id=device_id).delete()
        if deleted:
            remaining = _device_payload(control)
            return JsonResponse({
                'success': True,
                'message': 'Device removed from license',
                'license_key': license_key,
                'registered_devices': remaining,
                'registered_count': len(remaining),
                'max_devices': control.login_limit,
            }, status=200)

        return JsonResponse({
            'success': False,
            'error': 'Device not found for this license'
        }, status=404)

    # ================= DEMO LICENSE LOGOUT =================
    if demo:
        deleted, _ = demo.active_devices.filter(device_id=device_id).delete()
        if deleted:
            remaining = list(demo.active_devices.values())
            return JsonResponse({
                'success': True,
                'message': 'Demo device removed',
                'license_key': license_key,
                'registered_devices': remaining,
                'registered_count': len(remaining),
                'max_devices': demo.demo_login_limit,
            }, status=200)

        return JsonResponse({
            'success': False,
            'error': 'Device not found for this demo license'
        }, status=404)


from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

@require_http_methods(["GET"])
def api_get_project_data(request, endpoint):
    try:
        project = MobileProject.objects.get(api_endpoint=endpoint)
        controls = MobileControl.objects.filter(project=project)

        now = timezone.now()

        # 🔹 get customer filter (optional)
        customer = request.GET.get("customer")

        # 🔹 Demo licenses for this project (OG + Manual)
        demo_licenses = DemoMobileLicense.objects.filter(
            Q(project=project) |
            Q(original_license__project=project)
        )

        # 🔹 FILTER BY COMPANY if provided
        if customer:
            demo_licenses = demo_licenses.filter(
                Q(company_name__iexact=customer) |
                Q(original_license__customer_name__iexact=customer)
            )

        demo_keys = []
        for d in demo_licenses:
            # auto expire after 5 days
            if d.expires_at and d.expires_at < now and d.status:
                d.status = False
                d.save(update_fields=["status"])

            demo_keys.append({
                "company": d.original_license.customer_name if d.original_license else d.company_name,
                "demo_license": d.demo_license,
                "demo_login_limit": d.demo_login_limit,
                "status": "Active" if d.status else "Inactive",
                "created_at": d.created_at.date().isoformat(),
                "expires_at": d.expires_at.date().isoformat() if d.expires_at else None
            })

        customers_data = []

        for control in controls:
            registered_devices = _device_payload(control)
            registered_count = len(registered_devices)

            expiry_date = control.expiry_date
            remaining_days = None
            is_expired = False

            if expiry_date:
                delta = expiry_date - now
                remaining_days = delta.days
                is_expired = delta.total_seconds() <= 0

                if is_expired and control.status:
                    control.status = False
                    control.save(update_fields=["status"])

            customers_data.append({
                "customer_name": control.customer_name,
                "client_id": control.client_id,
                "license_key": control.license_key,

                "package": control.package.package_name if control.package else None,

                "modules": [
                    {
                        "module_name": m.module_name,
                        "module_code": m.module_code
                    }
                    for m in control.package.modules.all()
                ] if control.package else [],

                "license_summary": {
                    "registered_devices": registered_count,
                    "max_devices": control.login_limit,
                },

                "license_validity": {
                    "expiry_date": expiry_date.date().isoformat() if expiry_date else None,
                    "remaining_days": remaining_days,
                    "is_expired": is_expired,
                },

                "registered_devices": registered_devices,
                "status": "Active" if control.status else "Inactive",
            })

        return JsonResponse({
            "success": True,
            "project_name": project.project_name,
            "demo_licenses": demo_keys,
            "customers": customers_data
        })

    except MobileProject.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Project not found"
        }, status=404)




# h

@csrf_exempt
@require_http_methods(["POST"])
def toggle_mobile_control_status(request, pk):
    """
    Toggle Active/Inactive status WITHOUT deleting existing registered devices
    """
    try:
        control = get_object_or_404(MobileControl, pk=pk)

        # Toggle current status
        control.status = not control.status
        control.save()

        return JsonResponse({
            'success': True,
            'status': control.status,
            'message': f'Status changed to {"Active" if control.status else "Inactive"}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# http://127.0.0.1:8000/mobileapp/api/project/project1/license/register/
# http://127.0.0.1:8000/mobileapp/api/project/project1/logout/



# {
#   "license_key": "2LQ45VS8KM",
#   "device_id": "DEVICE-002"
# }



@csrf_exempt
@require_http_methods(["POST"])
def toggle_bill_status(request, pk):
    try:
        control = get_object_or_404(MobileControl, pk=pk)
        control.bill_status = not control.bill_status
        control.save()

        return JsonResponse({
            'success': True,
            'status': control.bill_status,
            'message': "Billed" if control.bill_status else "Unbilled"
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import MobileControl, MobileBillingHistory

def mobile_control_billing(request, pk):
    control = get_object_or_404(MobileControl, pk=pk)

    # ---------- CURRENT EXPIRY ----------
    expiry_date = control.expiry_date

    # Check for unbilled history
    has_unbilled_history = control.billing_history.filter(bill_status=False).exists()

    if request.method == "POST":
        if has_unbilled_history:
            messages.error(
                request,
                "Cannot update billing with outstanding unbilled items. Please clear pending bills first."
            )
            return redirect("MobileApp:mobile_control_billing", pk=pk)

        # ---------- INPUTS ----------
        extend_login = int(request.POST.get("extend_login") or 0)
        bill_status = request.POST.get("bill_status") in ["1", "on", "true"]
        remark = request.POST.get("remark", "").strip()

        # ---------- STORE OLD VALUES ----------
        old_login_limit = control.login_limit
        old_expiry = control.expiry_date

        # ---------- EXTEND DAYS LOGIC ----------
        package_id = request.POST.get("package")

        if package_id:
            package = get_object_or_404(Package, pk=package_id)
            extend_days = package.days_limit
            control.package = package
        else:
            extend_days = int(request.POST.get("extend_days") or 0)

        # ---------- LOGIN LIMIT (+ / -) ----------
        if extend_login != 0:
            new_login_limit = control.login_limit + extend_login
            if new_login_limit < 1:
                messages.error(request, "Login limit cannot be less than 1")
                return redirect("MobileApp:mobile_control_billing", pk=pk)
            control.login_limit = new_login_limit

        # ---------- EXPIRY DATE (+ / -) ----------
        if extend_days != 0:
            if control.expiry_date:
                new_expiry = control.expiry_date + timedelta(days=extend_days)
            else:
                new_expiry = timezone.now() + timedelta(days=extend_days)

            if new_expiry < timezone.now():
                messages.error(request, "Expiry date cannot be in the past")
                return redirect("MobileApp:mobile_control_billing", pk=pk)

            control.expiry_date = new_expiry

        # ---------- SAVE BILLING HISTORY ----------
        MobileBillingHistory.objects.create(
            control=control,
            extended_days=extend_days,
            extended_login_limit=extend_login,
            old_expiry_date=old_expiry,
            new_expiry_date=control.expiry_date,
            old_login_limit=old_login_limit,
            new_login_limit=control.login_limit,
            bill_status=bill_status,
            remark=remark
        )

        # ---------- RE-CALCULATE BILL STATUS ----------
        has_unbilled = control.billing_history.filter(bill_status=False).exists()
        control.bill_status = not has_unbilled

        # ✅ IMPORTANT: FULL SAVE (updates updated_date correctly)
        control.save()

        messages.success(request, "Billing updated successfully")
        return redirect("MobileApp:mobile_control_billing", pk=pk)

    # ---------- HISTORY ----------
    history = control.billing_history.all().order_by("-created_at")

    # ---------- PACKAGES ----------
    packages = Package.objects.filter(project=control.project)

    return render(request, "mobileapp_billing.html", {
        "control": control,
        "expiry_date": expiry_date,
        "history": history,
        "packages": packages,
        "has_unbilled_history": has_unbilled_history
    })

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import MobileBillingHistory

@csrf_exempt
@require_POST
def toggle_billing_history_status(request, pk):
    try:
        history = MobileBillingHistory.objects.get(pk=pk)
        history.bill_status = not history.bill_status
        history.save()

        # Update Parent Control Status
        control = history.control
        has_unbilled = control.billing_history.filter(bill_status=False).exists()
        control.bill_status = not has_unbilled
        control.save()

        return JsonResponse({
            "success": True,
            "status": history.bill_status
        })
    except MobileBillingHistory.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Record not found"
        }, status=404)
