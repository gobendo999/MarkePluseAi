from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import GoogleAuthSerializer, UserRegistrationSerializer, UserProfileSerializer


@extend_schema(
    tags=["Authentication & Accounts"],
    summary="Register a new user",
    description="Registers a new user on the Free tier with 25 initial AI credits.",
    responses={
        201: OpenApiResponse(response=UserProfileSerializer, description="User successfully registered."),
        400: OpenApiResponse(description="Validation error (e.g. duplicate email, password mismatch)."),
    },
)
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        profile_data = UserProfileSerializer(user).data
        return Response(profile_data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Authentication & Accounts"],
    summary="Get or update current user profile",
    description="Returns authenticated user details, role tier, and active credit balance.",
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

@extend_schema(
    tags=["Authentication & Accounts"],
    summary="Google OAuth 2.0 Sign-In / Sign-Up",
    description="Validates Google ID Token, links or creates account, grants 25 free credits, and returns SimpleJWT access & refresh tokens.",
    request=GoogleAuthSerializer,
)
class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # গুগলের ভ্যালিডেটেড প্রোফাইল ডাটা পাওয়া
        google_data = serializer.validated_data["id_token"]
        email = google_data.get("email")
        first_name = google_data.get("given_name", "")
        last_name = google_data.get("family_name", "")

        # ১. Account Linking: ডাটাবেজে এই ইমেইলের ইউজার আগে থেকেই আছে কি না চেক করা
        user = CustomUser.objects.filter(email=email).first()

        if not user:
            # ২. নাম দুটি একসাথে জোড়া লাগিয়ে full_name বানানো
            full_name = f"{first_name} {last_name}".strip() or email.split("@")[0]

            # আমাদের কাস্টম ইউজার টেবিলে সেভ করা (২৫ ফ্রি ক্রেডিট সহ)
            user = CustomUser.objects.create_user(
                email=email,
                full_name=full_name,
                role="FREE",
                credits_balance=25,
            )

        # ৩. SimpleJWT অ্যাক্সেস এবং রিফ্রেশ টোকেন জেনারেট করা
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Google authentication successful!",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserProfileSerializer(user).data,
        }, status=status.HTTP_200_OK)
