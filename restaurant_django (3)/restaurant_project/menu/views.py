# მოთხოვნების დამუშავება. სილაბუსი: Django Views, GET/POST, ფორმები, ავტორიზაცია, შეტყობინებები და სესიები.
from django.contrib.auth import login as auth_login
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .forms import RegistrationForm
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from . import api
from .forms import FilterForm, QuantityForm

ERROR = "სერვერთან დაკავშირება ვერ მოხერხდა. განაახლეთ გვერდი და გადაამოწმეთ კალათა ხელახლა ცდამდე."


# ვეძებთ კერძს მისი ნომრით. თუ ვერ ვიპოვეთ, ვაბრუნებთ None-ს.
def find_product(product_id):
    """კერძების სიაში ნომერს ეძებს; პოვნისას აბრუნებს კერძის ლექსიკონს, სხვა შემთხვევაში None-ს."""
    for product in api.products():
        if product["id"] == product_id:
            return product
    return None


# იგივე ძებნა, ოღონდ კალათაში.
def find_basket_item(product_id):
    """ამოწმებს, მოცემული კერძი უკვე არის თუ არა კალათაში."""
    for item in api.basket():
        if item["productId"] == product_id:
            return item
    return None


# მენიუს გვერდი: ვკითხულობთ ფილტრებს და ვიღებთ კერძებს.
def catalog(request):
    """GET მოთხოვნის ფილტრებს ამოწმებს და მიღებული კერძებით მენიუს HTML გვერდს ქმნის."""
    items = []
    error = None
    try:
        cats = api.categories()
        # თუ URL-ში ფილტრები არ არის, ფორმა შევსებული მონაცემების გარეშე იქმნება.
        form = FilterForm(request.GET or None, categories=cats)
        if not request.GET:
            items = api.products()
        # is_valid ველებს ამოწმებს; მხოლოდ სწორი მონაცემები გადავა API-ში.
        elif form.is_valid():
            items = api.products(form.api_params())
    except api.APIError:
        form = FilterForm()
        error = ERROR
    page_status = 200
    if error:
        page_status = 503
    # context ლექსიკონის სახელებით HTML-ში მონაცემებს მივწვდებით.
    context = {"products": items, "form": form, "error": error}
    return render(request, "menu/catalog.html", context, status=page_status)


# ვაგროვებთ კალათის მონაცემებს და ვითვლით ჯამს.
def cart_state():
    # თითოეული კერძი შევინახოთ მისი ნომრის მიხედვით.
    """კითხულობს კალათას, აერთებს კერძების მონაცემებთან და ითვლის თანხასა და პორციებს."""
    catalog = {}
    for product in api.products():
        catalog[product["id"]] = product
    rows = []
    total = Decimal("0.00")
    count = 0
    for entry in api.basket():
        product = catalog.get(entry["productId"])
        # თუ კერძი კატალოგში აღარ არის, მის ფასს ვერ გამოვიცნობთ.
        if product is None:
            raise api.APIError("Basket product is not in the catalog")
        # ერთი კერძის საერთო თანხა = ერთეულის ფასი × პორციების რაოდენობა.
        subtotal = product["price"] * entry["quantity"]
        rows.append(
            {"product": product, "quantity": entry["quantity"], "subtotal": subtotal}
        )
        # += არსებულ ჯამს უმატებს ამ კერძის თანხას.
        total += subtotal
        count += entry["quantity"]
    return {"rows": rows, "total": total, "count": count}


# კალათის მონაცემებს გადავცემთ HTML გვერდს.
def cart(request):
    """კალათის მონაცემებს გადასცემს cart.html-ს; API-ის შეცდომაზე აჩვენებს შეტყობინებას."""
    try:
        state = cart_state()
        state["error"] = None
    except api.APIError:
        state = {"rows": [], "total": Decimal("0.00"), "count": 0, "error": ERROR}
    page_status = 200
    if state["error"]:
        page_status = 503
    return render(request, "menu/cart.html", state, status=page_status)


