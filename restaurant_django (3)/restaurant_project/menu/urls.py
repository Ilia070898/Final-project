# როუტინგი: URL მისამართს უკავშირებს მის დამმუშავებელ ფუნქციას ან Django-ს მზა კლასს.
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from .forms import SignInForm

# namespace გვაძლევს საშუალებას შაბლონში გამოვიყენოთ menu:cart და მსგავსი სახელები.
app_name = "menu"
# path-ის პირველი არგუმენტი მისამართია, მეორე — დამმუშავებელი, name — მოკლე სახელი.
urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        # მზა class-based view ფორმას აჩვენებს და შესვლის მოთხოვნას ამუშავებს.
        LoginView.as_view(
            template_name="menu/auth.html",
            authentication_form=SignInForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", views.catalog, name="catalog"),
    path("cart/", views.cart, name="cart"),
    # <int:product_id> მისამართიდან რიცხვს იღებს და ფუნქციას არგუმენტად გადასცემს.
    path("cart/add/<int:product_id>/", views.add, name="add"),
    path("cart/update/<int:product_id>/", views.update, name="update"),
    path("cart/remove/<int:product_id>/", views.remove, name="remove"),
]
