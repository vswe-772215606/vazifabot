import pytest

from vazifabot import logic, texts
from vazifabot.storage import TaskStore

ALI, VALI = 101, 202


@pytest.fixture
def store():
    s = TaskStore(":memory:")
    yield s
    s.close()


def test_a_message_becomes_a_task(store):
    reply = logic.add_from_text(store, ALI, "Non olish")
    assert reply == texts.added(["Non olish"], 1)
    assert [t.title for t in store.list(ALI)] == ["Non olish"]


def test_each_line_becomes_its_own_task_and_blank_lines_are_skipped(store):
    reply = logic.add_from_text(store, ALI, "Non olish\n\n  Sut   olish  \nHisobot yuborish")
    assert reply == texts.added(["Non olish", "Sut olish", "Hisobot yuborish"], 3)
    assert [t.title for t in store.list(ALI)] == ["Non olish", "Sut olish", "Hisobot yuborish"]


def test_whitespace_only_adds_nothing(store):
    assert logic.add_from_text(store, ALI, "   \n  ") == texts.EMPTY
    assert store.list(ALI) == []


def test_a_title_over_the_limit_is_refused_and_nothing_is_added(store):
    reply = logic.add_from_text(store, ALI, "qisqa\n" + "x" * (logic.MAX_TITLE + 1))
    assert reply == texts.too_long(logic.MAX_TITLE)
    assert store.list(ALI) == []


def test_a_title_at_the_limit_is_accepted(store):
    logic.add_from_text(store, ALI, "x" * logic.MAX_TITLE)
    assert store.count(ALI) == 1


def test_the_list_stops_at_the_limit(store):
    logic.add_from_text(store, ALI, "\n".join(f"ish {i}" for i in range(logic.MAX_TASKS)))
    assert store.count(ALI) == logic.MAX_TASKS
    assert logic.add_from_text(store, ALI, "yana bitta") == texts.limit_reached(logic.MAX_TASKS)
    assert store.count(ALI) == logic.MAX_TASKS
    # another user still has room
    logic.add_from_text(store, VALI, "Valining ishi")
    assert store.count(VALI) == 1


def test_a_batch_that_would_pass_the_limit_is_refused_whole(store):
    logic.add_from_text(store, ALI, "\n".join(f"ish {i}" for i in range(logic.MAX_TASKS - 1)))
    assert logic.add_from_text(store, ALI, "bir\nikki") == texts.limit_reached(logic.MAX_TASKS)
    assert store.count(ALI) == logic.MAX_TASKS - 1


def test_the_reply_counts_open_tasks_only(store):
    logic.add_from_text(store, ALI, "a\nb")
    first = store.list(ALI)[0]
    store.toggle(ALI, first.id)
    assert logic.add_from_text(store, ALI, "c") == texts.added(["c"], 2)


def test_an_empty_list_has_no_buttons(store):
    assert logic.list_view(store, ALI) == (texts.EMPTY, [])


def test_list_view_gives_each_task_a_toggle_and_a_delete_button(store):
    a = store.add(ALI, "Non olish")
    b = store.add(ALI, "Sut olish")
    text, rows = logic.list_view(store, ALI)
    assert text == texts.render_list([a, b])
    assert rows == [
        [("1. Non olish", f"t:{a.id}"), (texts.BTN_DELETE, f"d:{a.id}")],
        [("2. Sut olish", f"t:{b.id}"), (texts.BTN_DELETE, f"d:{b.id}")],
    ]


def test_the_clear_button_appears_once_something_is_done(store):
    a = store.add(ALI, "Non olish")
    store.toggle(ALI, a.id)
    _, rows = logic.list_view(store, ALI)
    assert rows[-1] == [(texts.BTN_CLEAR, "c")]


def test_the_largest_list_fits_telegrams_limits(store):
    logic.add_from_text(store, ALI, "\n".join(
        f"{i:02d}" + "x" * (logic.MAX_TITLE - 2) for i in range(logic.MAX_TASKS)))
    store.toggle(ALI, store.list(ALI)[0].id)
    text, rows = logic.list_view(store, ALI)
    assert len(text) <= 4096
    assert sum(len(r) for r in rows) <= 100
    assert all(len(data.encode()) <= 64 for row in rows for _, data in row)


def test_toggle_button(store):
    a = store.add(ALI, "Non olish")
    assert logic.handle_button(store, ALI, f"t:{a.id}") == texts.TOAST_DONE
    assert logic.handle_button(store, ALI, f"t:{a.id}") == texts.TOAST_UNDONE


def test_delete_button(store):
    a = store.add(ALI, "Non olish")
    assert logic.handle_button(store, ALI, f"d:{a.id}") == texts.TOAST_DELETED
    assert logic.handle_button(store, ALI, f"d:{a.id}") == texts.TOAST_GONE


def test_clear_button(store):
    a = store.add(ALI, "a")
    store.add(ALI, "b")
    assert logic.handle_button(store, ALI, "c") == texts.TOAST_NOTHING_DONE
    store.toggle(ALI, a.id)
    assert logic.handle_button(store, ALI, "c") == texts.cleared(1)
    assert [t.title for t in store.list(ALI)] == ["b"]


@pytest.mark.parametrize("data", ["", "t:", "t:abc", "x:1", "d:-", "t:999"])
def test_broken_or_stale_button_data_changes_nothing(store, data):
    store.add(ALI, "Non olish")
    assert logic.handle_button(store, ALI, data) == texts.TOAST_GONE
    assert store.count(ALI) == 1
    assert store.count_open(ALI) == 1


def test_another_users_task_id_is_treated_as_gone(store):
    a = store.add(ALI, "Alining ishi")
    assert logic.handle_button(store, VALI, f"d:{a.id}") == texts.TOAST_GONE
    assert store.count(ALI) == 1
