from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from utils.base_models import BaseModel
from jalali_date import date2jalali


class Unit(BaseModel):
    title = models.CharField(max_length=20, verbose_name='واحد')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'واحد'
        verbose_name_plural = 'واحد ها'

class PrimaryIngredient(BaseModel):
    name = models.CharField(max_length=250, verbose_name='نام')
    unit = models.ForeignKey(Unit, related_name='ingredients', on_delete=models.SET_NULL, null=True, verbose_name='واحد')
    related_ingredient = models.ManyToManyField('MiddleIngredient', verbose_name='ماده اولیه مرتبط', null=True,
                                                blank=True, related_name='related_ingredient')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'محصول اولیه'
        verbose_name_plural = 'محصولات اولیه'


class PriceHistory(BaseModel):
    unit_price = models.CharField(max_length=200, verbose_name='قیمت واحد')
    ingredient = models.ForeignKey(PrimaryIngredient, related_name='price_history', verbose_name='ماده اولیه',
                                   on_delete=models.CASCADE)
    signal_involved = models.BooleanField(default=True)

    def __str__(self):
        return str(
            date2jalali(self.created_at.date())) + ' : ' + self.ingredient.name + ' -> ' + self.unit_price + ' تومان'

    class Meta:
        verbose_name = 'تاریخچه قیمت'
        verbose_name_plural = 'تاریخچه قیمت ها'


class MiddleIngredient(BaseModel):
    class TypeChoices(models.TextChoices):
        PRIMARY = 'p', 'محصول اولیه'
        FINAL = 'f', 'محصول نهایی'

    unit_amount = models.FloatField(verbose_name='نسبت مورد نیاز(عددی اعشاری بین ۰ و ۱ وارد کنید)', validators=[
        MinValueValidator(0), MaxValueValidator(1)
    ])
    base_ingredient = models.ForeignKey(verbose_name='ماده اولیه', to=PrimaryIngredient, on_delete=models.CASCADE,
                                        related_name='middle_ingredients')
    type = models.CharField(max_length=15, choices=TypeChoices.choices, default=TypeChoices.PRIMARY, verbose_name='نوع محصول مرتبط شده')

    def __str__(self):
        return self.base_ingredient.name + ' : ' + ' ' + str(self.unit_amount) + ' ' + self.base_ingredient.unit.title

    def clean(self):
        print(self.__dict__)
        if self.base_ingredient.related_ingredient.exists() and self.type == self.TypeChoices.PRIMARY:
            raise ValidationError('در حال حاضر نمیتوانید محصول میانی که دارای محصول میانی است اضافه کنید')

    class Meta:
        verbose_name = 'محصول میانی'
        verbose_name_plural = 'محصولات میانی'


class FinalProduct(BaseModel):
    name = models.CharField(max_length=200, verbose_name='نام')
    ingredients = models.ManyToManyField(MiddleIngredient, related_name='final_products',
                                         verbose_name='مواد اولیه مورد نیاز')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'محصول نهایی'
        verbose_name_plural = 'محصولات نهایی'


class FinalPriceHistory(BaseModel):
    sell_price = models.PositiveIntegerField(verbose_name='قیمت داخل منو')
    final_product = models.ForeignKey(FinalProduct, related_name='final_prices', on_delete=models.CASCADE,
                                      verbose_name='محصول نهایی')

    class Meta:
        verbose_name = 'تاریخچه قیمت داخل منو'
        verbose_name_plural = 'تاریخچه قیمت های داخل منو'


class SellPriceHistory(BaseModel):
    sell_price = models.PositiveIntegerField(verbose_name='قیمت نهایی')
    final_product = models.ForeignKey(FinalProduct, related_name='sell_prices', on_delete=models.CASCADE,
                                      verbose_name='محصول نهایی')

    def __str__(self):
        return str(date2jalali(self.created_at.date()))

    class Meta:
        verbose_name = 'تاریخچه قیمت نهایی'
        verbose_name_plural = 'تاریخجه قیمت های نهایی'


class Menu(BaseModel):
    file = models.FileField(verbose_name='فایل خروجی گرفته شده', null=True, blank=True, editable=False)
    imported_file = models.FileField(verbose_name='فایل ورودی قیمت ها', null=True, blank=True)

    def __str__(self):
        return str(date2jalali(self.created_at.date()))

    class Meta:
        verbose_name = 'منو'
        verbose_name_plural = 'منو ها'
