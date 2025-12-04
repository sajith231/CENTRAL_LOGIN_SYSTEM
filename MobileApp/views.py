from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import ActiveDevice, MobileProject, MobileControl, LoginLog
from StoreShop.models import Shop
from ModuleAndPackage.models import Package

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
    controls = MobileControl.objects.select_related('project', 'package').all()

    for control in controls:
        control.registered_count = control.active_devices.count()
        control.balance_count = control.login_limit - control.registered_count
        
        # Calculate remaining days and check expiration
        if control.package and control.package.days_limit > 0:
            days_limit = control.package.days_limit
            created_date = control.created_date
            expiry_date = created_date + timedelta(days=days_limit)
            now = timezone.now()
            
            # Calculate remaining days
            if expiry_date > now:
                remaining_days = (expiry_date - now).days
                control.remaining_days = remaining_days
                control.expiry_date = expiry_date
                control.is_expired = False
                
                # Auto-deactivate if expired
                if control.status and remaining_days <= 0:
                    control.status = False
                    control.save()
            else:
                control.remaining_days = 0
                control.expiry_date = expiry_date
                control.is_expired = True
                # Auto-deactivate if expired
                if control.status:
                    control.status = False
                    control.save()
        else:
            # Unlimited (days_limit = 0)
            control.remaining_days = None
            control.expiry_date = None
            control.is_expired = False

    context = {'controls': controls}
    return render(request, "mobile_control.html", context)


from StoreShop.models import Store

def add_mobile_control(request):
    projects = MobileProject.objects.all()
    shops = Shop.objects.all()
    stores = Store.objects.all()  # ➕ Store list added
    packages = Package.objects.all()

    if request.method == 'POST':
        project_id = request.POST.get('project')
        shop_id = request.POST.get('shop')
        store_id = request.POST.get('store')
        package_id = request.POST.get('package')
        login_limit = request.POST.get('login_limit', '1').strip()

        if not project_id or not shop_id or not store_id or not package_id:
            messages.error(request, 'All fields are required.')
            return redirect("MobileApp:add_mobile_control")

        project = get_object_or_404(MobileProject, pk=project_id)
        shop = get_object_or_404(Shop, pk=shop_id)
        store = get_object_or_404(Store, pk=store_id)
        package = get_object_or_404(Package, pk=package_id)

        MobileControl.objects.create(
            project=project,
            store=store,
            shop=shop,
            customer_name=shop.name,
            client_id=shop.client_id,
            login_limit=int(login_limit),
            package=package
        )

        messages.success(request, 'Mobile control saved successfully!')
        return redirect('MobileApp:mobile_control')

    return render(request, "add_mobile_control.html", {
        'projects': projects,
        'shops': shops,
        'stores': stores,  # ➕ send store list
        'packages': packages
    })



def edit_mobile_control(request, pk):
    control = get_object_or_404(MobileControl, pk=pk)
    projects = MobileProject.objects.all()
    shops = Shop.objects.all()
    stores = Store.objects.all()  # ➕ Store list
    packages = Package.objects.all()

    if request.method == 'POST':
        project = get_object_or_404(MobileProject, pk=request.POST.get('project'))
        shop = get_object_or_404(Shop, pk=request.POST.get('shop'))
        store = get_object_or_404(Store, pk=request.POST.get('store'))
        package = get_object_or_404(Package, pk=request.POST.get('package'))

        control.project = project
        control.shop = shop  # ➕ Save shop
        control.store = store  # ➕ Save store
        control.customer_name = shop.name
        control.client_id = shop.client_id
        control.package = package
        control.login_limit = int(request.POST.get('login_limit'))
        control.save()

        messages.success(request, 'Mobile control updated successfully!')
        return redirect('MobileApp:mobile_control')

    return render(request, "edit_mobile_control.html", {
        'control': control,
        'projects': projects,
        'shops': shops,
        'stores': stores,
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
            'ip_address',
            'logged_in_at',
        ).order_by('device_id')
    )


@csrf_exempt
@require_http_methods(["POST"])
def api_register_license(request, endpoint):
    """
    POST API: Registers a device against a license BEFORE login.
    Body: {"license_key": "ABC123", "device_id": "DEVICE-001"}
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    license_key = payload.get('license_key', '').strip()
    device_id = payload.get('device_id', '').strip()

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

    registered_count = control.active_devices.count()
    device_exists = control.active_devices.filter(device_id=device_id).exists()

    if device_exists:
        return JsonResponse({
            'success': True,
            'message': 'Device already registered',
            'license_key': license_key,
            'registered_devices': _device_payload(control),
            'registered_count': registered_count,
            'max_devices': control.login_limit,
        }, status=200)

    if registered_count >= control.login_limit:
        return JsonResponse({
            'success': False,
            'error': 'License limit reached',
            'max_devices': control.login_limit,
            'registered_count': registered_count
        }, status=403)

    ActiveDevice.objects.create(
        control=control,
        device_id=device_id,
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
        control = MobileControl.objects.get(project=project, license_key=license_key)
    except MobileProject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except MobileControl.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid license key for this project'}, status=404)
    
    # Check if the control is active (for logout, we allow even if inactive)
    # But it's good practice to check - you can remove this if you want logout to work always

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



@require_http_methods(["GET"])
def api_get_project_data(request, endpoint):
    """
    GET API: Returns all customers with login data + package + modules + active devices
    """
    try:
        project = MobileProject.objects.get(api_endpoint=endpoint)
        controls = MobileControl.objects.filter(project=project)

        customers_data = []
        for control in controls:
            registered_devices = _device_payload(control)

            customers_data.append({
                'customer_name': control.customer_name,
                'client_id': control.client_id,
                'license_key': control.license_key,
                'package': control.package.package_name if control.package else None,
                'modules': [
                    {
                        "module_name": m.module_name,
                        "module_code": m.module_code
                    } for m in control.package.modules.all()
                ] if control.package else [],
                'license_summary': {
                    'registered_count': len(registered_devices),
                    'max_devices': control.login_limit,
                },
                'registered_devices': registered_devices,
                'status': "Active" if control.status else "Inactive"  # ✔️ NEW STATUS FIELD
            })

        return JsonResponse({
            'success': True,
            'project_name': project.project_name,
            'customers': customers_data
        })

    except MobileProject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)


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



