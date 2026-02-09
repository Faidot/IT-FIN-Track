"""
URL configuration for the core app.
"""

from django.urls import path
from core.views import dashboard as dashboard_views
from core.views import auth as auth_views
from core.views import income as income_views
from core.views import income_source as income_source_views
from core.views import expense as expense_views
from core.views import vendor as vendor_views
from core.views import category as category_views
from core.views import reports as reports_views
from core.views import payment_tracker as payment_tracker_views
from core.views import user as user_views
from core.views import bills as bills_views
from core.views import roles as role_views

app_name = 'core'

urlpatterns = [
    # Authentication
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.profile_view, name='profile'),
    path('profile/change-password/', auth_views.change_password_view, name='change_password'),
    
    # Dashboard
    path('', dashboard_views.dashboard, name='dashboard'),
    
    # Payment Tracker (unified ledger view)
    path('payment-tracker/', payment_tracker_views.payment_tracker, name='payment_tracker'),
    
    # User Management (admin only)
    path('users/', user_views.user_list, name='user_list'),
    path('users/add/', user_views.user_create, name='user_create'),
    path('users/<int:pk>/', user_views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', user_views.user_edit, name='user_edit'),
    path('users/<int:pk>/reset-password/', user_views.user_reset_password, name='user_reset_password'),
    path('users/<int:pk>/toggle-status/', user_views.user_toggle_status, name='user_toggle_status'),
    
    # Role Management (admin only)
    path('roles/', role_views.role_list, name='role_list'),
    path('roles/add/', role_views.role_create, name='role_create'),
    path('roles/<int:pk>/', role_views.role_detail, name='role_detail'),
    path('roles/<int:pk>/edit/', role_views.role_edit, name='role_edit'),
    path('roles/<int:pk>/delete/', role_views.role_delete, name='role_delete'),
    
    # Income Sources (like Vendor for Expenses)
    path('income-sources/', income_source_views.income_source_list, name='income_source_list'),
    path('income-sources/add/', income_source_views.income_source_create, name='income_source_create'),
    path('income-sources/<int:pk>/', income_source_views.income_source_detail, name='income_source_detail'),
    path('income-sources/<int:pk>/edit/', income_source_views.income_source_edit, name='income_source_edit'),
    path('income-sources/<int:pk>/delete/', income_source_views.income_source_delete, name='income_source_delete'),
    
    # Income
    path('income/', income_views.income_list, name='income_list'),
    path('income/add/', income_views.income_create, name='income_create'),
    path('income/<int:pk>/', income_views.income_detail, name='income_detail'),
    path('income/<int:pk>/edit/', income_views.income_edit, name='income_edit'),
    path('income/<int:pk>/delete/', income_views.income_delete, name='income_delete'),
    
    # Expense
    path('expenses/', expense_views.expense_list, name='expense_list'),
    path('expenses/add/', expense_views.expense_create, name='expense_create'),
    path('expenses/batch/', expense_views.expense_batch_create, name='expense_batch_create'),
    path('expenses/<int:pk>/', expense_views.expense_detail, name='expense_detail'),
    path('expenses/<int:pk>/edit/', expense_views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', expense_views.expense_delete, name='expense_delete'),
    path('expenses/<int:pk>/approve/', expense_views.expense_approve, name='expense_approve'),
    path('expenses/<int:pk>/reject/', expense_views.expense_reject, name='expense_reject'),
    path('expense-bills/<int:pk>/delete/', expense_views.bill_delete, name='expense_bill_delete'),
    
    # Recurring Bills
    path('recurring-bills/', bills_views.bill_list, name='recurring_bill_list'),
    path('recurring-bills/add/', bills_views.bill_create, name='recurring_bill_create'),
    path('recurring-bills/<int:pk>/', bills_views.bill_detail, name='recurring_bill_detail'),
    path('recurring-bills/<int:pk>/edit/', bills_views.bill_edit, name='recurring_bill_edit'),
    path('recurring-bills/<int:pk>/delete/', bills_views.bill_delete, name='recurring_bill_delete'),
    path('recurring-bills/<int:pk>/pay/', bills_views.bill_pay, name='recurring_bill_pay'),
    path('recurring-bills/<int:pk>/generate/', bills_views.bill_generate_payment, name='recurring_bill_generate'),
    path('recurring-bills/month-detail/', bills_views.month_detail, name='recurring_bill_month_detail'),

    
    # Vendors
    path('vendors/', vendor_views.vendor_list, name='vendor_list'),
    path('vendors/add/', vendor_views.vendor_create, name='vendor_create'),
    path('vendors/<int:pk>/', vendor_views.vendor_detail, name='vendor_detail'),
    path('vendors/<int:pk>/edit/', vendor_views.vendor_edit, name='vendor_edit'),
    path('vendors/<int:pk>/delete/', vendor_views.vendor_delete, name='vendor_delete'),
    
    # Categories
    path('categories/', category_views.category_list, name='category_list'),
    path('categories/add/', category_views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', category_views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', category_views.category_delete, name='category_delete'),
    
    # Reports
    path('reports/', reports_views.report_dashboard, name='report_dashboard'),
    path('reports/monthly-expense/', reports_views.monthly_expense_report, name='monthly_expense_report'),
    path('reports/income-expense/', reports_views.income_expense_statement, name='income_expense_statement'),
    path('reports/reimbursement/', reports_views.reimbursement_report, name='reimbursement_report'),
    path('reports/account-balance/', reports_views.account_balance_report, name='account_balance_report'),
    path('reports/audit-trail/', reports_views.audit_trail, name='audit_trail'),
    path('reports/export/<str:report_type>/', reports_views.export_excel, name='export_excel'),
]


