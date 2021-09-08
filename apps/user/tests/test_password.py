from django.core.exceptions import ValidationError

from deep.tests import TestCase

from user.validators import CustomMaximumLengthValidator


class PasswordCheckerTest(TestCase):

    def test_password_greater_than_128_characters(self):
        self.assertIsNone(CustomMaximumLengthValidator().validate('12345678'))
        self.assertIsNone(CustomMaximumLengthValidator(max_length=20).validate('123'))

        with self.assertRaises(ValidationError) as vd:
            CustomMaximumLengthValidator(max_length=128).validate('12' * 129)
        self.assertEqual(vd.exception.error_list[0].code, 'password_too_long')
