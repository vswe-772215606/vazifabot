"""What the bot does with a message or a button press, kept apart from Telegram so it can be
tested on its own. A keyboard is returned as rows of (label, callback data) pairs."""

from . import texts
from .storage import TaskStore

# One list message has to fit Telegram's limits: 4096 characters of text and about 100
# buttons. 30 tasks of at most 100 characters each, two buttons per task, stay well inside.
MAX_TITLE = 100
MAX_TASKS = 30

Rows = list[list[tuple[str, str]]]


def add_from_text(store: TaskStore, chat_id: int, text: str) -> str:
    """Every non-empty line of the message becomes one task."""
    titles = [" ".join(line.split()) for line in text.splitlines()]
    titles = [t for t in titles if t]
    if not titles:
        return texts.EMPTY
    if any(len(t) > MAX_TITLE for t in titles):
        return texts.too_long(MAX_TITLE)
    if store.count(chat_id) + len(titles) > MAX_TASKS:
        return texts.limit_reached(MAX_TASKS)
    for t in titles:
        store.add(chat_id, t)
    return texts.added(titles, store.count_open(chat_id))


def list_view(store: TaskStore, chat_id: int) -> tuple[str, Rows]:
    tasks = store.list(chat_id)
    if not tasks:
        return texts.EMPTY, []
    rows: Rows = [[(texts.task_label(n, t), f"t:{t.id}"), (texts.BTN_DELETE, f"d:{t.id}")]
                  for n, t in enumerate(tasks, 1)]
    if any(t.done for t in tasks):
        rows.append([(texts.BTN_CLEAR, "c")])
    return texts.render_list(tasks), rows


def handle_button(store: TaskStore, chat_id: int, data: str) -> str:
    """Apply a button press; returns the short notice Telegram shows on top of the chat."""
    kind, _, raw = data.partition(":")
    if kind == "c":
        n = store.clear_done(chat_id)
        return texts.cleared(n) if n else texts.TOAST_NOTHING_DONE
    try:
        task_id = int(raw)
    except ValueError:
        return texts.TOAST_GONE
    if kind == "t":
        task = store.toggle(chat_id, task_id)
        if task is None:
            return texts.TOAST_GONE
        return texts.TOAST_DONE if task.done else texts.TOAST_UNDONE
    if kind == "d":
        return texts.TOAST_DELETED if store.delete(chat_id, task_id) else texts.TOAST_GONE
    return texts.TOAST_GONE
