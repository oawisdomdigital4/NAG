from django.db import models
from django.conf import settings

class UserActivity(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity'
    )
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'User Activities'
        
    def __str__(self):
        return f"{self.user.username}'s activity"
