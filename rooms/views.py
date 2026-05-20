from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Room, ChatMessage, RoomMedia
from .serializers import RoomSerializer, ChatMessageSerializer, RoomMediaSerializer


class RoomCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Create a new room with the active authenticated user as the creator
        room = Room.objects.create(created_by=request.user)
        serializer = RoomSerializer(room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def get_room(pk, user):
    if str(pk) == '00000000-0000-0000-0000-000000000000':
        room, _ = Room.objects.get_or_create(
            id='00000000-0000-0000-0000-000000000000',
            defaults={'created_by': user}
        )
        return room
    return get_object_or_404(Room, pk=pk)


class RoomJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        room = get_room(pk, request.user)
        
        # If the user joining is not the creator, bind them to joined_by
        if room.created_by != request.user:
            room.joined_by = request.user
            room.save()
                
        serializer = RoomSerializer(room)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoomDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        room = get_room(pk, request.user)
        serializer = RoomSerializer(room)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoomChatHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        room = get_room(pk, request.user)
        messages = room.chat_messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


import os
import cloudinary
import cloudinary.uploader
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

# Initialize Cloudinary config from environment variables
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )

class MediaUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if Cloudinary environment variables are configured
        if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
            try:
                # Upload directly to Cloudinary CDN
                # upload_large supports chunked uploading, perfect for streaming and large mobile videos (prevents memory OOM)
                upload_result = cloudinary.uploader.upload_large(
                    file_obj,
                    resource_type="auto",
                    chunk_size=6000000  # 6MB chunks
                )
                media_url = upload_result.get('secure_url')
                if media_url:
                    return Response({"url": media_url}, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Log the error and fallback to local file system
                print(f"Cloudinary upload failed: {e}. Falling back to default local storage.")
        
        # Save securely using Django's default storage engine without loading the entire file into memory (prevents OOM crashes on Render free tier)
        file_name = default_storage.get_available_name(file_obj.name)
        file_path = default_storage.save(os.path.join('uploads', file_name), file_obj)
        
        # Normalize the path for URLs (replaces backslashes on Windows systems)
        file_path_url = file_path.replace('\\', '/')
        
        # Build absolute streaming URL
        media_url = request.build_absolute_uri(settings.MEDIA_URL + file_path_url)
        
        # Force HTTPS in production to prevent browser Mixed Content security block
        if 'localhost' not in media_url and '127.0.0.1' not in media_url:
            media_url = media_url.replace('http://', 'https://')
            
        return Response({"url": media_url}, status=status.HTTP_201_CREATED)


class RoomMediaHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        room = get_room(pk, request.user)
        media_items = room.shared_medias.all()
        serializer = RoomMediaSerializer(media_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoomMediaDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, media_id):
        room = get_room(pk, request.user)
        media_item = get_object_or_404(RoomMedia, room=room, pk=media_id)
        
        # If the deleted video is the currently active room video, clear it
        if room.current_video_url == media_item.video_url:
            room.current_video_url = None
            room.is_playing = False
            room.current_time = 0.0
            room.save()
            
        media_item.delete()
        return Response({"detail": "Media deleted successfully"}, status=status.HTTP_200_OK)




