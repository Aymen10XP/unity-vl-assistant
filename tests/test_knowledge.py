from tutor_service.config import LESSONS_PATH
from tutor_service.knowledge import load_lessons


def test_lesson_library_is_well_formed():
    lessons = load_lessons(LESSONS_PATH)
    assert len(lessons) >= 15
    assert len({lesson.id for lesson in lessons}) == len(lessons)
    assert all(lesson.steps and lesson.verification for lesson in lessons)
    assert all(len(lesson.example_questions) >= 4 for lesson in lessons)
