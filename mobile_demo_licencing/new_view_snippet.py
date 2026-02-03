
from pyexpat.errors import messages
from django.shortcuts import get_object_or_404
from flask import redirect

from MobileApp.models import ActiveDevice


def delete_demo_device(request, pk):
    device = get_object_or_404(ActiveDevice, pk=pk)
    device.delete()
    messages.success(request, "Device removed successfully")
    return redirect("DemoLicensing:demo_list")