# ვაჩვენებთ შეტყობინებას და მომხმარებელს კალათის გვერდზე გადავიყვანთ.
def reply(request, error=None):
    """ინახავს შედეგის შეტყობინებას და გადამისამართებით ხსნის კალათის გვერდს."""
    if error:
        messages.error(request, error)
    else:
        messages.success(request, "კალათა განახლებულია.")
    # POST-ის შემდეგ GET-ზე გადასვლა გვერდის განახლებისას ფორმის ხელახალ გაგზავნას არ მოითხოვს.
    return redirect("menu:cart")


# დეკორატორი: მხოლოდ POST-ს უშვებს; ბმულის GET გახსნით კალათა ვერ შეიცვლება.
@require_POST
# კალათაში ახალი კერძის დამატება ან არსებულის რაოდენობის გაზრდა.
def add(request, product_id):
    """პირველი დამატებისას რაოდენობაა 1; განმეორებითი დამატება ზრდის მას ერთით."""
    try:
        product = find_product(product_id)
        if not product:
            return reply(request, "კერძი ვერ მოიძებნა.")
        existing = find_basket_item(product_id)
        quantity = 1
        if existing is not None:
            quantity = existing["quantity"] + 1
        if quantity > 99:
            return reply(request, "მაქსიმალური რაოდენობაა 99.")
        api.write_basket(product, quantity, existing is not None)
        return reply(request)
    except api.APIError:
        return reply(request, ERROR)


# დეკორატორი: მხოლოდ POST-ს უშვებს; ბმულის GET გახსნით კალათა ვერ შეიცვლება.
@require_POST
# ახალ რაოდენობას ვამოწმებთ და შემდეგ ვაგზავნით API-ში.
def update(request, product_id):
    """ფორმით მიღებულ რაოდენობას ამოწმებს და API-ში ინახავს."""
    # POST შეიცავს HTML ფორმის გამოგზავნილ quantity ველს.
    form = QuantityForm(request.POST)
    if not form.is_valid():
        return reply(request, "რაოდენობა უნდა იყოს მთელი რიცხვი 1-დან 99-მდე.")
    try:
        product = find_product(product_id)
        if product is None or find_basket_item(product_id) is None:
            return reply(request, "კერძი კალათაში ვერ მოიძებნა.")
        api.write_basket(product, form.cleaned_data["quantity"], True)
        return reply(request)
    except api.APIError:
        return reply(request, ERROR)


# დეკორატორი: მხოლოდ POST-ს უშვებს; ბმულის GET გახსნით კალათა ვერ შეიცვლება.
@require_POST
# API-დან ვშლით მითითებულ კერძს.
def remove(request, product_id):
    """კერძს შლის API-ის კალათიდან და მომხმარებელს კალათის გვერდზე აბრუნებს."""
    try:
        api.delete(product_id)
        return reply(request)
    except api.APIError:
        return reply(request, ERROR)


# პაროლის ველები მგრძნობიარეა; never_cache ავტორიზაციის გვერდის ქეშირებას კრძალავს.
@sensitive_post_parameters("password1", "password2")
@never_cache
@require_http_methods(["GET", "POST"])
# ვამოწმებთ რეგისტრაციის ფორმას და ვინახავთ მომხმარებელს.
def register(request):
    """GET-ზე აჩვენებს ცარიელ ფორმას; სწორ POST-ზე ქმნის მომხმარებელს და ავტორიზებულ სესიას."""
    if request.user.is_authenticated:
        return redirect("menu:catalog")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
    else:
        form = RegistrationForm()
    if request.method == "POST" and form.is_valid():
        # UserCreationForm პაროლს ჰეშავს და Django ORM-ით მომხმარებელს ინახავს.
        user = form.save()
        # სესია შემდეგ მოთხოვნებშიც ამოიცნობს ამ მომხმარებელს.
        auth_login(request, user)
        messages.success(request, "ანგარიში შექმნილია. კეთილი იყოს შენი მობრძანება!")
        return redirect("menu:catalog")
    return render(request, "menu/auth.html", {"form": form, "registering": True})
