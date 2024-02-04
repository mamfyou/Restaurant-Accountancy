import os

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from openpyxl.reader.excel import load_workbook

from product.models import FinalProduct, FinalPriceHistory, SellPriceHistory, PrimaryIngredient, PriceHistory, Unit


def get_last_final_price(product):
    if FinalPriceHistory.objects.filter(final_product=product, sell_price__gt=0).first():
        return FinalPriceHistory.objects.filter(final_product=product, sell_price__gt=0).first().sell_price


def get_last_sell_price(product):
    if SellPriceHistory.objects.filter(final_product=product, sell_price__gt=0).first():
        return SellPriceHistory.objects.filter(final_product=product, sell_price__gt=0).first().sell_price


def get_profit(product):
    if (FinalPriceHistory.objects.filter(final_product=product,
                                         sell_price__gt=0).first() and
            SellPriceHistory.objects.filter(final_product=product, sell_price__gt=0).first()):
        return (FinalPriceHistory.objects.filter(final_product=product,
                                                 sell_price__gt=0).first().sell_price -
                SellPriceHistory.objects.filter(final_product=product, sell_price__gt=0).first().sell_price)


def create_data():
    data = pd.DataFrame({'محصولات': [product.name for product in FinalProduct.objects.all()],
                         'قیمت نهایی': [get_last_sell_price(product) for product in FinalProduct.objects.all()],
                         'قیمت داخل منو': [get_last_final_price(product) for product in FinalProduct.objects.all()],
                         'سود و ضرر': [get_profit(product) for product in FinalProduct.objects.all()]})
    return data


def import_from_excel(imported_file):
    try:
        wb = load_workbook(imported_file.path)
        ws = wb['Page 1']
        all_rows = list(ws.rows)
        for row in range(2, len(all_rows)):
            product_name = all_rows[row][1].value
            product_unit = all_rows[row][2].value
            product_unit_price = int(all_rows[row][3].value)
            if not PrimaryIngredient.objects.filter(name=product_name).exists():
                PrimaryIngredient.objects.create(name=product_name,
                                                 unit=Unit.objects.get_or_create(title=product_unit)[0])
            PriceHistory.objects.create(unit_price=product_unit_price,
                                        ingredient=PrimaryIngredient.objects.get(name=product_name))
    except ValidationError as v:
        raise ValidationError(v)
    except Exception as e:
        raise Exception('فایل اکسل وارد شده در فرمت درستی نمی باشد!')


def validate_excel(imported_file):
    try:
        name = default_storage.save(imported_file.name, imported_file)
        path = default_storage.path(name)

        wb = load_workbook(path)
        ws = wb['Page 1']
        all_rows = list(ws.rows)
        for row in range(2, len(all_rows)):
            product_name = all_rows[row][1].value
            product_unit = all_rows[row][2].value
            product_unit_price = int(all_rows[row][3].value)
        default_storage.delete(path)
    except Exception as e:
        try:
            default_storage.delete(path)
        except Exception:
            pass
        raise Exception('فایل اکسل وارد شده در فرمت درستی نمی باشد!')
