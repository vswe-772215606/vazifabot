import pytest

from vazifabot.storage import TaskStore

ALI, VALI = 101, 202


@pytest.fixture
def store(tmp_path):
    s = TaskStore(tmp_path / "data" / "tasks.db")
    yield s
    s.close()


def test_creates_the_folder_and_keeps_tasks_after_reopen(tmp_path):
    path = tmp_path / "nested" / "tasks.db"
    s = TaskStore(path)
    s.add(ALI, "Non olish")
    s.close()

    again = TaskStore(path)
    assert [t.title for t in again.list(ALI)] == ["Non olish"]
    again.close()


def test_add_returns_an_open_task(store):
    task = store.add(ALI, "Non olish")
    assert task.title == "Non olish"
    assert task.done is False
    assert task.chat_id == ALI


def test_list_puts_open_tasks_first_then_done_oldest_first(store):
    a = store.add(ALI, "birinchi")
    store.add(ALI, "ikkinchi")
    store.add(ALI, "uchinchi")
    store.toggle(ALI, a.id)
    assert [t.title for t in store.list(ALI)] == ["ikkinchi", "uchinchi", "birinchi"]


def test_toggle_flips_back_and_forth(store):
    task = store.add(ALI, "Non olish")
    assert store.toggle(ALI, task.id).done is True
    assert store.toggle(ALI, task.id).done is False


def test_counts(store):
    a = store.add(ALI, "a")
    store.add(ALI, "b")
    store.toggle(ALI, a.id)
    assert store.count(ALI) == 2
    assert store.count_open(ALI) == 1


def test_delete(store):
    task = store.add(ALI, "Non olish")
    assert store.delete(ALI, task.id) is True
    assert store.list(ALI) == []
    assert store.delete(ALI, task.id) is False


def test_clear_done_removes_only_done_tasks(store):
    a = store.add(ALI, "a")
    b = store.add(ALI, "b")
    store.add(ALI, "c")
    store.toggle(ALI, a.id)
    store.toggle(ALI, b.id)
    assert store.clear_done(ALI) == 2
    assert [t.title for t in store.list(ALI)] == ["c"]
    assert store.clear_done(ALI) == 0


def test_users_never_see_or_change_each_others_tasks(store):
    alis = store.add(ALI, "Alining ishi")
    store.add(VALI, "Valining ishi")

    assert [t.title for t in store.list(ALI)] == ["Alining ishi"]
    assert [t.title for t in store.list(VALI)] == ["Valining ishi"]
    # Vali pressing a button that carries Ali's task id changes nothing
    assert store.toggle(VALI, alis.id) is None
    assert store.delete(VALI, alis.id) is False
    store.toggle(ALI, alis.id)
    assert store.clear_done(VALI) == 0
    assert store.list(ALI)[0].done is True
