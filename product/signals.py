from django.db.models.signals import post_save
from django.dispatch import receiver

from product.models import PriceHistory, FinalProduct, SellPriceHistory


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
        price += int(float(PriceHistory.objects.filter(ingredient=i.base_ingredient).first().unit_price) * i.unit_amount)
    SellPriceHistory.objects.create(sell_price=price, final_product=instance)
