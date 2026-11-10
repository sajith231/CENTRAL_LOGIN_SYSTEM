import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from MobileApp.models import MobileProject, MobileControl, MobileBillingHistory
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
        Package.objects.create(project=self.project_a, package_name="Prime", users_count=10)
        Package.objects.create(project=self.project_b, package_name="Prime", users_count=10)
        Package.objects.create(project=self.project_b, package_name="Basic", users_count=5)

    def _url(self):
        return reverse("auto_licence:api_licence_create")

    def _t_erp_url(self):
        return reverse("auto_licence:t_erp_api_licence_create")

    def _payload(self, projects=None, email="sajiththomas231@gmail.com", company_name="SAJITH TEST"):
        if projects is None:
            projects = [{"project": "Trellisco Beta", "package": "Prime"}]
        return {
            "corporate": {"name": "SAJITH TEST", "place": ""},
            "company": {
                "name": company_name,
                "place": "",
                "email": email,
                "contact_no": "9061947005",
                "country": "India",
            },
            "projects": projects,
        }

    def _post(self, payload):
        return self.client.post(
            self._url(), data=json.dumps(payload), content_type="application/json"
        )

    def _post_t_erp(self, payload):
        return self.client.post(
            self._t_erp_url(), data=json.dumps(payload), content_type="application/json"
        )

    def test_projects_default_to_not_t_erp(self):
        self.assertFalse(self.project_a.t_erp)
        self.assertFalse(self.project_b.t_erp)

    def test_t_erp_endpoint_rejects_projects_not_enabled(self):
        resp = self._post_t_erp(self._payload())
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not enabled for the T-ERP", resp.json()["error"])
        self.assertEqual(MobileControl.objects.count(), 0)

    def test_t_erp_endpoint_allows_only_enabled_projects(self):
        self.project_b.t_erp = True
        self.project_b.save(update_fields=["t_erp"])

        resp = self._post_t_erp(self._payload())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(MobileControl.objects.count(), 1)
        self.assertEqual(MobileControl.objects.get().project, self.project_b)

        control = MobileControl.objects.get()
        self.assertAlmostEqual(
            (control.expiry_date - timezone.now()).total_seconds(),
            timedelta(days=14).total_seconds(),
            delta=5,
        )
        self.assertEqual(
            MobileBillingHistory.objects.get(control=control).extended_days,
            14,
        )

    def test_regular_endpoint_still_creates_thirty_day_licence(self):
        resp = self._post(self._payload())
        self.assertEqual(resp.status_code, 201)

        control = MobileControl.objects.get()
        self.assertAlmostEqual(
            (control.expiry_date - timezone.now()).total_seconds(),
            timedelta(days=30).total_seconds(),
            delta=5,
        )
        self.assertEqual(
            MobileBillingHistory.objects.get(control=control).extended_days,
            30,
        )

    def test_bulk_creates_licences_for_multiple_projects(self):
        resp = self._post(self._payload(projects=[
            {"project": "Trellisco Alpha", "package": "Prime"},
            {"project": "Trellisco Beta", "package": "Prime"},
        ]))
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["reused_existing_company"])
        self.assertEqual(data["created_count"], 2)
        self.assertEqual(data["skipped_count"], 0)

        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(Shop.objects.count(), 1)
        self.assertEqual(MobileControl.objects.count(), 2)
        self.assertEqual(MobileBillingHistory.objects.count(), 2)

        store = Store.objects.get()
        shop = Shop.objects.get()
        for control in MobileControl.objects.all():
            self.assertEqual(control.store, store)
            self.assertEqual(control.shop, shop)
            self.assertEqual(control.client_id, "sajiththomas231@gmail.com")
            self.assertEqual(control.customer_name, "SAJITH TEST")
            self.assertEqual(control.package.package_name, "Prime")
            self.assertEqual(control.licence_type, "new")
            self.assertEqual(control.login_limit, 10)

        statuses = {r["project"]: r["status"] for r in data["results"]}
        self.assertEqual(statuses, {
            "Trellisco Alpha": "created",
            "Trellisco Beta": "created",
        })

    def test_existing_email_skips_only_projects_already_licensed(self):
        first = self._post(self._payload(projects=[
            {"project": "Trellisco Alpha", "package": "Prime"},
        ]))
        self.assertEqual(first.status_code, 201)
        shop = Shop.objects.get()
        existing_control = MobileControl.objects.get(project=self.project_a)
        existing_key = existing_control.license_key

        resp = self._post(self._payload(projects=[
            {"project": "Trellisco Alpha", "package": "Prime"},
            {"project": "Trellisco Beta", "package": "Prime"},
        ]))
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data["reused_existing_company"])
        self.assertEqual(data["created_count"], 1)
        self.assertEqual(data["skipped_count"], 1)

        # No duplicate corporate/company and only one new licence.
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(Shop.objects.count(), 1)
        self.assertEqual(MobileControl.objects.count(), 2)

        existing_control.refresh_from_db()
        self.assertEqual(existing_control.license_key, existing_key)

        results = {r["project"]: r["status"] for r in data["results"]}
        self.assertEqual(results["Trellisco Alpha"], "skipped_existing")
        self.assertEqual(results["Trellisco Beta"], "created")
        self.assertEqual(MobileControl.objects.get(project=self.project_b).shop, shop)

    def test_different_company_name_reuses_company_matched_by_email(self):
        first = self._post(self._payload(
            projects=[{"project": "Trellisco Alpha", "package": "Prime"}],
            company_name="OLD COMPANY NAME",
        ))
        self.assertEqual(first.status_code, 201)

        resp = self._post(self._payload(
            projects=[{"project": "Trellisco Beta", "package": "Prime"}],
            company_name="NEW COMPANY NAME",
        ))
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data["reused_existing_company"])

        # The email-matched company wins; the submitted different name is ignored.
        self.assertEqual(Shop.objects.count(), 1)
        self.assertEqual(Shop.objects.get().name, "OLD COMPANY NAME")
        control_b = MobileControl.objects.get(project=self.project_b)
        self.assertEqual(control_b.customer_name, "OLD COMPANY NAME")
        self.assertEqual(data["company"]["name"], "OLD COMPANY NAME")

    def test_invalid_package_rejects_whole_request(self):
        resp = self._post(self._payload(projects=[
            {"project": "Trellisco Alpha", "package": "Prime"},
            {"project": "Trellisco Beta", "package": "Premium"},
        ]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not found", resp.json()["error"])
        self.assertEqual(MobileControl.objects.count(), 0)
        self.assertEqual(MobileBillingHistory.objects.count(), 0)
        self.assertEqual(Store.objects.count(), 0)
        self.assertEqual(Shop.objects.count(), 0)

    def test_package_must_belong_to_selected_project(self):
        # "Basic" exists only under project B, not project A.
        resp = self._post(self._payload(projects=[
            {"project": "Trellisco Alpha", "package": "Basic"},
        ]))
        self.assertEqual(resp.status_code, 400)
        error = resp.json()["error"]
        self.assertIn("Trellisco Alpha", error)
        self.assertIn("not found", error)
        self.assertEqual(MobileControl.objects.count(), 0)

    def test_unknown_project_rejected(self):
        resp = self._post(self._payload(projects=[
            {"project": "Missing Project", "package": "Prime"},
        ]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not found", resp.json()["error"])
        self.assertEqual(MobileControl.objects.count(), 0)
        self.assertEqual(Store.objects.count(), 0)
        self.assertEqual(Shop.objects.count(), 0)

    def test_duplicate_project_in_payload_rejected(self):
        resp = self._post(self._payload(projects=[
            {"project": "Trellisco Alpha", "package": "Prime"},
            {"project": "Trellisco Alpha", "package": "Prime"},
        ]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("more than once", resp.json()["error"])
        self.assertEqual(MobileControl.objects.count(), 0)

    def test_project_and_package_matching_requires_exact_names(self):
        resp = self._post(self._payload(projects=[
            {"project": "trellisco alpha", "package": "pRiMe"},
        ]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("match exactly", resp.json()["error"])
        self.assertEqual(MobileControl.objects.count(), 0)

    def test_project_package_pair_is_validated_against_same_project(self):
        resp = self._post(self._payload(projects=[
            {"project": "Trellisco Alpha", "package": "Basic"},
        ]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Trellisco Alpha", resp.json()["error"])
        self.assertEqual(MobileControl.objects.count(), 0)

    def test_empty_projects_list_rejected(self):
        resp = self._post(self._payload(projects=[]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("projects", resp.json()["error"])

    def test_missing_company_email_rejected(self):
        payload = self._payload()
        payload["company"]["email"] = ""
        resp = self._post(payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("email", resp.json()["error"])
