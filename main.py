import os
import logging
import wikipedia
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)
from uuid import uuid4

# ---------------- НАСТРОЙКИ ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не найден. Добавь его в переменные окружения Render!")

wikipedia.set_lang("ru")

# ---------------- ЛОГИ ----------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ---------------- КОМАНДЫ ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "👋 Привет! Я бот для поиска в Википедии.\n"
        "Чтобы воспользоваться мной, просто напиши в любом чате:\n"
        "<code>@ishaSearch_bot [твой запрос]</code>\n\n"
        "Например:\n<code>@ishaSearch_bot теория относительности</code>"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто напиши: @ishaSearch_bot [твой запрос]\n\n"
        "Я покажу краткое содержание статьи из Википедии 📘"
    )

# ---------------- INLINE ПОИСК ----------------
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    if not query:
        return

    user = update.inline_query.from_user
    logger.info(f"🔍 {user.first_name} ищет: {query}")

    # Симуляция "печати"
    await context.bot.send_chat_action(chat_id=update.inline_query.from_user.id, action="typing")

    try:
        summary = wikipedia.summary(query, sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        summary = "❗ Запрос неоднозначен. Возможные варианты:\n" + "\n".join(e.options[:5])
    except wikipedia.exceptions.PageError:
        summary = "❌ Статья не найдена в Википедии."
    except Exception as e:
        logger.exception("Ошибка при поиске статьи")
        summary = "⚠️ Произошла ошибка при поиске статьи."

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"Результат: {query}",
            input_message_content=InputTextMessageContent(f"📘 *{query}*\n\n{summary}", parse_mode="Markdown"),
            description=summary[:100] + "..." if len(summary) > 100 else summary
        )
    ]

    await update.inline_query.answer(results, cache_time=5)

# ---------------- ГЛАВНАЯ ----------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(InlineQueryHandler(inline_query))

    logger.info("🚀 Бот запущен и ждёт inline-запросов...")
    app.run_polling()

if __name__ == "__main__":
    main()
