from rest_framework import serializers
from .models import Room, ChatMessage, RoomMedia
from accounts.serializers import UserSerializer


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    sender_email = serializers.ReadOnlyField(source='sender.email')

    class Meta:
        model = ChatMessage
        fields = ('id', 'room', 'sender', 'sender_name', 'sender_email', 'content', 'timestamp')
        read_only_fields = ('id', 'sender', 'timestamp')


class RoomMediaSerializer(serializers.ModelSerializer):
    added_by_name = serializers.ReadOnlyField(source='added_by.username')

    class Meta:
        model = RoomMedia
        fields = ('id', 'room', 'added_by', 'added_by_name', 'video_url', 'title', 'added_at')
        read_only_fields = ('id', 'added_by', 'added_at')


class RoomSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    joined_by_detail = UserSerializer(source='joined_by', read_only=True)

    class Meta:
        model = Room
        fields = (
            'id', 'created_at', 'created_by', 'created_by_detail', 
            'joined_by', 'joined_by_detail', 'current_video_url', 
            'is_playing', 'current_time', 'last_updated_at'
        )
        read_only_fields = ('id', 'created_at', 'created_by', 'last_updated_at')
