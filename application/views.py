from os import stat
import re
from traceback import print_tb
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import *
import json
from django.contrib.auth import login, logout
import time
from django.db.models import Q
import re
import uuid
from django.contrib.auth import user_logged_in
from django.dispatch.dispatcher import receiver
from django.shortcuts import get_object_or_404


# Signals to add device in loggged in device
@receiver(user_logged_in)
def remove_other_sessions(sender, user, request, **kwargs):
    request.session.save()
    session_id = request.session.session_key
    new_device = Device(user=user, session_id=session_id)
    new_device.set_browser_info(request)
    is_exists = new_device.is_already_exists()
    if is_exists:
        new_device = is_exists
        new_device.session_id = session_id

    if new_device.is_limit_reached() and not is_exists:
        messages.error(request, "You have reached maximum Sessions limit!")
        print("Loging out")
        logout(request)
        return

    new_device.save()

    # remove other sessions
    print("-------------------")
    # return redirect("profile")
    # save current session
    print("-------------------")

    # create a link from the user to the current session (for later removal)
    # UserSession.objects.get_or_create(
    #     user=user,
    #     session_id=request.session.session_key
    # )


@login_required
def reset_password(request):
    if request.method == "POST":
        password_form = ResetPasswordForm(request.POST)
        if password_form.is_valid():
            password = password_form.cleaned_data["password"]
            print(password)
            user = request.user
            user.set_password(password)
            user.save()
            messages.success(
                request, "Password has been updated successfully!")
        else:
            messages.error(request, password_form.errors)

    return redirect("profile")


@login_required
def profile(request):
    user_form = UserForm(instance=request.user)
    password_form = ResetPasswordForm()

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        if not user_form.is_valid():
            print(user_form.errors)

        user = User.objects.get(id=request.user.id)
        user.first_name = (
            request.POST.get("first_name")
            if request.POST.get("first_name")
            else user.first_name
        )
        user.last_name = (
            request.POST.get("last_name")
            if request.POST.get("last_name")
            else user.last_name
        )
        user.username = (
            request.POST.get("email") if request.POST.get(
                "email") else user.username
        )
        user.email = (
            request.POST.get("email") if request.POST.get(
                "email") else user.email
        )
        user.save()
        user_form = UserForm(instance=user)
        messages.success(request, "Profile has been updated")
        return redirect("profile")

    device_sessions = Device.objects.filter(user=request.user)
    all_trainings = Access.objects.filter(user=request.user)
    context = {
        "all_trainings": all_trainings,
        "user_form": user_form,
        "page": "profile",
        "device_sessions": device_sessions,
        "password_form": password_form,
        "accessed_training": get_accessed_training(request.user)
    }
    return render(request, "profile.html", context)


@login_required
def index(request):
    return redirect("trainings")
    all_folders = Folder.objects.filter(user=request.user)[0:3]
    all_bookmarks = Bookmark.objects.filter(user=request.user)[0:3]
    all_terms = Term.objects.filter(user=request.user)[0:3]
    context = {
        'page': 'dashboard',
        'all_folders': all_folders,
        'all_bookmarks': all_bookmarks,
        'all_terms': all_terms
    }
    return render(request, 'index.html', context)


def signup(request):
    if request.user.is_authenticated:
        return redirect("index")

    user_form = UserForm()
    if request.method == "POST":
        user_form = UserForm(request.POST)
        if user_form.is_valid():
            new_user = User.objects.create_user(**user_form.cleaned_data)
            messages.success(request, "You have beem registered successfully!")

            folder_names = ["Term Papers", "Quizzes", "Project"]
            for folder in folder_names:
                new_folder = Folder(name=folder, user=new_user)
                new_folder.save()
            return redirect("signin")

    context = {'user_form': user_form}
    return render(request, "signup.html", context)


# function for login

def signin(request):
    if request.user.is_authenticated:
        return redirect("index")

    login_form = LoginForm()
    if request.method == "POST":
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user = login_form.cleaned_data
            # print(user)
            print("============= LOGIN IN START ===============")
            login(request, user)
            print("============= LOGIN IN END ===============")
            return redirect("trainings")

            # if new_device.is_already_exists():
            #     login(request, login_form.cleaned_data)
            #     return redirect("index")
            # else:
            #     if new_device.is_limit_reached():
            #         messages.error(request, 'Max Account Limit Reached!!')
            #         return redirect("index")
            #     else:
            #         new_device.save()
            #         login(request, login_form.cleaned_data)
            #         return redirect("index")

    return render(request, "login.html", {'login_form': login_form})


