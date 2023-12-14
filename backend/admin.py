from django.contrib import admin

from .models import ArxivPaper, Author, Subject, PaperImage, PaperSource


class ArxivPaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'citations', 'total_author_citations', 'summary', 'publication_date', 'arxiv_id',
                    'created_at')
    search_fields = ('title', 'abstract', 'arxiv_id')
    readonly_fields = ('created_at', 'modified_at')
    ordering = ('-publication_date',)
    list_filter = ('publication_date', 'created_at', 'citations', 'total_author_citations')


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'full_name')
    search_fields = ('short_name', 'full_name')
    ordering = ('short_name',)


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'affiliation', 'email', 'email_domain', 'citations', 'scholar_id')
    search_fields = ('name', 'affiliation', 'email', 'email_domain', 'citations', 'scholar_id')
    ordering = ('name',)


class PaperImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'paper')
    search_fields = ('image', 'paper')
    ordering = ('image',)


class PaperSourceAdmin(admin.ModelAdmin):
    list_display = ('paper',)
    search_fields = ('paper',)


admin.site.register(ArxivPaper, ArxivPaperAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(PaperImage, PaperImageAdmin)
admin.site.register(PaperSource, PaperSourceAdmin)
