from django.db import transaction
from ..models.questions import Question
from django.db import models

def recalculate_ranks_by_activity():
    """
    Recalculate ranks for approved questions based on activity_score.
    Highest score gets rank 1.
    """
    approved_questions = Question.objects.filter(is_approved=True).order_by('-activity_score', 'created_at')

    for i, q in enumerate(approved_questions, start=1):
        q.rank = i
        q.save(update_fields=['rank'])


@transaction.atomic
def move_question_rank(question_id, new_rank):
    """
    Move a question to a new rank, shifting others accordingly.
    """
    question = Question.objects.get(id=question_id)
    old_rank = question.rank

    if new_rank == old_rank:
        return  # No change

    if new_rank < old_rank:
        # Shift others down (rank+1)
        Question.objects.filter(rank__gte=new_rank, rank__lt=old_rank).update(rank=models.F('rank') + 1)
    else:
        # Shift others up (rank-1)
        Question.objects.filter(rank__gt=old_rank, rank__lte=new_rank).update(rank=models.F('rank') - 1)

    # Set the new rank for the moved question
    question.rank = new_rank
    question.save(update_fields=['rank'])
