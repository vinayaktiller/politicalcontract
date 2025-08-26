from django.core.management.base import BaseCommand
from blog_related.models import Question

class Command(BaseCommand):
    help = 'Populate predefined private funding system questions'

    questions_texts = [
        "What is private funding system?",
        "Why private funding system is bad?",
        "Why private funding system leads to corruption?",
        "Why private funding system leads to political inequality?",
        "Why private funding system leads to caste inequality?",
        "Why private funding system leads to gender inequality?",
        "Why private funding system leads to chamchagiri?",
        "How private funding system kills democracy and dialogue?",
        "Why private funding system leads to exclusive majoritarianisms?",
        "Why private funding system needs crime to thrive?"
    ]

    def handle(self, *args, **options):
        created_count = 0
        for rank, text in enumerate(self.questions_texts, 1):
            question, created = Question.objects.get_or_create(
                text=text,
                defaults={
                    'author_id': None,
                    'is_approved': True,
                    'rank': rank,
                    'activity_score': 0,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created question rank {rank}: {text[:50]}"))
            else:
                self.stdout.write(f"Already exists question rank {question.rank}: {text[:50]}")

        self.stdout.write(self.style.SUCCESS(f"Finished! Created {created_count} new questions."))
