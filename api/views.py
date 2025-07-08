from django.utils.timezone import localtime
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from company_news.models import Company, Industry, CompanyIndustryGroup, Article
from .serializers import NewsSerializer, ArticleSerializer
from .utils import get_news

@api_view(['POST'])
def find_company_news(request):
    company_name = request.data.get('CompanyName')
    company_website = request.data.get('CompanyWebsite')
    searched_industry = request.data.get('SearchedIndustry')

    if not company_name or not company_website or not searched_industry:
        return Response({"error": "Missing parameters"}, status=400)

    final_news = get_news(company_website, searched_industry, company_name)

    serializer = NewsSerializer(final_news, many=True)

    return Response(serializer.data)

@api_view(['GET'])
def get_company_news(request):
    company_name = request.GET.get('CompanyName')
    industry_name = request.GET.get('SearchedIndustry')

    if not company_name or not industry_name:
        return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        company = Company.objects.get(name__iexact=company_name)
        industry = Industry.objects.get(name__iexact=industry_name)
        group = CompanyIndustryGroup.objects.get(company=company, industry=industry)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
    except Industry.DoesNotExist:
        return Response({'error': 'Industry not found'}, status=status.HTTP_404_NOT_FOUND)
    except CompanyIndustryGroup.DoesNotExist:
        return Response([], status=status.HTTP_200_OK)

    articles = Article.objects.filter(group=group).order_by('-publication_date')[:9]
    serializer = ArticleSerializer(articles, many=True)

    last_updated_iso = localtime(group.last_updated).isoformat() if group.last_updated else None

    return Response({
        'articles': serializer.data,
        'last_updated': last_updated_iso
    })