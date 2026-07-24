from django.contrib import admin
from .models import Bike

@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display  = ['bike_name','brand','year','fuel_type','engine_capacity_cc','kms_driven','price_usd']
    list_filter   = ['brand','fuel_type','year']
    search_fields = ['bike_name','brand']
    ordering      = ['-year','brand']

from .models import EmailVerification
admin.site.register(EmailVerification)
