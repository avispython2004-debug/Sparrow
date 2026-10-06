from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RegisterTests(TestCase):
    def test_register_creates_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser', 'email': 'new@example.com',
            'password1': 'Str0ngPass!99', 'password2': 'Str0ngPass!99',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username='taken', email='dup@example.com', password='x' * 12)
        response = self.client.post(reverse('register'), {
            'username': 'newuser', 'email': 'dup@example.com',
            'password1': 'Str0ngPass!99', 'password2': 'Str0ngPass!99',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
