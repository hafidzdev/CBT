from django import template

register = template.Library()

@register.filter
def count_by_difficulty(questions, level):
    """Filter custom untuk menghitung jumlah soal berdasarkan tingkat kesulitan."""
    try:
        return questions.filter(difficulty=level).count()
    except Exception:
        return 0
