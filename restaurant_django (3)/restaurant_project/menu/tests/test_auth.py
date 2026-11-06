# რეგისტრაციისა და შესვლის ტესტები. დროებითი სატესტო ბაზა ინახავს მხოლოდ ტესტის მომხმარებლებს.
from django.test import TestCase, Client
from django.contrib.auth import get_user_model


class AccountTests(TestCase):
    def setUp(self):
        """ყოველი ტესტის წინ ვამზადებთ დამოუკიდებელ საწყის მონაცემებს."""
        self.data = {
            "first_name": "გურამი",
            "username": "guram",
            "email": "guram@example.com",
            "password1": "Kitchen!Leaf4829",
            "password2": "Kitchen!Leaf4829",
        }

    def test_register_page(self):
        """რეგისტრაციის გვერდი და ელფოსტის ველი უნდა გამოჩნდეს."""
        r = self.client.get("/register/")
        self.assertContains(r, "შექმენი ანგარიში")
        self.assertContains(r, 'name="email"')

    def test_registration_creates_hashed_password_and_logs_in(self):
        """მომხმარებელი ინახება ჰეშირებული პაროლით და იწყება სესია."""
        r = self.client.post("/register/", self.data)
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        user = get_user_model().objects.get(username="guram")
        self.assertTrue(user.check_password(self.data["password1"]))
        self.assertNotEqual(user.password, self.data["password1"])
        self.assertEqual(user.email, self.data["email"])
        self.assertEqual(str(user.pk), self.client.session["_auth_user_id"])

    def test_password_mismatch(self):
        """განსხვავებული გამეორებული პაროლით მომხმარებელი არ იქმნება."""
        self.data["password2"] = "Different!Secret888"
        r = self.client.post("/register/", self.data)
        self.assertIn("password2", r.context["form"].errors)
        self.assertFalse(get_user_model().objects.exists())

    def test_weak_password(self):
        """სუსტი პაროლი უარყოფილია."""
        self.data.update(password1="12345678", password2="12345678")
        self.client.post("/register/", self.data)
        self.assertFalse(get_user_model().objects.exists())

    def test_duplicate_username(self):
        """დაკავებული მომხმარებლის სახელით მეორე ანგარიში ვერ შეიქმნება."""
        get_user_model().objects.create_user(
            username="guram", password="Another!Secret882"
        )
        r = self.client.post("/register/", self.data)
        self.assertIn("username", r.context["form"].errors)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_bad_email(self):
        """არასწორი ფორმატის ელფოსტა უარყოფილია."""
        self.data["email"] = "invalid"
        r = self.client.post("/register/", self.data)
        self.assertIn("email", r.context["form"].errors)
        self.assertFalse(get_user_model().objects.exists())

    def test_login_and_post_logout(self):
        """სწორი მონაცემებით შესვლა და POST-ით გამოსვლა მუშაობს."""
        user = get_user_model().objects.create_user(
            username="guram", password=self.data["password1"]
        )
        r = self.client.post(
            "/login/", {"username": "guram", "password": self.data["password1"]}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(str(user.pk), self.client.session["_auth_user_id"])
        self.assertEqual(self.client.get("/logout/").status_code, 405)
        self.client.post("/logout/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_wrong_password(self):
        """არასწორი მონაცემები სესიას არ ქმნის."""
        r = self.client.post(
            "/login/", {"username": "unknown", "password": "incorrect"}
        )
        self.assertContains(r, "მომხმარებლის სახელი ან პაროლი არასწორია.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_external_next_rejected(self):
        """შესვლის შემდეგ უცხო საიტზე გადამისამართება არ უნდა მოხდეს."""
        get_user_model().objects.create_user(
            username="guram", password=self.data["password1"]
        )
        r = self.client.post(
            "/login/?next=https://example.com",
            {"username": "guram", "password": self.data["password1"]},
        )
        self.assertEqual(r.url, "/")

    def test_csrf_required_for_registration(self):
        """რეგისტრაციის POST-იც მოითხოვს CSRF ტოკენს."""
        self.assertEqual(
            Client(enforce_csrf_checks=True).post("/register/", self.data).status_code,
            403,
        )

    def test_signed_in_registration_redirect(self):
        """უკვე შესულ მომხმარებელს რეგისტრაციის ნაცვლად მენიუზე ვაბრუნებთ."""
        user = get_user_model().objects.create_user(
            username="guram", password=self.data["password1"]
        )
        self.client.force_login(user)
        self.assertRedirects(
            self.client.get("/register/"), "/", fetch_redirect_response=False
        )
