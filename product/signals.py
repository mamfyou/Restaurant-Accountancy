import os

import pandas as pd
from django.core.exceptions import ValidationError

from django.db.models.signals import post_save
from django.dispatch import receiver
from jalali_date import date2jalali
from openpyxl.reader.excel import load_workbook

from RestaurantAccountancy import settings
from product.models import PriceHistory, FinalProduct, SellPriceHistory, Menu, PrimaryIngredient
from utils.utils import create_data, import_from_excel


@receiver(post_save, sender=PriceHistory)
def update_middle_ingredient_prices(sender, instance, created, **kwargs):
    from product.models import PrimaryIngredient
    if instance.signal_involved:
        ingredient: PrimaryIngredient = instance.ingredient
        if ingredient.middle_ingredients.exists():
            for i in ingredient.middle_ingredients.all():
                if i.related_ingredient.exists():
                    for r in i.related_ingredient.all():
                        PriceHistory.objects.create(ingredient=r, signal_involved=False,
                                                    unit_price=int(float(instance.unit_price) * i.unit_amount))


@receiver(post_save, sender=FinalProduct)
def update_prices(sender, instance, created, **kwargs):
    price = 0
    for i in instance.ingredients.all():
        price += int(
            float(PriceHistory.objects.filter(ingredient=i.base_ingredient).first().unit_price) * i.unit_amount)
    SellPriceHistory.objects.create(sell_price=price, final_product=instance)



@receiver(post_save, sender=Menu)
def export_data(sender, instance, created, **kwargs):
    if instance.imported_file:
        import_from_excel(instance.imported_file)
    data = create_data()
    path = os.path.join(settings.MEDIA_ROOT, f'menu_{str(date2jalali(instance.created_at.date()))}.xlsx')

    data_to_excel = pd.ExcelWriter(path)
    data.to_excel(data_to_excel, sheet_name='قیمت محصولات')

    # workbook = data_to_excel.book
    # worksheet = data_to_excel.sheets['قیمت محصولات']
    # format_right_to_left = workbook.add_format({'reading_order': 2})
    # worksheet.right_to_left()

    data_to_excel.close()

    Menu.objects.filter(id=instance.id).update(file=path.split(settings.MEDIA_ROOT)[1])
