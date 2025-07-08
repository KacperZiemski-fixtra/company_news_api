from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField()

class Industry(models.Model):
    name = models.CharField(max_length=55)

class IndustrySources(models.Model):
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    source = models.CharField(max_length=255)

class IndustryKeywords(models.Model):
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=30)

class CompanyIndustryGroup(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'industry')

class Article(models.Model):
    group = models.ForeignKey(CompanyIndustryGroup, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    url = models.URLField()
    author = models.CharField(max_length=255, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    summary = models.TextField()

class MainTopic(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    topic = models.TextField()
