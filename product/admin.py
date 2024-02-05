import datetime

from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from jalali_date import date2jalali

from utils.utils import import_from_excel, validate_excel, format_number, get_color
from .models import PrimaryIngredient, MiddleIngredient, FinalProduct, PriceHistory, SellPriceHistory, \
    FinalPriceHistory, Menu


class PriceHistoryInLine(admin.StackedInline):
    model = PriceHistory
    extra = 0
    ordering = ['-created_at']
    fields = ('unit_price', 'get_unit_price')
    readonly_fields = ('get_unit_price',)

    def get_unit_price(self, obj):
        return format_number(obj.unit_price)

    get_unit_price.short_description = 'قیمت'

    def has_change_permission(self, request, obj=None):
        return False


class MiddleIngredientInLine(admin.TabularInline):
    model = MiddleIngredient
    extra = 0


class PrimaryIngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_last_price']
    inlines = [PriceHistoryInLine]
    autocomplete_fields = ('related_ingredient',)

    def get_last_price(self, obj):
        return format_number((int(obj.price_history.first().unit_price))) if obj.price_history.exists() else None

    get_last_price.short_description = 'آخرین قیمت'
    search_fields = ['name']

    def calculate_final_price(self, middle_ingredients: [MiddleIngredient]):
        price = 0
        for i in middle_ingredients:
            price += int(
                float(PriceHistory.objects.filter(ingredient=i.base_ingredient).first().unit_price) * i.unit_amount)
        return price

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['related_ingredient']
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        form.cleaned_data.pop('price_history', None)
        super().save_model(request, obj, form, change)
        print(form.cleaned_data)
        if form.cleaned_data.get('related_ingredient'):
            price = self.calculate_final_price(form.cleaned_data['related_ingredient'])
            PriceHistory.objects.create(ingredient=obj, unit_price=price)


class MiddleIngredientAdminForm(forms.ModelForm):
    class Meta:
        model = MiddleIngredient
        fields = '__all__'


class MiddleIngredientAdmin(admin.ModelAdmin):
    autocomplete_fields = ['base_ingredient']
    form = MiddleIngredientAdminForm
    search_fields = ('base_ingredient__name',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['type'].initial = 'f'
        return form


class SellPriceHistoryInLine(admin.StackedInline):
    model = SellPriceHistory
    extra = 0
    ordering = ['-created_at']
    fields = ('sell_price', 'get_sell_price')
    readonly_fields = ('get_sell_price',)

    def get_sell_price(self, obj):
        return format_number(obj.sell_price)

    get_sell_price.short_description = 'قیمت نهایی'

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class FinalPriceHistoryInLine(admin.StackedInline):
    model = FinalPriceHistory
    extra = 0
    ordering = ['-created_at']
    fields = ('sell_price', 'get_sell_price')
    readonly_fields = ('get_sell_price',)

    def get_sell_price(self, obj):
        return format_number(obj.sell_price)

    get_sell_price.short_description = 'قیمت ثبت شده در منو'

    def has_change_permission(self, request, obj=None):
        return False


class FinalProductAdmin(admin.ModelAdmin):
    inlines = [SellPriceHistoryInLine, FinalPriceHistoryInLine]
    list_display = ('name', 'get_last_sell_price', 'get_last_final_price', 'get_profit')
    search_fields = ('name',)
    autocomplete_fields = ('ingredients',)

    def get_last_final_price(self, obj):
        if FinalPriceHistory.objects.filter(final_product=obj, sell_price__gt=0).first():
            return format_number(
                FinalPriceHistory.objects.filter(final_product=obj, sell_price__gt=0).first().sell_price)

    def get_last_sell_price(self, obj):
        if SellPriceHistory.objects.filter(final_product=obj, sell_price__gt=0).first():
            return format_number(
                SellPriceHistory.objects.filter(final_product=obj, sell_price__gt=0).first().sell_price)

    def get_profit(self, obj):
        final_price_history_qs = FinalPriceHistory.objects.filter(final_product=obj, sell_price__gt=0)
        sell_price_history_qs = SellPriceHistory.objects.filter(final_product=obj, sell_price__gt=0)
        if final_price_history_qs.exists() and sell_price_history_qs.exists():
            profit = final_price_history_qs.first().sell_price - sell_price_history_qs.first().sell_price
            color = get_color(profit)
            return format_html('<span style="color:{};">{}</span>', color, format_number(profit))

    get_last_final_price.short_description = 'قیمت ثبت شده در منو'
    get_last_sell_price.short_description = 'قیمت محاسبه شده'
    get_profit.short_description = 'سود محاسبه شده'


class PriceHistoryAdmin(admin.ModelAdmin):
    fields = ('unit_price', 'ingredient' 'get_unit_price')
    readonly_fields = ('ingredient', 'get_unit_price')
    search_fields = ('ingredient__name', 'unit_price')
    list_filter = ('created_at',)
    list_display = ('get_date', 'ingredient', 'get_unit_price')

    def get_date(self, obj):
        return date2jalali(obj.created_at.date())

    get_date.short_description = 'تاریخ'

    def get_unit_price(self, obj):
        return format_number(obj.unit_price)

    def has_change_permission(self, request, obj=None):
        return False


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = '__all__'

    def clean(self):
        print(self.cleaned_data)
        excel_file = self.cleaned_data.get('imported_file')
        if excel_file:
            try:
                validate_excel(excel_file)
            except Exception as e:
                raise ValidationError(e)
        super().clean()


class MenuAdmin(admin.ModelAdmin):
    readonly_fields = ('file',)
    list_filter = ('created_at',)
    form = MenuForm


class SellPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'get_final_price', 'get_sell_price', 'get_profit', 'get_date')
    fields = ('get_name', 'get_final_price', 'sell_price', 'get_profit', 'get_date')
    readonly_fields = ('get_name', 'get_final_price', 'get_profit', 'sell_price', 'get_date', 'get_sell_price')
    list_filter = ('created_at',)
    search_fields = ('final_product__name',)

    @admin.display(description='نام')
    def get_name(self, obj):
        return obj.final_product.name

    @admin.display(description='تاریخ')
    def get_date(self, obj):
        return date2jalali(obj.created_at.date())

    @admin.display(description='قیمت داخل منو')
    def get_final_price(self, obj):
        final_price_queryset = FinalPriceHistory.objects.filter(final_product=obj.final_product,
                                                                created_at__lte=obj.created_at + datetime.timedelta(
                                                                    seconds=3))
        if final_price_queryset.first():
            return format_number(final_price_queryset.first().sell_price)

    def get_sell_price(self, obj):
        return format_number(obj.sell_price)

    @admin.display(description='سود و ضرر')
    def get_profit(self, obj):
        final_price_queryset = FinalPriceHistory.objects.filter(final_product=obj.final_product,
                                                                sell_price__gt=0,
                                                                created_at__lte=obj.created_at + datetime.timedelta(
                                                                    seconds=3))

        if final_price_queryset:
            profit = final_price_queryset.first().sell_price - obj.sell_price
            color = get_color(profit)
            return format_html('<span style="color:{};">{}</span>', color, format_number(profit))

    def has_add_permission(self, request):
        return False


admin.site.register(PrimaryIngredient, PrimaryIngredientAdmin)
admin.site.register(MiddleIngredient, MiddleIngredientAdmin)
admin.site.register(FinalProduct, FinalProductAdmin)
admin.site.register(PriceHistory, PriceHistoryAdmin)
admin.site.register(SellPriceHistory, SellPriceHistoryAdmin)
admin.site.register(Menu, MenuAdmin)
