from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from django.http import HttpResponse
import csv
from .models import PortfolioItem, Category, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'item_count', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def item_count(self, obj):
        return obj.portfolioitem_set.count()
    item_count.short_description = 'Items Count'

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'status', 'is_featured', 'views_count', 'file_preview', 'created_at', 'description_preview')
    list_filter = ('status', 'is_featured', 'category', 'created_at', 'user__role', 'user')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'views_count', 'file_preview')
    list_editable = ('status', 'is_featured')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'user', 'category')
        }),
        ('File Information', {
            'fields': ('file', 'file_preview')
        }),
        ('Status & Settings', {
            'fields': ('status', 'is_featured', 'views_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_items', 'reject_items', 'feature_items', 'unfeature_items', 'export_portfolio_data', 'reset_views']
    
    def file_preview(self, obj):
        """Display file preview in admin list"""
        if obj.file:
            if obj.file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                return format_html(
                    '<img src="{}" style="max-width: 50px; max-height: 50px;" />',
                    obj.file.url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank">📄 {}</a>',
                    obj.file.url,
                    obj.file.name.split('/')[-1]
                )
        return "No file"
    file_preview.short_description = 'File Preview'
    
    def description_preview(self, obj):
        """Show truncated description in list view"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return "No description"
    description_preview.short_description = 'Description'
    
    def get_queryset(self, request):
        """Optimize queries by selecting related user data"""
        return super().get_queryset(request).select_related('user', 'category')
    
    def save_model(self, request, obj, form, change):
        """Set user automatically if not set"""
        if not obj.user and not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    # Custom actions
    def approve_items(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} portfolio items have been approved.')
    approve_items.short_description = "Approve selected items"
    
    def reject_items(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} portfolio items have been rejected.')
    reject_items.short_description = "Reject selected items"
    
    def feature_items(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} portfolio items have been featured.')
    feature_items.short_description = "Feature selected items"
    
    def unfeature_items(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} portfolio items have been unfeatured.')
    unfeature_items.short_description = "Unfeature selected items"
    
    def reset_views(self, request, queryset):
        updated = queryset.update(views_count=0)
        self.message_user(request, f'{updated} portfolio items have had their view counts reset.')
    reset_views.short_description = "Reset view counts"
    
    def export_portfolio_data(self, request, queryset):
        """Export portfolio data to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="portfolio_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'User', 'Category', 'Status', 'Featured', 'Views', 'Description', 'File', 'Created At'])
        
        for item in queryset:
            writer.writerow([
                item.title,
                item.user.username,
                item.category.name if item.category else '',
                item.status,
                'Yes' if item.is_featured else 'No',
                item.views_count,
                item.description,
                item.file.name if item.file else '',
                item.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_portfolio_data.short_description = "Export selected items to CSV"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('portfolio_item', 'user', 'content_preview', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at', 'user__role')
    search_fields = ('content', 'user__username', 'portfolio_item__title')
    ordering = ('-created_at',)
    list_editable = ('is_approved',)
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('portfolio_item', 'user', 'content')
        }),
        ('Moderation', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_comments', 'reject_comments', 'export_comments']
    
    def content_preview(self, obj):
        """Show truncated content in list view"""
        if obj.content:
            return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
        return "No content"
    content_preview.short_description = 'Content'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments have been approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments have been rejected.')
    reject_comments.short_description = "Reject selected comments"
    
    def export_comments(self, request, queryset):
        """Export comments data to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="comments_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Portfolio Item', 'User', 'Content', 'Approved', 'Created At'])
        
        for comment in queryset:
            writer.writerow([
                comment.portfolio_item.title,
                comment.user.username,
                comment.content,
                'Yes' if comment.is_approved else 'No',
                comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_comments.short_description = "Export selected comments to CSV"
