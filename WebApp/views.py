from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import ActiveDevice, WebProject, WebControl, LoginLog
from StoreShop.models import Shop
from django.shortcuts import render
from .models import WebProject

def web_home(request):
    """Display list of all web projects"""
    projects = WebProject.objects.all()

    # build_absolute_uri('/') returns e.g. "http://127.0.0.1:8000/"
    # strip trailing slash so later joins are consistent
    base_url = request.build_absolute_uri('/')[:-1]

    context = {
        'projects': projects,
        'base_url': base_url,
    }
    return render(request, "webapp_list.html", context)


def webproject_create(request):
    """Create a new web project"""
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
    """Edit an existing web project"""
    project = get_object_or_404(WebProject, pk=pk)
    
    if request.method == 'POST':
        project_name = request.POST.get('project_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if project_name:
            project.project_name = project_name
            project.description = description if description else None
            project.save()  # API endpoint will auto-update
            messages.success(request, 'Web project updated successfully!')
            return redirect('WebApp:webapp_list')
        else:
            messages.error(request, 'Project name is required!')
    
    context = {'project': project}
    return render(request, "webproject_edit.html", context)

def webproject_delete(request, pk):
    """Delete a web project"""
    project = get_object_or_404(WebProject, pk=pk)
    project_name = project.project_name
    project.delete()
    messages.success(request, f'Web project "{project_name}" deleted successfully!')
    return redirect('WebApp:webapp_list')


# WEB CONTROL VIEWS
def web_control_list(request):
    """Shows table of WebControl entries"""
    controls = WebControl.objects.select_related('project').all()
    context = {'controls': controls}
    return render(request, "web_control.html", context)

def add_web_control(request):
    """Add Web Control"""
    projects = WebProject.objects.all()
    shops = Shop.objects.all()

    if request.method == 'POST':
        project_id = request.POST.get('project')
        shop_id = request.POST.get('shop')
        login_limit = request.POST.get('login_limit', '1').strip()

        if not project_id or not shop_id:
            messages.error(request, 'Project and Shop are required.')
            return render(request, "add_web_control.html", {'projects': projects, 'shops': shops})

        project = get_object_or_404(WebProject, pk=project_id)
        shop = get_object_or_404(Shop, pk=shop_id)

        try:
            login_limit_val = int(login_limit)
            if login_limit_val < 0:
                raise ValueError()
        except ValueError:
            messages.error(request, 'Login limit must be a non-negative integer.')
            return render(request, "add_web_control.html", {'projects': projects, 'shops': shops})

        WebControl.objects.create(
            project=project,
            customer_name=shop.name,
            client_id=shop.client_id,
            login_limit=login_limit_val
        )

        messages.success(request, 'Web control saved successfully!')
        return redirect('WebApp:web_control')

    return render(request, "add_web_control.html", {'projects': projects, 'shops': shops})


def edit_web_control(request, pk):
    """Edit Web Control"""
    control = get_object_or_404(WebControl, pk=pk)
    projects = WebProject.objects.all()
    shops = Shop.objects.all()

    if request.method == 'POST':
        project_id = request.POST.get('project')
        shop_id = request.POST.get('shop')
        login_limit = request.POST.get('login_limit', '1').strip()

        if not project_id or not shop_id:
            messages.error(request, 'Project and Shop are required.')
            return render(request, "edit_web_control.html", {'control': control, 'projects': projects, 'shops': shops})

        project = get_object_or_404(WebProject, pk=project_id)
        shop = get_object_or_404(Shop, pk=shop_id)

        try:
            login_limit_val = int(login_limit)
            if login_limit_val < 0:
                raise ValueError()
        except ValueError:
            messages.error(request, 'Login limit must be a non-negative integer.')
            return render(request, "edit_web_control.html", {'control': control, 'projects': projects, 'shops': shops})

        control.project = project
        control.customer_name = shop.name
        control.client_id = shop.client_id
        control.login_limit = login_limit_val
        control.save()

        messages.success(request, 'Web control updated successfully!')
        return redirect('WebApp:web_control')

    return render(request, "edit_web_control.html", {'control': control, 'projects': projects, 'shops': shops})


def delete_web_control(request, pk):
    """Delete web control"""
    control = get_object_or_404(WebControl, pk=pk)
    name = str(control)
    control.delete()
    messages.success(request, f'Web control "{name}" deleted.')
    return redirect('WebApp:web_control')


# ==================== API VIEWS ====================

# @require_http_methods(["GET"])
# def api_get_project_data(request, endpoint):
#     """
#     GET API: Returns all customers data for a project
#     Shows correct active device count
#     """
#     try:
#         project = WebProject.objects.get(api_endpoint=endpoint)
#         controls = WebControl.objects.filter(project=project)
        
#         customers_data = []
#         for control in controls:
#             # Count current active devices
#             active_count = control.active_devices.count()
            
#             customers_data.append({
#                 'customer_name': control.customer_name,
#                 'client_id': control.client_id,
#                 'login_limit': control.login_limit,
#                 'logged_count': active_count,  # ✅ Correct count now
#             })
        
#         response_data = {
#             'success': True,
#             'project_name': project.project_name,
#             'customers': customers_data
#         }
#         return JsonResponse(response_data, status=200)

#     except WebProject.DoesNotExist:
#         return JsonResponse({
#             'success': False,
#             'error': 'Project not found'
#         }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def api_post_login(request, endpoint):
    """
    POST API: Logs in a device if under limit
    Body: {"client_id": "xxx", "device_id": "yyy"}
    """
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id', '').strip()
        device_id = data.get('device_id', '').strip()

        if not client_id or not device_id:
            return JsonResponse({'success': False, 'error': 'client_id and device_id are required'}, status=400)

        project = WebProject.objects.get(api_endpoint=endpoint)
        control = WebControl.objects.get(project=project, client_id=client_id)

        # Count currently logged in devices
        active_count = ActiveDevice.objects.filter(control=control).count()
        if active_count >= control.login_limit:
            return JsonResponse({
                'success': False,
                'error': 'Login limit reached',
                'login_limit': control.login_limit,
                'active_devices': active_count
            }, status=403)

        # Check if already logged in
        if ActiveDevice.objects.filter(control=control, device_id=device_id).exists():
            return JsonResponse({'success': True, 'message': 'Already logged in'}, status=200)

        # Register new device
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        ActiveDevice.objects.create(control=control, device_id=device_id, ip_address=ip)

        return JsonResponse({
            'success': True,
            'message': 'Login successful',
            'device_id': device_id,
            'active_devices': ActiveDevice.objects.filter(control=control).count(),
            'login_limit': control.login_limit
        }, status=200)

    except WebProject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except WebControl.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Client ID not found for this project'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)







@csrf_exempt
@require_http_methods(["POST"])
def api_post_logout(request, endpoint):
    """
    POST API: Logs out a specific device
    Body: {"client_id": "xxx", "device_id": "yyy"}
    """
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id', '').strip()
        device_id = data.get('device_id', '').strip()

        if not client_id or not device_id:
            return JsonResponse({'success': False, 'error': 'client_id and device_id are required'}, status=400)

        project = WebProject.objects.get(api_endpoint=endpoint)
        control = WebControl.objects.get(project=project, client_id=client_id)

        deleted, _ = ActiveDevice.objects.filter(control=control, device_id=device_id).delete()
        if deleted:
            return JsonResponse({'success': True, 'message': 'Logged out successfully'}, status=200)
        else:
            return JsonResponse({'success': False, 'error': 'Device not found or already logged out'}, status=404)

    except WebProject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except WebControl.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Client ID not found for this project'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)




@require_http_methods(["GET"])
def api_get_project_data(request, endpoint):
    """
    GET API: Returns all customers with login data + active devices list
    """
    try:
        project = WebProject.objects.get(api_endpoint=endpoint)
        controls = WebControl.objects.filter(project=project)

        customers_data = []
        for control in controls:
            active_devices = list(control.active_devices.values(
                'device_id', 'ip_address', 'logged_in_at'
            ))

            customers_data.append({
                'customer_name': control.customer_name,
                'client_id': control.client_id,
                'login_limit': control.login_limit,
                'logged_count': len(active_devices),
                'active_devices': active_devices,
            })

        return JsonResponse({
            'success': True,
            'project_name': project.project_name,
            'customers': customers_data
        })

    except WebProject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
