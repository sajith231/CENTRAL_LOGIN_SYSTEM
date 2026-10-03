import json

from django.test import TestCase
from django.urls import reverse

from MobileApp.models import MobileProject, MobileControl
from ModuleAndPackage.models import Package
from branch.models import Branch
from StoreShop.models import Store, Shop


class LicenceCreateApiTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="IMC Developments", country="India", currency_code="INR"
        )
        self.project_a = MobileProject.objects.create(
            project_name="Trellisco Alpha", app_type="mobile_app"
        )
        self.project_b = MobileProject.objects.create(
            project_name="Trellisco Beta", app_type="mobile_app"
        )
        Package.objects.create(project=self.project_b, package_name="Prime", users_count=10)
        Package.objects.create(project=self.project_a, package_name="Prime", users_count=10)

    def _url(self, project):
        return reverse(
            "auto_licence:api_licence_create", kwargs={"endpoint": project.api_endpoint}
        )

    def _payload(self, email="sajiththomas231@gmail.com", company_name="SAJITH TEST"):
        return {
            "corporate": {"name": "SAJITH TEST", "place": ""},
            "company": {
                "name": company_name,
                "place": "",
                "email": email,
                "contact_no": "9061947005",
                "country": "India",
            },
            "package": "Prime",
        }

    def test_new_company_creates_store_shop_and_licence(self):
        resp = self.client.post(
            self._url(self.project_b),
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["reused_existing_company"])
        self.assertEqual(data["client_id"], "sajiththomas231@gmail.com")
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(Shop.objects.count(), 1)
        self.assertEqual(MobileControl.objects.count(), 1)
        self.assertEqual(MobileControl.objects.first().client_id, "sajiththomas231@gmail.com")

    def test_existing_email_reuses_company_store_and_client_id(self):
        # Company already registered under project A
        store = Store.objects.create(
            name="EXISTING CORPORATE", branch=self.branch, place="Old Place"
        )
        shop = Shop.objects.create(
            store=store,
            branch=self.branch,
            name="EXISTING COMPANY NAME",
            place="Old Place",
            email="sajiththomas231@gmail.com",
            contact_no="9999999999",
            country="India",
            currency_code="INR",
            client_id="sajiththomas231@gmail.com",
        )
        existing_store_id = store.store_id
        existing_shop_id = shop.id

        # Same email used for a NEW project licence
        resp = self.client.post(
            self._url(self.project_b),
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["reused_existing_company"])

        # No new corporate/company were created
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(Shop.objects.count(), 1)

        # Existing records untouched (same branch, corporate, details, client_id)
        store.refresh_from_db()
        shop.refresh_from_db()
        self.assertEqual(store.store_id, existing_store_id)
        self.assertEqual(store.name, "EXISTING CORPORATE")
        self.assertEqual(store.branch, self.branch)
        self.assertEqual(shop.id, existing_shop_id)
        self.assertEqual(shop.name, "EXISTING COMPANY NAME")
        self.assertEqual(shop.contact_no, "9999999999")
        self.assertEqual(shop.client_id, "sajiththomas231@gmail.com")
        self.assertEqual(shop.store, store)

        # New licence created under project B pointing at the existing company
        control = MobileControl.objects.filter(project=self.project_b).get()
        self.assertEqual(control.shop, shop)
        self.assertEqual(control.store, store)
        self.assertEqual(control.client_id, "sajiththomas231@gmail.com")
        self.assertEqual(control.customer_name, "EXISTING COMPANY NAME")
        self.assertEqual(control.package.package_name, "Prime")

        # Response reflects the EXISTING company details, not the submitted form
        self.assertEqual(data["corporate"]["name"], "EXISTING CORPORATE")
        self.assertEqual(data["corporate"]["store_id"], existing_store_id)
        self.assertEqual(data["company"]["name"], "EXISTING COMPANY NAME")
        self.assertEqual(data["company"]["contact_no"], "9999999999")
        self.assertEqual(data["company"]["client_id"], "sajiththomas231@gmail.com")

    def test_existing_company_with_non_email_client_id_still_one_licence_per_project(self):
        # Manually registered shop whose client_id is NOT the email
        store = Store.objects.create(name="MANUAL CORPORATE", branch=self.branch)
        shop = Shop.objects.create(
            store=store,
            branch=self.branch,
            name="MANUAL COMPANY",
            email="sajiththomas231@gmail.com",
            client_id="ABC123XYZ789",  # random client_id, not the email
        )

        resp = self.client.post(
            self._url(self.project_b),
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.json()["reused_existing_company"])
        self.assertEqual(MobileControl.objects.count(), 1)

        # Second attempt for the SAME project must be rejected — the
        # existing company already holds a licence under this project.
        resp = self.client.post(
            self._url(self.project_b),
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(MobileControl.objects.count(), 1)

    def test_same_company_cannot_get_two_licences_in_same_project(self):
        self.client.post(
            self._url(self.project_b),
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        resp = self.client.post(
            self._url(self.project_b),
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 409)
        self.assertFalse(resp.json()["success"])
        self.assertEqual(MobileControl.objects.count(), 1)

    def test_package_required_and_exact_match(self):
        resp = self.client.post(
            self._url(self.project_b),
            data=json.dumps({k: v for k, v in self._payload().items() if k != "package"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post(
            self._url(self.project_b),
            data=json.dumps(dict(self._payload(), package="Premium")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not found", resp.json()["error"])

    def test_missing_company_email_rejected(self):
        payload = self._payload()
        payload["company"]["email"] = ""
        resp = self.client.post(
            self._url(self.project_b), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
