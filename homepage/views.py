from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
from datetime import date, timedelta

from backend.models import ArxivPaper


def index(request):
    """
    The only page of the app!
    """
    return render(request, "homepage/index.html")


@require_GET
def papers_api(request):
    """
    API endpoint for papers. Either gets the most recent 50 or takes a query, 'q'
    """
    search_query = request.GET.get('q', '')
    date_filter = request.GET.get('d', '')
    try:
        start_item = int(request.GET.get('s', 0))
    except ValueError:
        return JsonResponse({'error': 'Invalid start item'}, status=400)

    if search_query:
        papers = ArxivPaper.objects.filter(
            Q(summary__icontains=search_query) |
            Q(abstract__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(authors__name__icontains=search_query)
        )
    else:
        papers = ArxivPaper.objects.all()

    if date_filter == 'today':
        today = date.today()
        start_of_period = today - timedelta(days=1.5)
        papers = papers.filter(publication_date__range=[start_of_period, today])
    elif date_filter == 'this-week':
        today = date.today()
        start_of_period = today - timedelta(days=6)
        papers = papers.filter(publication_date__range=[start_of_period, today])
    elif date_filter == 'this-month':
        today = date.today()
        start_of_period = today - timedelta(days=29)
        papers = papers.filter(publication_date__range=[start_of_period, today])
    elif date_filter == 'this-year':
        today = date.today()
        start_of_period = today - timedelta(days=364)
        papers = papers.filter(publication_date__range=[start_of_period, today])
    elif date_filter == 'forever':
        pass

    papers = papers.order_by('-publication_date').distinct()[start_item:start_item + 15]
    papers_data = []
    for paper in papers:
        try:
            paper_data = {
                'arxiv_id': paper.arxiv_id,
                'image_url': paper.images.first().image.url if paper.images.exists() else paper.screenshot.url,
                'title': paper.title,
                'summary': paper.summary,
                'first_author': paper.authors.first().name if paper.authors.exists() else '',
                'authors': [author.name for author in paper.authors.all()],
                'author_count': paper.authors.count(),
                'publication_date': paper.publication_date,
                'citations': paper.citations,
                'total_author_citations': paper.total_author_citations
            }
        except ValueError:
            # some papers may be in the DB but missing some information, for now we skip over them
            continue
        papers_data.append(paper_data)

    return JsonResponse(papers_data, safe=False)
