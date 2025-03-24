import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from users.models import UserAccount


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.email = 'testuser@example.com'
        self.password = 'testpass123'
        self.user = UserAccount.objects.create_user(email=self.email, password=self.password)
        self.access_token = str(AccessToken.for_user(self.user))

        self.url = reverse('jwt_create')  # Token creation endpoint
        self.refresh_url = reverse('jwt_refresh')  # Refresh token endpoint
        self.verify_url = reverse('jwt_verify')  # Token verification endpoint


@pytest.mark.django_db
class TestCustomTokenObtainPairView(TestSetup):
    def test_successful_login_sets_cookies(self):
        """Test successful login sets access and refresh cookies"""
        # Prepare login data
        credentials = {'email': self.email, 'password': self.password}

        # Make POST request
        response = self.client.post(self.url, credentials, format='json')

        # Assert response status
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'access' in response.cookies
        assert 'refresh' in response.cookies

        # Check cookies are set
        assert 'access' in response.cookies
        assert 'refresh' in response.cookies

        # Verify cookie attributes for access token
        access_cookie = response.cookies['access']
        assert access_cookie.value == response.data['access']
        assert access_cookie['max-age'] == settings.AUTH_COOKIE_MAX_AGE
        assert bool(access_cookie['secure']) == settings.AUTH_COOKIE_SECURE
        assert bool(access_cookie['httponly']) == settings.AUTH_COOKIE_HTTP_ONLY
        assert access_cookie['samesite'] == settings.AUTH_COOKIE_SAMESITE
        assert access_cookie['path'] == settings.AUTH_COOKIE_PATH

        # Verify cookie attributes for refresh token
        refresh_cookie = response.cookies['refresh']
        assert refresh_cookie.value == response.data['refresh']
        assert refresh_cookie['max-age'] == settings.AUTH_COOKIE_MAX_AGE
        assert refresh_cookie['secure'] == '' if not settings.AUTH_COOKIE_SECURE else refresh_cookie['secure']
        assert refresh_cookie['httponly'] == '' if not settings.AUTH_COOKIE_HTTP_ONLY else refresh_cookie['httponly']
        assert refresh_cookie['samesite'] == settings.AUTH_COOKIE_SAMESITE
        assert refresh_cookie['path'] == settings.AUTH_COOKIE_PATH

    def test_failed_login_no_cookies(self):
        """Test failed login doesn't set cookies"""
        # Prepare invalid credentials
        credentials = {'email': self.email, 'password': 'wrongpassword'}
        # Make POST request
        response = self.client.post(self.url, credentials, format='json')

        # Assert unauthorized status
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Check no cookies are set
        assert 'access' not in response.cookies
        assert 'refresh' not in response.cookies

    def test_missing_credentials(self):
        """Test request with missing credentials"""
        # Make POST request with empty data
        response = self.client.post(self.url, {}, format='json')

        # Assert bad request status
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Check no cookies are set
        assert 'access' not in response.cookies
        assert 'refresh' not in response.cookies

    def test_invalid_credentials(self):
        """Test request with invalid credentials"""
        # Prepare invalid credentials
        credentials = {'email': self.email, 'password': 'wrongpassword'}
        # Make POST request
        response = self.client.post(self.url, credentials, format='json')
        # Assert unauthorized status
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, f"Unexpected response: {response.json()}"


@pytest.mark.django_db
class TestCustomTokenVerifyView(TestSetup):
    def test_verify_token_from_cookie(self):
        """Test token verification using access token from cookies."""
        self.client.cookies['access'] = self.access_token  # Set the access token in cookies

        response = self.client.post(self.verify_url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK, f"Unexpected response: {response.json()}"

    def test_verify_token_from_body(self):
        """Test token verification by passing the token in request body."""
        data = {'token': self.access_token}
        response = self.client.post(self.verify_url, data, format='json')

        assert response.status_code == status.HTTP_200_OK, f"Unexpected response: {response.json()}"

    def test_no_token_provided(self):
        """Test verification failure when no token is provided in cookie or body."""
        response = self.client.post(self.verify_url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST, f"Unexpected response: {response.json()}"
        # assert 'detail' in response.json(), "Expected error message missing in response."
