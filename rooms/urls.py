from django.urls import path
from .views import (
    RoomCreateView, RoomJoinView, RoomDetailView, RoomChatHistoryView, 
    MediaUploadView, RoomMediaHistoryView, RoomMediaDeleteView
)

urlpatterns = [
    path('create/', RoomCreateView.as_view(), name='room_create'),
    path('upload/', MediaUploadView.as_view(), name='media_upload'),
    path('<uuid:pk>/join/', RoomJoinView.as_view(), name='room_join'),
    path('<uuid:pk>/', RoomDetailView.as_view(), name='room_detail'),
    path('<uuid:pk>/chat/', RoomChatHistoryView.as_view(), name='room_chat_history'),
    path('<uuid:pk>/media/', RoomMediaHistoryView.as_view(), name='room_media_history'),
    path('<uuid:pk>/media/<int:media_id>/', RoomMediaDeleteView.as_view(), name='room_media_delete'),
]
