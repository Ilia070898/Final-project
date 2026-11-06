# მენიუს, API-ის და კალათის ტესტები. mock-ით ვანაცვლებთ ქსელს, რომ საერთო კალათა არ შეიცვალოს.
from decimal import Decimal
from unittest.mock import patch
from urllib.error import URLError
from django.test import SimpleTestCase, Client
from menu import api

PRODUCT = {
    "id": 1,
    "name": "Test salad",
    "price": Decimal("9.50"),
    "nuts": False,
    "vegeterian": True,
    "spiciness": 0,
    "categoryId": 1,
    "image": "https://example.com/salad.png",
}
CATEGORIES = [{"id": 1, "name": "Salads"}]


class PageTests(SimpleTestCase):
    def setUp(self):
        """ყოველი ტესტის წინ ვამზადებთ დამოუკიდებელ საწყის მონაცემებს."""
        for name, value in [
            ("products", [PRODUCT.copy()]),
            ("categories", CATEGORIES),
            ("basket", [{"productId": 1, "quantity": 2, "price": 9.5}]),
            ("write_basket", None),
            ("delete", None),
        ]:
            p = patch("menu.views.api." + name, return_value=value)
            setattr(self, name, p.start())
            self.addCleanup(p.stop)

    def test_catalog_and_cards(self):
        """ვამოწმებთ კერძის სახელისა და ნიშნების გამოჩენას მენიუში."""
        r = self.client.get("/")
        self.assertContains(r, "Test salad")
        self.assertContains(r, "0 / 4")
        self.assertContains(r, "თხილეულის გარეშე")

    def test_combined_filters_include_zero_and_false(self):
        """ვამოწმებთ, რომ სიცხარე 0 და false ფილტრი API-მდე სწორად მიდის."""
        r = self.client.get(
            "/",
            {
                "spiciness": "0",
                "nuts": "false",
                "vegeterian": "true",
                "categoryId": "1",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.products.assert_called_once_with(
            {"spiciness": 0, "nuts": "false", "vegeterian": "true", "categoryId": "1"}
        )

    def test_bad_filter_not_sent(self):
        """არასწორ ფილტრზე API მოთხოვნა არ უნდა გაიგზავნოს."""
        self.client.get("/", {"spiciness": "9"})
        self.products.assert_not_called()

    def test_cart_total(self):
        """ორი პორციის ჯამი უნდა იყოს 19.00."""
        r = self.client.get("/cart/")
        self.assertEqual(r.context["total"], Decimal("19.00"))
        self.assertEqual(r.context["count"], 2)

    def test_empty_cart(self):
        """ცარიელი კალათა აჩვენებს შესაბამის შეტყობინებას და ნულოვან ჯამს."""
        self.basket.return_value = []
        r = self.client.get("/cart/")
        self.assertContains(r, "შენი კალათა ჯერ ცარიელია")
        self.assertEqual(r.context["total"], Decimal("0.00"))

    def test_add_existing_uses_catalog_price(self):
        """არსებულ კერძს რაოდენობა ეზრდება; ბრაუზერის ყალბი ფასი იგნორირებულია."""
        r = self.client.post("/cart/add/1/", {"price": "0.01"})
        self.assertRedirects(r, "/cart/", fetch_redirect_response=False)
        self.write_basket.assert_called_once_with(PRODUCT, 3, True)

    def test_add_new(self):
        """ახალი კერძი უნდა დაემატოს ერთი პორციით."""
        self.basket.return_value = []
        self.client.post("/cart/add/1/")
        self.write_basket.assert_called_once_with(PRODUCT, 1, False)

    def test_missing_product(self):
        """არარსებული კერძისთვის ჩაწერა არ ხდება."""
        self.assertEqual(self.client.post("/cart/add/999/").status_code, 302)
        self.write_basket.assert_not_called()

    def test_quantity_limits(self):
        """ვამოწმებთ არასწორ რაოდენობებს: ნული, უარყოფითი, წილადი, ტექსტი და ზედმეტად დიდი რიცხვი."""
        for quantity in ["0", "-1", "100", "1.5", "abc", ""]:
            with self.subTest(quantity=quantity):
                self.assertEqual(
                    self.client.post(
                        "/cart/update/1/", {"quantity": quantity}
                    ).status_code,
                    302,
                )
        self.write_basket.assert_not_called()

    def test_update(self):
        """რაოდენობის ცვლილება სწორ პროდუქტსა და რაოდენობას უგზავნის API-ს."""
        self.assertEqual(
            self.client.post("/cart/update/1/", {"quantity": "4"}).status_code,
            302,
        )
        self.write_basket.assert_called_once_with(PRODUCT, 4, True)

    def test_add_limit(self):
        """99 პორციაზე მეტის დამატება უნდა შეიზღუდოს."""
        self.basket.return_value = [{"productId": 1, "quantity": 99}]
        self.assertEqual(self.client.post("/cart/add/1/").status_code, 302)
        self.write_basket.assert_not_called()

    def test_delete(self):
        """წაშლის ფუნქცია იღებს სწორ კერძის ნომერს."""
        self.assertEqual(self.client.post("/cart/remove/1/").status_code, 302)
        self.delete.assert_called_once_with(1)

    def test_get_cannot_mutate(self):
        """GET მეთოდით კალათის შეცვლის მცდელობა უნდა უარყოს."""
        for action in ["add", "update", "remove"]:
            self.assertEqual(self.client.get(f"/cart/{action}/1/").status_code, 405)

    def test_csrf_required(self):
        """CSRF ტოკენის გარეშე POST უნდა უარყოს."""
        self.assertEqual(
            Client(enforce_csrf_checks=True).post("/cart/add/1/").status_code, 403
        )

    def test_api_outage_page(self):
        """API-ის გათიშვისას გვერდები აბრუნებს 503 სტატუსს."""
        self.products.side_effect = api.APIError()
        self.assertEqual(self.client.get("/").status_code, 503)
        self.assertEqual(self.client.get("/cart/").status_code, 503)

    def test_api_outage_write(self):
        """წარუმატებელი ჩაწერის შემდეგ მომხმარებელი ხედავს შეცდომის შეტყობინებას."""
        self.write_basket.side_effect = api.APIError()
        r = self.client.post("/cart/add/1/", follow=True)
        self.assertContains(r, "სერვერთან დაკავშირება ვერ მოხერხდა")

    def test_plain_form_update_refreshes_total(self):
        """POST-ის შემდეგ გადამისამართებულ გვერდზე ახალი რაოდენობა და ჯამი ჩანს."""

        def save_quantity(product, quantity, exists):
            self.basket.return_value = [{"productId": 1, "quantity": quantity}]

        self.write_basket.side_effect = save_quantity
        response = self.client.post("/cart/update/1/", {"quantity": "4"}, follow=True)
        self.assertEqual(response.redirect_chain, [("/cart/", 302)])
        self.assertEqual(response.context["total"], Decimal("38.00"))
        self.assertContains(response, "კალათა განახლებულია")

    def test_plain_form_error_is_visible(self):
        """არასწორი რაოდენობის შეტყობინება HTML გვერდზე ჩანს."""
        response = self.client.post("/cart/update/1/", {"quantity": "0"}, follow=True)
        self.assertContains(response, "რაოდენობა უნდა იყოს მთელი რიცხვი")
        self.write_basket.assert_not_called()

    def test_delete_last_item_shows_empty_cart(self):
        """ბოლო კერძის წაშლის შემდეგ ცარიელი კალათა უნდა გამოჩნდეს."""

        def delete_item(product_id):
            self.basket.return_value = []

        self.delete.side_effect = delete_item
        response = self.client.post("/cart/remove/1/", follow=True)
        self.assertEqual(response.context["count"], 0)
        self.assertContains(response, "შენი კალათა ჯერ ცარიელია")

    def test_pages_do_not_load_javascript(self):
        """გვერდებში script ტეგები და AJAX ატრიბუტები არ უნდა იყოს."""
        for url in ["/", "/cart/", "/register/", "/login/"]:
            response = self.client.get(url)
            self.assertNotContains(response, "<script")
            self.assertNotContains(response, "data-ajax")


class APIClientTests(SimpleTestCase):
    @patch("menu.api.urlopen")
    def test_filter_url(self, opener):
        """ფილტრები სწორად უნდა დაერთოს API-ის URL-ს."""
        opener.return_value.__enter__.return_value.read.return_value = b"[]"
        api.products({"spiciness": 0, "nuts": "false"})
        self.assertIn("spiciness=0&nuts=false", opener.call_args.args[0].full_url)

    @patch("menu.api.urlopen")
    def test_write_payload_and_plain_text(self, opener):
        """PUT მოთხოვნაში სწორი ფასი იგზავნება; ტექსტური პასუხიც მისაღებია."""
        opener.return_value.__enter__.return_value.read.return_value = (
            b"Updated successfully"
        )
        api.write_basket(PRODUCT, 3, True)
        request = opener.call_args.args[0]
        self.assertEqual(request.method, "PUT")
        self.assertIn(b'"price": 9.5', request.data)

    @patch("menu.api.urlopen", side_effect=URLError("offline"))
    def test_network_error(self, opener):
        """ქსელის შეცდომა გარდაიქმნება APIError-ად და მოთხოვნა არ მეორდება."""
        with self.assertRaises(api.APIError):
            api.products()
        self.assertEqual(opener.call_count, 1)

    @patch("menu.api.urlopen")
    def test_invalid_json(self, opener):
        """არასწორი JSON პასუხი კონტროლირებულ შეცდომად უნდა გადაიქცეს."""
        opener.return_value.__enter__.return_value.read.return_value = b"broken"
        with self.assertRaises(api.APIError):
            api.products()

    def test_invalid_prices(self):
        """NaN, უსასრულობა, უარყოფითი და არარიცხვითი ფასი მიუღებელია."""
        for value in ["NaN", "Infinity", "-1", "bad"]:
            with self.assertRaises(api.APIError):
                api.money(value)

    @patch("menu.api.call")
    def test_live_nested_basket_shape(self, call):
        """ვამოწმებთ API-ის რეალურ, ჩაშენებული product-ის ფორმატს."""
        call.return_value = [{"quantity": 2, "price": 9.5, "product": {"id": 2}}]
        self.assertEqual(api.basket()[0]["productId"], 2)

    @patch("menu.api.call")
    def test_documented_flat_basket_shape(self, call):
        """ვამოწმებთ დოკუმენტაციაში აღწერილ productId ფორმატსაც."""
        call.return_value = [{"quantity": 2, "price": 9.5, "productId": 2}]
        self.assertEqual(api.basket()[0]["productId"], 2)
