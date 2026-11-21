from django.contrib import admin

from .models import Agent, AgentReferral


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'number', 'company_name', 'referral_code', 'created_at')
    search_fields = ('name', 'code', 'number', 'company_name', 'referral_code')
    readonly_fields = ('referral_code', 'created_at', 'updated_at')


@admin.register(AgentReferral)
class AgentReferralAdmin(admin.ModelAdmin):
    list_display = ('mail_id', 'agent', 'created_at')
    list_filter = ('agent',)
    search_fields = ('mail_id', 'agent__name', 'agent__referral_code')
    readonly_fields = ('created_at',)
