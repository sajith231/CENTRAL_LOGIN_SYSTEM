from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .r2 import get_r2
import os

BUCKET = os.getenv("CLOUDFLARE_R2_BUCKET")

# ---------- UPLOAD PAGE ----------
def upload_page(request):
    r2 = get_r2()

    if request.method == "POST":
        folder = request.POST.get("folder").strip()
        files = request.FILES.getlist("files")

        if not folder:
            return JsonResponse({"error": "Folder name is required"}, status=400)

        if not files:
            return JsonResponse({"error": "No files selected"}, status=400)

        uploaded_count = 0
        for f in files:
            try:
                key = f"{folder}/{f.name}"
                r2.upload_fileobj(f, BUCKET, key)
                uploaded_count += 1
            except Exception as e:
                print(f"Error uploading {f.name}: {e}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": True,
                "message": f"{uploaded_count} file(s) uploaded successfully",
                "count": uploaded_count
            })
        
        return redirect("downloads:upload")

    # list folders with file details
    objects = r2.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    folders_data = {}
    
    for obj in objects:
        if "/" in obj["Key"]:
            folder_name = obj["Key"].split("/")[0]
            file_name = obj["Key"].split("/", 1)[1]  # Get filename after folder
            
            if folder_name not in folders_data:
                folders_data[folder_name] = {
                    "name": folder_name,
                    "file_count": 0,
                    "total_size": 0,
                    "files": []
                }
            folders_data[folder_name]["file_count"] += 1
            folders_data[folder_name]["total_size"] += obj.get("Size", 0)
            folders_data[folder_name]["files"].append({
                "name": file_name,
                "size": obj.get("Size", 0)
            })

    folders = sorted(folders_data.values(), key=lambda x: x["name"])

    return render(request, "upload.html", {"folders": folders})


def delete_folder(request, name):
    if request.method == "POST":
        r2 = get_r2()
        objs = r2.list_objects_v2(Bucket=BUCKET, Prefix=f"{name}/").get("Contents", [])

        deleted_count = 0
        for obj in objs:
            try:
                r2.delete_object(Bucket=BUCKET, Key=obj["Key"])
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {obj['Key']}: {e}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": True,
                "message": f"Folder '{name}' deleted successfully",
                "count": deleted_count
            })

    return redirect("downloads:upload")


# ---------- DOWNLOAD PAGE ----------
def download_page(request):
    r2 = get_r2()
    q = request.GET.get("q", "").lower()

    objects = r2.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    folders = {}

    for obj in objects:
        parts = obj["Key"].split("/")
        if len(parts) > 1:
            folder = parts[0]
            file = parts[1]
            if q and q not in folder.lower() and q not in file.lower():
                continue
            
            if folder not in folders:
                folders[folder] = []
            
            folders[folder].append({
                "name": file,
                "size": obj.get("Size", 0),
                "last_modified": obj.get("LastModified")
            })

    # Sort folders and files
    folders = dict(sorted(folders.items()))
    for folder in folders:
        folders[folder] = sorted(folders[folder], key=lambda x: x["name"])

    # Calculate total files
    total_files = sum(len(files) for files in folders.values())

    return render(request, "download.html", {"folders": folders, "q": q, "total_files": total_files})


def download_file(request, folder, filename):
    r2 = get_r2()
    key = f"{folder}/{filename}"
    
    try:
        obj = r2.get_object(Bucket=BUCKET, Key=key)
        response = HttpResponse(obj['Body'].read(), content_type=obj.get('ContentType', 'application/octet-stream'))
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        return HttpResponse(f"Error downloading file: {e}", status=404)