# function for logout
def signout(request):
    logout(request)
    return redirect("signin")


# Function for checking the browser, IP-address, and device info of the user
def get_browser_info(request):

    # status of mobile, pc or tablet
    is_mobile = request.user_agent.is_mobile
    is_tablet = request.user_agent.is_tablet
    is_pc = request.user_agent.is_pc

    # fetching the browser info
    browser_family = request.user_agent.browser.family
    browser_version = request.user_agent.browser.version

    # fetching the os info
    os_family = request.user_agent.os.family
    os_version = request.user_agent.os.version

    # fetching the device info
    device_name = request.user_agent.device.family
    ip = get_client_ip(request)

    test = ':'.join(re.findall('..', '%012x' % uuid.getnode()))

    str = f'The {request.user.last_name} is on the Mobile: {is_mobile}\nThe {request.user.last_name} is on the Tablet: {is_tablet}\nThe {request.user.last_name} is on the PC: {is_pc}\nThe {request.user.last_name} Browser is: {browser_family}\nThe {request.user.last_name} Browser Version is: {browser_version}\nThe {request.user.last_name} OS is: {os_family}\nThe {request.user.last_name} OS Version is: {os_version}\nThe {request.user.last_name} Device is: {device_name}\n\n{test}'
    # print(test)
    # print(type(test))

    # joins elements of getnode() after each 2 digits.
    # using regex expression
    print("The MAC address in formatted and less complex way is : ", end="")
    print(':'.join(re.findall('..', '%012x' % uuid.getnode())))

    print(ip)
    return HttpResponse(str)


@login_required
def delete_user_device(request, device_id):
    # filtering if the device with the given id exists or not
    # device = Device.objects.filter(id=device_id)
    device = get_object_or_404(Device, pk=device_id)

    if device.user == request.user:
        device.delete()
        return HttpResponseRedirect(reverse('profile'))
    else:
        return HttpResponseRedirect(reverse('profile'))


def get_accessed_training(user):
    access = Access.objects.filter(
        user=user).values_list("training_id", flat=True)
    return access

# Function to Render the All Trainings Page


@login_required
def all_trainings(request):
    trainings = Training.objects.all()
    accessed_training = get_accessed_training(request.user)
    allowed = training = None
    expand_id = request.GET.get('expand')
    if expand_id:
        training = Training.objects.filter(id=expand_id).first()
        allowed = True if training and training.id in accessed_training else False

    context = {
        'allowed': allowed,
        'training': training,
        'trainings': trainings,
        'accessed_training': accessed_training,
    }
    return render(request, 'all_trainings.html', context)


# Function to Render the All Modules Page
@login_required
def all_modules(request, training_id):
    training = Training.objects.get(id=training_id)
    modules = Module.objects.filter(training=training)
    context = {
        'training': training,
        'modules': modules
    }
    return render(request, 'all_modules.html', context)

# Function to render a single video page


@login_required
def media(request, training_id, module_id, media_id=None):
    module = Module.objects.get(id=module_id)
    medias = Media.objects.filter(module=module)
    training = Training.objects.get(id=training_id)
    media = None
    if media_id:
        media = Media.objects.get(id=media_id)

    # print(medias[0])
    # if len(media) > 1:
    #     first_media = media[0]
    # else:
    #     first_media = media
    context = {
        'module': module,
        'medias': medias,
        'media': media,
        'first_media': medias.first(),
        'training': training,
    }
    return render(request, 'single_media.html', context)


# Function to render the single_media page
@login_required
def single_media(request, training_id, module_id, media_id):
    training = Training.objects.get(id=training_id)
    module = Module.objects.get(id=module_id)
    media = Media.objects.get(id=media_id)
    medias = Media.objects.filter(module=module)
    context = {
        'module': module,
        'media': media,
        'training': training,
        'medias': medias,
    }
    return render(request, 'single_media.html', context)
