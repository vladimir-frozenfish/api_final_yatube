from django.shortcuts import get_object_or_404

from rest_framework import filters, viewsets, permissions, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from posts.models import Follow, Group, Post, User

from .serializers import (CommentSerializer,
                          FollowSerializer,
                          GroupSerializer,
                          PostSerializer)

from .permissions import IsAuthorOrReadOnly


def get_or_none(model, *args, **kwargs):
    """
    функция возвращает объект модели или None
    """
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnly]

    def get_queryset(self):
        post_id = self.kwargs.get("post_id")
        post = get_object_or_404(Post, id=post_id)
        new_queryset = post.comments.all()
        return new_queryset

    def perform_create(self, serializer):
        post_id = self.kwargs.get("post_id")
        post = get_object_or_404(Post, id=post_id)
        serializer.save(author=self.request.user, post=post)


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('following__username',)

    def get_queryset(self):
        new_queryset = Follow.objects.filter(user=self.request.user.id)
        return new_queryset

    def create(self, request, *args, **kwargs):
        user = self.request.user
        following = get_or_none(User, username=request.data.get('following'))
        if following is None:
            return Response({"message": "Неправильные данные!"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif user == following:
            return Response({"message": "На себя нельзя подписаться!"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif following.following.filter(user=user).exists():
            return Response({"message": "На этого автора уже есть подписка!"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = FollowSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=user, following=following)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
