from rest_framework import generics, status, permissions
from rest_framework.response import Response

from . import serializers


class TokenViewBase(generics.GenericAPIView):
    serializer_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK
        )


class TokenObtainPairView(TokenViewBase):
    serializer_class = serializers.TokenObtainPairSerializer


class HIDTokenObtainPairView(TokenViewBase):
    serializer_class = serializers.HIDTokenObtainPairSerializer


class TokenRefreshView(TokenViewBase):
    serializer_class = serializers.TokenRefreshSerializer
    permission_classes = (permissions.IsAuthenticated,)
