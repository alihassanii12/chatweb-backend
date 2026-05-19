import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    joined_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='joined_rooms')
    
    # Video Synced parameters
    current_video_url = models.URLField(max_length=1000, null=True, blank=True)
    is_playing = models.BooleanField(default=False)
    current_time = models.FloatField(default=0.0)
    last_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.id} (Created by {self.created_by.email})"


class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message by {self.sender.username} at {self.timestamp}"


class RoomMedia(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='shared_medias')
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_medias')
    video_url = models.URLField(max_length=1000)
    title = models.CharField(max_length=255, default='Shared Video')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.title} added in {self.room.id}"

