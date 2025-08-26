from rest_framework import serializers
from ..models import Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'author_id', 'is_approved', 'rank', 'activity_score', 'created_at']
