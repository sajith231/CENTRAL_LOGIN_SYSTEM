from django.db import models
import uuid


def generate_token():
    return uuid.uuid4().hex


class ApiToken(models.Model):
    user = models.ForeignKey('app1.Users', on_delete=models.CASCADE, related_name='api_tokens')
    token = models.CharField(max_length=64, unique=True, default=generate_token)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.token[:8]}..."
