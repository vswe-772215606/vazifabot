"""Everything the bot says, in Uzbek, and how a task list is written out."""

from .storage import Task

BTN_LIST = "Vazifalar"
BTN_HELP = "Yordam"
BTN_DELETE = "O'chirish"
BTN_CLEAR = "Bajarilganlarni tozalash"

DONE_MARK = "✓"
LABEL_LEN = 28

COMMANDS = [
    ("start", "Boshlash"),
    ("vazifalar", "Vazifalar ro'yxati"),
    ("yordam", "Qanday ishlatiladi"),
]

START = (
    "Salom! Men sizning vazifalar daftaringizman.\n\n"
    "Qilinadigan ishni menga yozib yuboring, ro'yxatga qo'shib qo'yaman.\n"
    "Ro'yxatni ko'rish uchun «Vazifalar» tugmasini bosing."
)

HELP = (
    "Qanday ishlatiladi:\n\n"
    "• Ishni yozib yuboring, u ro'yxatga qo'shiladi. Bir xabarda bir nechta qator "
    "yozsangiz, har bir qator alohida vazifa bo'ladi.\n"
    "• «Vazifalar» tugmasi ro'yxatni ochadi.\n"
    "• Vazifani bossangiz, bajarildi deb belgilanadi. Yana bossangiz, qaytadi.\n"
    "• «O'chirish» vazifani butunlay o'chiradi.\n"
    "• «Bajarilganlarni tozalash» bajarilgan ishlarni ro'yxatdan olib tashlaydi.\n\n"
    "Har kimning ro'yxati o'ziniki: vazifalaringizni boshqalar ko'rmaydi."
)

EMPTY = "Ro'yxat bo'sh. Birinchi vazifani yozib yuboring."
LIST_HEADER = "Vazifalaringiz:"
LIST_HINT = "Bajarildi deb belgilash uchun vazifani bosing."
ONLY_TEXT = "Hozircha faqat yozilgan vazifalarni tushunaman. Vazifani matn qilib yuboring."

TOAST_DONE = "Bajarildi"
TOAST_UNDONE = "Qaytarildi"
TOAST_DELETED = "O'chirildi"
TOAST_NOTHING_DONE = "Bajarilgan vazifa yo'q"
TOAST_GONE = "Bu vazifa endi yo'q"


def added(titles: list[str], open_count: int) -> str:
    head = f"Qo'shildi: {titles[0]}" if len(titles) == 1 else f"{len(titles)} ta vazifa qo'shildi."
    return f"{head}\nRo'yxatda {open_count} ta bajarilmagan vazifa bor."


def too_long(limit: int) -> str:
    return f"Vazifa juda uzun. Har birini {limit} belgidan qisqaroq yozing."


def limit_reached(limit: int) -> str:
    return (f"Ro'yxatga {limit} tagacha vazifa sig'adi. "
            "Bajarilganlarini tozalang yoki keraksizini o'chiring.")


def cleared(n: int) -> str:
    return f"{n} ta bajarilgan vazifa tozalandi"


def render_list(tasks: list[Task]) -> str:
    lines = []
    for n, t in enumerate(tasks, 1):
        lines.append(f"{n}. {DONE_MARK} {t.title}" if t.done else f"{n}. {t.title}")
    return "\n\n".join([LIST_HEADER, "\n".join(lines), LIST_HINT])


def task_label(n: int, task: Task) -> str:
    title = task.title if len(task.title) <= LABEL_LEN else task.title[:LABEL_LEN - 1].rstrip() + "…"
    return f"{DONE_MARK} {n}. {title}" if task.done else f"{n}. {title}"
