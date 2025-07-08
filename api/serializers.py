from rest_framework import serializers

from company_news.models import MainTopic, Article


class PersonMentionedSerializer(serializers.Serializer):
    name = serializers.CharField()
    role = serializers.CharField()


class NewsSerializer(serializers.Serializer):
    title = serializers.CharField()
    url = serializers.URLField()
    author = serializers.CharField(allow_blank=True)
    publication_date = serializers.CharField(allow_blank=True)
    summary = serializers.CharField()
    main_topics = serializers.ListField(
        child=serializers.CharField(), allow_empty=True
    )



class MainTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainTopic
        fields = ['topic']

class ArticleSerializer(serializers.ModelSerializer):
    main_topics = MainTopicSerializer(many=True, source='topic_set')

    class Meta:
        model = Article
        fields = ['title', 'url', 'author', 'publication_date', 'summary', 'main_topics']