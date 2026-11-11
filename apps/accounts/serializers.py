from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import serializers


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = CustomUser
        fields = ("id", "email", "full_name", "password", "password_confirm")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data.get("full_name", ""),
            password=validated_data["password"],
            role=CustomUser.Role.FREE,
            credits_balance=25,
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    is_pro = serializers.BooleanField(source="is_pro_or_enterprise", read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "full_name",
            "role",
            "credits_balance",
            "is_pro",
            "date_joined",
        )
        read_only_fields = ("id", "email", "role", "credits_balance", "is_pro", "date_joined")
class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True, write_only=True)
    def validate_id_token(self, value):
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        try:
            # গুগলের পাবলিক সার্টিফিকেট দিয়ে ক্রিপ্টোগ্রাফিক্যালি যাচাই করা
            id_info = id_token.verify_oauth2_token(
                value, 
                google_requests.Request(), 
                client_id
            )
            # টোকেন ভ্যালিড হলে গুগলের প্রোফাইল ডাটা ফেরত পাঠানো
            return id_info
        except Exception as e:
            raise serializers.ValidationError(f"Invalid Google Token: {str(e)}")