import os
import logging
import wikipedia
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------------- НАСТРОЙКИ ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # токен из переменной окружения
SUMMARY_SENTENCES = 5  # сколько предложений показывать
LOG_FILE = "logs.txt"

# Проверяем наличие токена
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не найден. Добавь его в переменные окружения Render!")

# Настройка языка Википедии
wikipedia.set_lang("ru")

# ---------------- ЛОГИ ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------------- КОМАНДЫ ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "Привет! 👋\nЯ бот, который ищет статьи в Википедии.\n"
        "Просто напиши запрос, например:\n<i>Квантовая запутанность</i>"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь текст запроса — я покажу краткое содержание статьи из Википедии.")

# ---------------- ОБРАБОТКА ЗАПРОСА ----------------
async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return

    try:
        summary = wikipedia.summary(query, sentences=SUMMARY_SENTENCES)
    except wikipedia.exceptions.DisambiguationError as e:
        options = "\n".join(e.options[:5])
        await update.message.reply_text(f"❗ Запрос неоднозначен. Возможные варианты:\n{options}")
        return
    except wikipedia.exceptions.PageError:
        await update.message.reply_text("❌ Статья не найдена в Википедии.")
        return
    except Exception as e:
        logger.exception(f"Ошибка при поиске статьи: {e}")
        await update.message.reply_text("⚠️ Ошибка при поиске статьи. Попробуйте позже.")
        return

    context.user_data["article"] = {
        "text": summary,
        "offset": 0
    }

    await send_article(update, context)

# ---------------- ПАГИНАЦИЯ ("Ещё") ----------------
async def send_article(update, context):
    article = context.user_data.get("article", {})
    text = article.get("text", "")
    offset = article.get("offset", 0)
    chunk_size = 1000

    part = text[offset:offset + chunk_size]
    buttons = []

    if offset + chunk_size < len(text):
        context.user_data["article"]["offset"] = offset + chunk_size
        buttons.append([InlineKeyboardButton("Ещё", callback_data="more")])

    markup = InlineKeyboardMarkup(buttons) if buttons else None

    if hasattr(update, "message") and update.message:
        await update.message.reply_text(part, reply_markup=markup)
    else:
        await update.callback_query.message.reply_text(part, reply_markup=markup)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await send_article(query, context)

# ---------------- ГЛАВНАЯ ----------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
    app.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("🚀 Бот запущен, жду запросов в Telegram...")
    app.run_polling()

if __name__ == "__main__":
    main()