from django.db import models
from django.contrib.auth.models import User


class Resume(models.Model):
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resume')
    file           = models.FileField(upload_to='resumes/')
    extracted_text = models.TextField(blank=True, null=True)
    uploaded_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s resume"

    @property
    def word_count(self):
        if not self.extracted_text:
            return 0
        return len(self.extracted_text.split())
