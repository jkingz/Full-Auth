import factory
import pytest
from django.conf import settings
from django.urls import reverse
from pytest_factoryboy import register
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from users.models import UserAccount


# ✅ Define a UserFactory
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserAccount  # Your user model
        # skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')  # Hash password
    is_superuser = False  # Default to regular user
    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        """Override to explicitly save the instance after postgeneration hooks."""
        if create and instance.pk is not None:
            instance.save()


# ✅ Register the factory so it works as a pytest fixture
register(UserFactory)


# ✅ Test Setup
@pytest.fixture
def api_client():
    """Fixture for APIClient instance"""
    return APIClient()


@pytest.fixture
def user(db, user_factory):
    """Fixture to create a normal user"""
    return user_factory()

@pytest.fixture
def access_token(user):
    """Fixture to generate JWT token for user authentication"""
    return str(AccessToken.for_user(user))


@pytest.fixture
def urls():
    """Fixture for all authentication URLs"""
    return {
        'create': reverse('jwt_create'),
        'refresh': reverse('jwt_refresh'),
        'verify': reverse('jwt_verify'),
    }


# ✅ Test for Token Verification & User Detail
@pytest.mark.django_db
class TestCustomTokenObtainPairView:
    @pytest.mark.parametrize('token_source', ['cookie', 'body'])
    def test_verify_token(self, api_client, access_token, urls, token_source):
        """Test token verification from cookie and request body"""
        if token_source == 'cookie':
            api_client.cookies['access'] = access_token
            response = api_client.post(urls['verify'], {}, format='json')
        else:
            response = api_client.post(urls['verify'], {'token': access_token}, format='json')

        assert response.status_code == status.HTTP_200_OK, f'Unexpected response: {response.json()}'

    def test_successful_login_sets_cookies(self, api_client, user, urls):
        """Test successful login sets access and refresh cookies"""
        # Prepare login data
        credentials = {'email': user.email, 'password': 'testpass123'}

        # Make POST request
        response = api_client.post(urls['create'], credentials, format='json')

        # Assert response status
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

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

    def test_failed_login_no_cookies(self, api_client, urls):
        """Test failed login doesn't set cookies"""
        # Prepare invalid credentials
        credentials = {'email': 'wrong@example.com', 'password': 'wrongpassword'}

        # Make POST request
        response = api_client.post(urls['create'], credentials, format='json')

        # Assert unauthorized status
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Check no cookies are set
        assert 'access' not in response.cookies
        assert 'refresh' not in response.cookies

    def test_missing_credentials(self, api_client, urls):
        """Test request with missing credentials"""
        # Make POST request with empty data
        response = api_client.post(urls['create'], {}, format='json')

        # Assert bad request status
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Check no cookies are set
        assert 'access' not in response.cookies
        assert 'refresh' not in response.cookies

    def test_invalid_credentials(self, api_client, urls):
        """Test request with invalid credentials"""
        # Prepare invalid credentials
        credentials = {'email': 'wrong@example.com', 'password': 'wrongpassword'}

        # Make POST request
        response = api_client.post(urls['create'], credentials, format='json')

        # Assert unauthorized status
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, f'Unexpected response: {response.json()}'
