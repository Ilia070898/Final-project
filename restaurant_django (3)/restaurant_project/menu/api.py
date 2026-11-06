# გარე სერვერთან ურთიერთობა. სილაბუსი: ფუნქციები/მოდულები, გამონაკლისები, JSON, HTTP მეთოდები. ეს არის API-ის კლიენტი; საკუთარი DRF სერვერი არ არის.
# ჩაწერა ავტომატურად არ მეორდება: კავშირის გაწყვეტამდე სერვერს შეიძლება უკვე შეესრულებინა იგი.

import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError
from decimal import Decimal, InvalidOperation
from django.conf import settings


class APIError(Exception):
    # საკუთარი შეცდომის ტიპი: views.py მას იჭერს და მომხმარებელს შეტყობინებას აჩვენებს.
    pass


def call(path, method="GET", payload=None, params=None):
    """აგზავნის HTTP მოთხოვნას IT Step-ის API-ში. GET პასუხს JSON-დან Python-ის სიად გარდაქმნის."""
    # ბაზის მისამართს ვუმატებთ კონკრეტული ოპერაციის გზას.
    url = settings.API_BASE_URL + path
    if params:
        # urlencode ლექსიკონს მისამართის პარამეტრებად აქცევს, მაგალითად spiciness=0.
        url += "?" + urlencode(params)
    data = None
    if payload is not None:
        # dumps ქმნის JSON ტექსტს, encode კი ქსელში გასაგზავნ ბაიტებს.
        data = json.dumps(payload).encode()
    req = Request(
        url,
        data=data,
        method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        # with პასუხთან კავშირს გამოყენების შემდეგ ხურავს; timeout ლოდინს ზღუდავს.
        with urlopen(req, timeout=settings.API_TIMEOUT) as response:
            raw = response.read().decode("utf-8")
        if method != "GET":
            return None  # ჩაწერის პასუხი ზოგჯერ ცარიელი ან ჩვეულებრივი ტექსტია.
        # loads აბრუნებს Python-ის მონაცემებს JSON ტექსტიდან.
        result = json.loads(raw)
        if not isinstance(result, list):
            raise ValueError("Expected an array")
        return result
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        raise APIError("API request failed") from exc


def money(value):
    """API-ის ფასს Decimal ტიპად გარდაქმნის და ორ ათწილადამდე ამრგვალებს."""
    try:
        # თანხასთან ვიყენებთ Decimal-ს, რათა float-ის დამრგვალების ცდომილება ავიცილოთ.
        result = Decimal(str(value))
        if not result.is_finite() or result < 0:
            raise ValueError()
        return result.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise APIError("Invalid API price") from exc


def products(filters=None):
    """აბრუნებს ყველა კერძს ან ფორმით შერჩეული პირობებით გაფილტრულ სიას."""
    if filters:
        data = call("/Products/GetFiltered", params=filters)
    else:
        data = call("/Products/GetAll")
    try:
        for item in data:
            item["id"] = int(item["id"])
            item["price"] = money(item["price"])
            # საჭირო ველის არყოფნისას KeyError წარმოქმნის APIError-ს.
            for key in ("name", "image", "spiciness", "nuts", "vegeterian"):
                item[key]
        return data
    except (KeyError, TypeError, ValueError) as exc:
        raise APIError("Invalid product response") from exc


def categories():
    """API-დან იღებს კატეგორიების სიას."""
    return call("/Categories/GetAll")


def basket():
    """კითხულობს საერთო API კალათას და მის ორ შესაძლო ფორმატს ერთ ფორმატად გარდაქმნის."""
    data = call("/Baskets/GetAll")
    try:
        for row in data:
            # რეალურ API-ში ნომერი product.id-შია, დოკუმენტაციაში კი productId-ში.
            product_id = row.get("productId")
            if product_id is None:
                product_id = row["product"]["id"]
            row["productId"] = int(product_id)
            row["quantity"] = int(row["quantity"])
            if row["quantity"] < 1:
                raise ValueError()
        return data
    except (KeyError, TypeError, ValueError) as exc:
        raise APIError("Invalid basket response") from exc


def write_basket(product, quantity, exists=False):
    """ახალ ჩანაწერს POST-ით ქმნის, ხოლო არსებულის რაოდენობას PUT-ით ცვლის."""
    basket_item = {
        "productId": product["id"],
        "quantity": quantity,
        "price": float(product["price"]),
    }
    if exists:
        call("/Baskets/UpdateBasket", "PUT", basket_item)
    else:
        call("/Baskets/AddToBasket", "POST", basket_item)


def delete(product_id):
    """კერძის ნომრით აგზავნის DELETE მოთხოვნას გარე API-ში."""
    call(f"/Baskets/DeleteProduct/{product_id}", "DELETE")
