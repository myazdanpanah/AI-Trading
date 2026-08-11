"""Authentication views."""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from apps.users.models import User, UserProfile
from apps.users.serializers import UserCreateSerializer, UserSerializer, UserProfileSerializer


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """Register a new user."""
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    """Logout user by blacklisting refresh token."""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset(request):
    """Initiate password reset."""
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    # TODO: Send password reset email
    return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    """Confirm password reset."""
    # TODO: Implement password reset confirmation
    return Response({'message': 'Password reset confirmed'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """Get current user profile."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return Response({
        'user': UserSerializer(user).data,
        'profile': UserProfileSerializer(profile).data,
    })


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """Update user profile."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Update user fields
    for field in ['first_name', 'last_name', 'email', 'preferred_ai_provider']:
        if field in request.data:
            setattr(user, field, request.data[field])
    user.save()
    
    # Update profile fields
    for field in ['risk_level', 'favorite_symbols', 'notification_settings', 'timezone']:
        if field in request.data:
            setattr(profile, field, request.data[field])
    profile.save()
    
    return Response({
        'user': UserSerializer(user).data,
        'profile': UserProfileSerializer(profile).data,
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Change user password."""
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not old_password or not new_password or not confirm_password:
        return Response(
            {'error': 'All password fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not user.check_password(old_password):
        return Response(
            {'error': 'Current password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password != confirm_password:
        return Response(
            {'error': 'New passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return Response(
            {'error': str(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user.set_password(new_password)
    user.save()
    
    return Response({'message': 'Password changed successfully'})
