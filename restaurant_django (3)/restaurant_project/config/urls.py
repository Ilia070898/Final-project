# პროექტის მთავარი URL სია. include გადასცემს მისამართების დამუშავებას menu აპს.
from django.urls import include, path

urlpatterns = [path("", include("menu.urls"))]
