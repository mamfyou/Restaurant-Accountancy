from django.contrib import admin
from django import forms

from .models import PrimaryIngredient, MiddleIngredient, FinalProduct, PriceHistory, SellPriceHistory, FinalPriceHistory


class PriceHistoryInLine(admin.StackedInline):
    model = PriceHistory
    extra = 0


class MiddleIngredientInLine(admin.TabularInline):
    model = MiddleIngredient
    extra = 0


class PrimaryIngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_last_price']
    inlines = [PriceHistoryInLine]

    def get_last_price(self, obj):
        return obj.price_history.first().unit_price if obj.price_history.exists() else None

    get_last_price.short_description = 'آخرین قیمت'
    search_fields = ['name']

    def calculate_final_price(self, middle_ingredients: [MiddleIngredient]):
        price = 0
        for i in middle_ingredients:
            price += int(
                float(PriceHistory.objects.filter(ingredient=i.base_ingredient).first().unit_price) * i.unit_amount)
        return price

    def save_model(self, request, obj, form, change):
        print(form.cleaned_data)
        if form.cleaned_data.get('related_ingredient'):
            form.cleaned_data.pop('price_history', None)
            price = self.calculate_final_price(form.cleaned_data['related_ingredient'])
            PriceHistory.objects.create(ingredient=obj, unit_price=price)
        return super().save_model(request, obj, form, change)


class MiddleIngredientAdminForm(forms.ModelForm):
    class Meta:
        model = MiddleIngredient
        fields = '__all__'


class MiddleIngredientAdmin(admin.ModelAdmin):
    autocomplete_fields = ['base_ingredient']
    form = MiddleIngredientAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Set the default value for the 'type' field
        form.base_fields['type'].initial = 'f'
        return form


class SellPriceHistoryInLine(admin.StackedInline):
    model = SellPriceHistory
    extra = 0


class FinalPriceHistoryInLine(admin.StackedInline):
    model = FinalPriceHistory
    extra = 0


class FinalProductAdmin(admin.ModelAdmin):
    inlines = [SellPriceHistoryInLine, FinalPriceHistoryInLine]
    list_display = ('name', 'get_last_sell_price', 'get_last_final_price', 'get_profit')

    def get_last_final_price(self, obj):
        if FinalPriceHistory.objects.filter(final_product=obj).first():
            return FinalPriceHistory.objects.filter(final_product=obj, sell_price__gt=0).first().sell_price

    def get_last_sell_price(self, obj):
        if SellPriceHistory.objects.filter(final_product=obj).first():
            return SellPriceHistory.objects.filter(final_product=obj, sell_price__gt=0).first().sell_price

    def get_profit(self, obj):
        if (FinalPriceHistory.objects.filter(final_product=obj,
                                             sell_price__gt=0).first() and
                SellPriceHistory.objects.filter(final_product=obj, sell_price__gt=0).first()):
            return (FinalPriceHistory.objects.filter(final_product=obj,
                                                     sell_price__gt=0).first().sell_price -
                    SellPriceHistory.objects.filter(final_product=obj, sell_price__gt=0).first().sell_price)

    get_last_final_price.short_description = 'قیمت ثبت شده در منو'
    get_last_sell_price.short_description = 'قیمت محاسبه شده'
    get_profit.short_description = 'سود محاسبه شده'


class PriceHistoryAdmin(admin.ModelAdmin):
    fields = ('unit_price', 'ingredient')
    readonly_fields = ('ingredient',)


admin.site.register(PrimaryIngredient, PrimaryIngredientAdmin)
admin.site.register(MiddleIngredient, MiddleIngredientAdmin)
admin.site.register(FinalProduct, FinalProductAdmin)
admin.site.register(PriceHistory, PriceHistoryAdmin)
admin.site.register(SellPriceHistory)
