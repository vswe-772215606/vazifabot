"""The Telegram handlers, driven with small stand-ins for Telegram's objects."""

import asyncio
from types import SimpleNamespace

import pytest
from telegram import InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, CommandHandler

from vazifabot import main, texts
from vazifabot.storage import TaskStore

CHAT = 101


class FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.replies = []

    async def reply_text(self, text, reply_markup=None):
        self.replies.append((text, reply_markup))


class FakeQuery:
    def __init__(self, data, edit_error=None):
        self.data = data
        self.answers = []
        self.edits = []
        self.edit_error = edit_error

    async def answer(self, text=None):
        self.answers.append(text)

    async def edit_message_text(self, text, reply_markup=None):
        if self.edit_error:
            raise self.edit_error
        self.edits.append((text, reply_markup))


@pytest.fixture
def store():
    s = TaskStore(":memory:")
    yield s
    s.close()


def context_for(store):
    return SimpleNamespace(bot_data={"store": store})


def message_update(text=""):
    return SimpleNamespace(message=FakeMessage(text), effective_chat=SimpleNamespace(id=CHAT))


def button_update(query):
    return SimpleNamespace(callback_query=query, effective_chat=SimpleNamespace(id=CHAT))


def test_start_greets_in_uzbek_with_the_menu(store):
    update = message_update("/start")
    asyncio.run(main.start(update, context_for(store)))
    assert update.message.replies == [(texts.START, main.MENU)]


def test_a_text_message_is_saved_as_a_task(store):
    update = message_update("Non olish")
    asyncio.run(main.add_tasks(update, context_for(store)))
    assert [t.title for t in store.list(CHAT)] == ["Non olish"]
    assert update.message.replies[0][0] == texts.added(["Non olish"], 1)


def test_the_list_comes_with_inline_buttons(store):
    task = store.add(CHAT, "Non olish")
    update = message_update(texts.BTN_LIST)
    asyncio.run(main.show_list(update, context_for(store)))
    text, markup = update.message.replies[0]
    assert text == texts.render_list([task])
    assert isinstance(markup, InlineKeyboardMarkup)
    assert markup.inline_keyboard[0][0].callback_data == f"t:{task.id}"
    assert markup.inline_keyboard[0][1].callback_data == f"d:{task.id}"


def test_an_empty_list_has_no_inline_keyboard(store):
    update = message_update(texts.BTN_LIST)
    asyncio.run(main.show_list(update, context_for(store)))
    assert update.message.replies == [(texts.EMPTY, None)]


def test_a_button_press_answers_and_redraws_the_list(store):
    task = store.add(CHAT, "Non olish")
    query = FakeQuery(f"t:{task.id}")
    asyncio.run(main.on_button(button_update(query), context_for(store)))
    assert query.answers == [texts.TOAST_DONE]
    assert store.list(CHAT)[0].done is True
    assert query.edits[0][0] == texts.render_list(store.list(CHAT))


def test_an_unchanged_list_is_not_an_error(store):
    query = FakeQuery("c", edit_error=BadRequest("Message is not modified"))
    asyncio.run(main.on_button(button_update(query), context_for(store)))
    assert query.answers == [texts.TOAST_NOTHING_DONE]


def test_other_telegram_errors_still_surface(store):
    query = FakeQuery("c", edit_error=BadRequest("Message to edit not found"))
    with pytest.raises(BadRequest):
        asyncio.run(main.on_button(button_update(query), context_for(store)))


def test_markup_builds_rows_of_buttons():
    m = main.markup([[("1. Non olish", "t:1"), (texts.BTN_DELETE, "d:1")], [(texts.BTN_CLEAR, "c")]])
    assert [[b.text for b in row] for row in m.inline_keyboard] == [
        ["1. Non olish", texts.BTN_DELETE], [texts.BTN_CLEAR]]
    assert main.markup([]) is None


def test_build_app_registers_the_commands_and_the_button_handler(tmp_path):
    app = main.build_app("123456:TEST-TOKEN", str(tmp_path / "tasks.db"))
    handlers = app.handlers[0]
    commands = set().union(*(h.commands for h in handlers if isinstance(h, CommandHandler)))
    assert {"start", "vazifalar", "yordam"} <= commands
    assert any(isinstance(h, CallbackQueryHandler) for h in handlers)
    assert (tmp_path / "tasks.db").exists()
    app.bot_data["store"].close()


def test_main_refuses_to_start_without_a_token(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        main.main()
