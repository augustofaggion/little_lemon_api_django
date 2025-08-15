from django.apps import AppConfig

class LittleLemonAPIConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "LittleLemonAPI"

    def ready(self):
        from django.contrib.auth.models import Group
        for group_name in ["Manager", "Delivery crew"]:
            Group.objects.get_or_create(name=group_name)
