from distutils.command.upload import upload
from pydoc import describe
from django.db import models
from datetime import datetime
from django.contrib.auth.models import User, auth
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django_quill.fields import QuillField
# from django.contrib import admin


# Create your models here.

# python manage.py makemigrations
# python manage.py migrate
# python manage.py runserver


# Custom Model for the Device
class Device(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
    browser = models.CharField(max_length=50)
    device = models.CharField(max_length=50)
    device_type = models.CharField(max_length=50)
    os = models.CharField(max_length=20)
    ip = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(default=timezone.now)

    # method to fetch the ip of client
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    # Function for checking the browser, IP-address, and device info of the user
    def set_browser_info(self, request):

        # status of mobile, pc or tablet
        is_mobile = request.user_agent.is_mobile
        is_tablet = request.user_agent.is_tablet
        is_pc = request.user_agent.is_pc

        if is_mobile:
            self.device_type = 'Mobile'
        elif is_tablet:
            self.device_type = 'Tablet'
        elif is_pc:
            self.device_type = 'PC or Laptop'
        else:
            self.device_type = 'Unknown'

        # fetching the browser info
        browser_family = request.user_agent.browser.family
        self.browser = browser_family
        browser_version = request.user_agent.browser.version

        # fetching the os info
        os_family = request.user_agent.os.family
        self.os = os_family
        os_version = request.user_agent.os.version

        # fetching the device info
        device_name = request.user_agent.device.family
        self.device = device_name

        ip = self.get_client_ip(request)
        self.ip = ip

    def is_already_exists(self):
        device_queryset = Device.objects.filter(
            user=self.user,
            browser=self.browser,
            device=self.device,
            device_type=self.device_type,
            os=self.os,
            ip=self.ip)

        return device_queryset.first()

    def is_limit_reached(self, limit=4):
        devices = Device.objects.filter(user=self.user)
        print(devices.count())
        return not devices.count() < limit

    def save(self, *args, **kwargs):
        # figure out warranty end date
        if self.pk:
            self.last_login = timezone.now()
        super(Device, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} - ({self.os}, {self.browser}, {self.device_type}, {self.ip}, {self.session})'


# signal to remove session from DB after deleting the device
@receiver(post_delete, sender=Device)
def delete_session(sender, instance, *args, **kwargs):
    instance.session.delete()

# Model for the Trainings


class Training(models.Model):
    name = models.CharField(max_length=50)
    description = QuillField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_all_modules(self):
        all_modules = Module.objects.filter(training=self)
        return all_modules

    def get_progress(self, completed_ids):
        completed = 0
        module_ids = Module.objects.filter(
            training=self).values_list('id', flat=True)
        all_medias = Media.objects.filter(
            module_id__in=module_ids).values_list('id', flat=True)
        for i in completed_ids:
            if i in all_medias:
                completed += 1
        return int((completed / all_medias.count()) * 100)

    def get_short_description(self):
        # return None
        from html2text import html2text

        text = html2text(self.description.html)
        limit = 150
        description = text
        if description and len(description) > limit:
            return description[0: limit] + "..."
        return description

    def __str__(self):
        return self.name


# Model for the Modules
class Module(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/')
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    prev = models.ForeignKey('self', on_delete=models.CASCADE,
                             related_name='mod_prev', null=True, blank=True)
    next = models.ForeignKey('self', on_delete=models.CASCADE,
                             related_name='mod_next', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_short_description(self):
        limit = 150
        description = self.description
        if len(description) > limit:
            return description[0: limit] + "..."
        return description

    def get_all_media(self):
        all_media = Media.objects.filter(
            module=self).values_list("name", flat=True)
        return all_media

    def get_progress(self, completed_ids):
        completed = 0
        all_medias = Media.objects.filter(
            module=self).values_list('id', flat=True)
        for i in completed_ids:
            if i in all_medias:
                completed += 1
        return int((completed / all_medias.count()) * 100)

    def __str__(self):
        return self.name


# Model for the Media
class Media(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/')
    file = models.FileField(upload_to='videos/')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    prev = models.ForeignKey('self', on_delete=models.CASCADE,
                             related_name='file_prev', null=True, blank=True)
    next = models.ForeignKey('self', on_delete=models.CASCADE,
                             related_name='file_next', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)

# Model for giving the access to the user


class Access(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now, editable=False)


class Completed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
