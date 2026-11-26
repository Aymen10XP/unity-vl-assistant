from tutor_service.config import LESSONS_PATH
from tutor_service.knowledge import load_lessons


def test_lesson_library_is_well_formed():
    """Protect the service from empty lessons, duplicate IDs, or missing guidance."""

    lessons = load_lessons(LESSONS_PATH)
    assert len(lessons) >= 40
    assert len({lesson.id for lesson in lessons}) == len(lessons)
    assert all(lesson.steps and lesson.verification for lesson in lessons)
    assert all(len(lesson.example_questions) >= 4 for lesson in lessons)
    required_themes = {
        "input", "ui", "animation", "audio", "physics", "debugging",
        "lighting", "scene", "scripting", "2d", "3d", "build",
    }
    available_tags = {tag.lower() for lesson in lessons for tag in lesson.tags}
    assert required_themes <= available_tags
