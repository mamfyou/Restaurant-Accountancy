import pandas as pd

from product.models import FinalProduct, FinalPriceHistory, SellPriceHistory


def get_last_final_price(product):
    if FinalPriceHistory.objects.filter(final_product=product).first():
        return FinalPriceHistory.objects.filter(final_product=product, sell_price__gt=0).first().sell_price


def get_last_sell_price(product):
    if SellPriceHistory.objects.filter(final_product=product).first():
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
