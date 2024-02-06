import os

import pandas as pd
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from jalali_date import date2jalali

from RestaurantAccountancy import settings
from product.models import PriceHistory, FinalProduct, SellPriceHistory, Menu, MiddleIngredient
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


@receiver(post_save, sender=PriceHistory)
def update_final_product(sender, instance: PriceHistory, created, **kwargs):
    finals = FinalProduct.objects.filter(ingredients__base_ingredient=instance.ingredient)
    if finals.exists():
        for final in finals:
            price = 0
            for i in final.ingredients.all():
                price += int(
                    float(PriceHistory.objects.filter(ingredient=i.base_ingredient).order_by(
                        '-created_at').first().unit_price) * i.unit_amount)
            if price > 0:
                SellPriceHistory.objects.create(sell_price=price, final_product=final)


@receiver(m2m_changed, sender=FinalProduct.ingredients.through)
def update_prices(sender, instance, action, **kwargs):
    if action in ['post_add']:
        price = 0
        for i in instance.ingredients.all():
            price += int(
                float(PriceHistory.objects.filter(ingredient=i.base_ingredient).first().unit_price) * i.unit_amount)
        SellPriceHistory.objects.create(sell_price=price, final_product=instance)


@receiver(post_save, sender=Menu)
def export_data(sender, instance, created, **kwargs):
    if instance.imported_file:
        import_from_excel(instance.imported_file)

    path = os.path.join(settings.MEDIA_ROOT, f'menu_{str(date2jalali(instance.created_at.date()))}.xlsx')

    with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
        cell_format = writer.book.add_format(
            {
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True,
                'font_size': 12,
                'font_name': 'B Nazanin',
                'num_format': '#,##0'
            })

        # Write data for each FinalProduct starting from the first sheet
        for i, product in enumerate(FinalProduct.objects.all()):
            data = create_data(product)
            sheet_name = f'{product.name}' if i == 0 else f'{product.name}_{i}'
            data.to_excel(writer, index=False, sheet_name=sheet_name)
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(data.columns):
                max_len = max(data[col].astype(str).apply(len).max(), len(col))
                worksheet.set_column(idx, idx, max_len + 2, cell_format)

    Menu.objects.filter(id=instance.id).update(file=path.split(settings.MEDIA_ROOT)[1])
