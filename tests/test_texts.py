from vazifabot import texts
from vazifabot.storage import Task


def test_added_names_a_single_task():
    assert texts.added(["Non olish"], 3) == "Qo'shildi: Non olish\nRo'yxatda 3 ta bajarilmagan vazifa bor."


def test_added_counts_several_tasks():
    assert texts.added(["a", "b"], 2).startswith("2 ta vazifa qo'shildi.")


def test_render_list_numbers_tasks_and_marks_done_ones():
    tasks = [Task(1, 7, "Non olish", False), Task(2, 7, "Sut olish", True)]
    assert texts.render_list(tasks) == (
        "Vazifalaringiz:\n\n"
        "1. Non olish\n"
        f"2. {texts.DONE_MARK} Sut olish\n\n"
        f"{texts.LIST_HINT}"
    )


def test_task_label_keeps_a_short_title_whole():
    assert texts.task_label(1, Task(1, 7, "Non olish", False)) == "1. Non olish"
    assert texts.task_label(2, Task(2, 7, "Non olish", True)) == f"{texts.DONE_MARK} 2. Non olish"


def test_task_label_shortens_a_long_title():
    label = texts.task_label(1, Task(1, 7, "a" * 60, False))
    assert label == "1. " + "a" * (texts.LABEL_LEN - 1) + "…"


def test_command_names_are_valid_for_telegram():
    for name, about in texts.COMMANDS:
        assert name.isascii() and name.islower() and 1 <= len(name) <= 32
        assert 1 <= len(about) <= 256
