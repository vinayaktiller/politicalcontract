from rest_framework import serializers

class TokenSerializer(serializers.Serializer):
    """
    Serializer for authentication tokens.

    This class defines the structure for refresh and access tokens returned 
    after a successful authentication.

    Attributes:
        - `refresh` (str): The refresh token used to obtain a new access token.
        - `access` (str): The access token used for API authentication.
    """
    refresh = serializers.CharField()
    access = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for formatting responses from the LoginWithGoogle API.

    This serializer ensures proper structuring of the response data and validation.
    It contains user authentication details, tokens (if applicable), and 
    messages related to the login process.

    Attributes:
        - `user_type` (str): Defines the user category (`'olduser'`, `'pendinguser'`, `'newuser'`).
        - `user_email` (str): The email address linked to the user's account.
        - `user_id` (int, optional): The user's unique ID (present for existing users).
        - `tokens` (dict, optional): Authentication tokens for verified users (`refresh`, `access`).
        - `message` (str, optional): Additional information regarding the user’s status.
    
    """
    user_type = serializers.CharField()
    user_email = serializers.EmailField()
    user_id = serializers.IntegerField(required=False)
    tokens = TokenSerializer(required=False)
    message = serializers.CharField(required=False)
    name = serializers.CharField(required=False, allow_null=True)  # New field
    profile_pic = serializers.URLField(required=False, allow_null=True)  # New field