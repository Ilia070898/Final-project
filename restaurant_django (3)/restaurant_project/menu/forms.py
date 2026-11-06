# ფორმების აღწერა და ვალიდაცია. კლასები მემკვიდრეობით იყენებს Django-ს მზა შემოწმებებს.
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model


# forms.Form მონაცემებს ამოწმებს, მაგრამ თავისით ბაზაში არაფერს ინახავს.
class FilterForm(forms.Form):
    # required=False ნიშნავს, რომ ველის შევსება აუცილებელი არ არის.
    categoryId = forms.ChoiceField(label="კატეგორია", required=False)
    # TypedChoiceField არჩეულ ტექსტს coerce=int-ით მთელ რიცხვად აქცევს.
    spiciness = forms.TypedChoiceField(
        label="სიცხარე",
        required=False,
        choices=[
            ("", "ნებისმიერი"),
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
        ],
        coerce=int,
        empty_value=None,
    )
    # არჩევანის წყვილში პირველია გასაგზავნი მნიშვნელობა, მეორე — ხილული წარწერა.
    nuts = forms.ChoiceField(
        label="ნიგოზი / თხილეული",
        required=False,
        choices=[("", "ყველა"), ("true", "შეიცავს"), ("false", "არ შეიცავს")],
    )
    # API იყენებს სწორედ ამ მართლწერას: vegeterian.
    vegeterian = forms.ChoiceField(
        label="ვეგეტარიანული",
        required=False,
        choices=[("", "ყველა"), ("true", "კი"), ("false", "არა")],
    )

    def __init__(self, *args, categories=(), **kwargs):
        """ფორმის შექმნისას ჯერ მშობლის ინიციალიზაციას ასრულებს, შემდეგ ჩვენს ველებს ამზადებს."""
        # *args და **kwargs მშობელ კლასს გადასცემს მიღებულ არგუმენტებს.
        super().__init__(*args, **kwargs)
        choices = [("", "ყველა კატეგორია")]
        for category in categories:
            choices.append((str(category["id"]), category["name"]))
        self.fields["categoryId"].choices = choices

    def api_params(self):
        """ამზადებს API-ის ფილტრების ლექსიკონს მხოლოდ შევსებული ველებით."""
        filters = {}
        for name, value in self.cleaned_data.items():
            # ცარიელ ფილტრს არ ვაგზავნით. ნული კი სიცხარის სწორი მნიშვნელობაა.
            if value != "" and value is not None:
                filters[name] = value
        return filters


# IntegerField უარყოფს ტექსტს, წილადს და 1–99 დიაპაზონის გარეთ რიცხვს.
class QuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99)


# მემკვიდრეობა: Django უკვე ამოწმებს სახელს, პაროლის სირთულესა და მის გამეორებას.
class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label="სახელი",
        max_length=150,
        widget=forms.TextInput(
            attrs={"autocomplete": "given-name", "placeholder": "შენი სახელი"}
        ),
    )
    email = forms.EmailField(
        label="ელფოსტა",
        widget=forms.EmailInput(
            attrs={"autocomplete": "email", "placeholder": "name@example.com"}
        ),
    )

    # Meta მიუთითებს, რომელ მოდელს უკავშირდება ფორმა და რომელი ველები ჩანს.
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("first_name", "username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        """ფორმის შექმნისას ჯერ მშობლის ინიციალიზაციას ასრულებს, შემდეგ ჩვენს ველებს ამზადებს."""
        # *args და **kwargs მშობელ კლასს გადასცემს მიღებულ არგუმენტებს.
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "მომხმარებლის სახელი"
        self.fields["username"].help_text = (
            "გამოიყენე ასოები, ციფრები ან @ . + - _ სიმბოლოები."
        )
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "username", "placeholder": "მაგალითად: guram"}
        )
        self.fields["password1"].label = "პაროლი"
        self.fields["password1"].help_text = (
            "მინიმუმ 8 სიმბოლო. მოერიდე გავრცელებულ, მხოლოდ ციფრებისგან შემდგარ ან პირადი მონაცემების მსგავს პაროლს."
        )
        self.fields["password2"].label = "გაიმეორე პაროლი"
        self.fields["password2"].help_text = "შეიყვანე იგივე პაროლი კიდევ ერთხელ."


# AuthenticationForm ამოწმებს სახელსა და პაროლს; ჩვენ ქართულ წარწერებს ვცვლით.
class SignInForm(AuthenticationForm):
    username = forms.CharField(
        label="მომხმარებლის სახელი",
        widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    password = forms.CharField(
        label="პაროლი",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    error_messages = {
        "invalid_login": "მომხმარებლის სახელი ან პაროლი არასწორია.",
        "inactive": "ეს ანგარიში არააქტიურია.",
    }
