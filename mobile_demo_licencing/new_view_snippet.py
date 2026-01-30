
def delete_demo_device(request, pk):
    device = get_object_or_404(ActiveDevice, pk=pk)
    device.delete()
    messages.success(request, "Device removed successfully")
    return redirect("DemoLicensing:demo_list")
