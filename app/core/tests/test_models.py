from django.test import TestCase
from django.contrib.auth import get_user_model


class UserTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'example123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_email_normalization(self):
        sample_emails = [
            ['test1@eXample.com', 'test1@example.com'],
            ['tEst2@Example.com', 'tEst2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['Test4@ExamPle.com', 'Test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                password='example123'
            )
            self.assertEqual(user.email, expected)

    def test_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                password='example123'
            )

    def test_create_super_user(self):
        email = 'test@example.com'
        password = 'example123'
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password,
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)