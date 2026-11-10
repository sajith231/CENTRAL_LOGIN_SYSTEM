from django.test import TestCase
from django.urls import reverse

from .models import MobileProject


class MobileProjectCreateTests(TestCase):
    def test_create_project_defaults_t_erp_to_false(self):
        response = self.client.post(
            reverse('MobileApp:mobileproject_create'),
            {'project_name': 'Standard Project', 'app_type': 'mobile_app'},
        )

        self.assertRedirects(response, reverse('MobileApp:mobileapp_list'))
        self.assertFalse(MobileProject.objects.get(project_name='Standard Project').t_erp)

    def test_create_project_accepts_t_erp_checkbox(self):
        response = self.client.post(
            reverse('MobileApp:mobileproject_create'),
            {
                'project_name': 'T ERP Project',
                'app_type': 'mobile_app',
                't_erp': 'on',
            },
        )

        self.assertRedirects(response, reverse('MobileApp:mobileapp_list'))
        self.assertTrue(MobileProject.objects.get(project_name='T ERP Project').t_erp)
