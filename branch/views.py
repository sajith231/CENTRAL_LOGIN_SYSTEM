from django.shortcuts import render, redirect, get_object_or_404
from .models import Branch

def branch_list(request):
    branches = Branch.objects.all()
    return render(request, "branch_list.html", {"branches": branches})

def add_branch(request):
    if request.method == "POST":
        name = request.POST.get("name")
        place = request.POST.get("place")
        country = request.POST.get("country")

        Branch.objects.create(
            name=name,
            place=place,
            country=country
        )
        return redirect("branch_list")
    return render(request, "add_branch.html")

def edit_branch(request, id):
    branch = get_object_or_404(Branch, id=id)
    if request.method == "POST":
        branch.name = request.POST.get("name")
        branch.place = request.POST.get("place")
        branch.country = request.POST.get("country")
        branch.save()
        return redirect("branch_list")
    return render(request, "edit_branch.html", {"branch": branch})

def delete_branch(request, id):
    branch = get_object_or_404(Branch, id=id)
    branch.delete()
    return redirect("branch_list")
