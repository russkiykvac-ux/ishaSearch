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
import hashlib

# ---------------- НАСТРОЙКИ ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не найден. Добавь его в переменные окружения Render!")

wikipedia.set_lang("ru")
SUMMARY_SENTENCES = 3  # сколько предложений показывать в сниппете

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
        summary = wikipedia.summary(query, sentences=SUMMARY_SENTENCES)
        # Ссылка на полную статью
        page_url = wikipedia.page(query).url
        summary += f"\n\n🔗 [Открыть в Википедии]({page_url})"
    except wikipedia.exceptions.DisambiguationError as e:
        summary = "❗ Запрос неоднозначен. Возможные варианты:\n" + "\n".join(e.options[:5])
    except wikipedia.exceptions.PageError:
        summary = "❌ Статья не найдена в Википедии."
    except Exception as e:
        logger.exception("Ошибка при поиске статьи")
        summary = "⚠️ Произошла ошибка при поиске статьи."

    # Генерируем детерминированный ID для предотвращения дублирования
    result_id = hashlib.md5(query.encode()).hexdigest()

    results = [
        InlineQueryResultArticle(
            id=result_id,
            title=f"Результат: {query}",
            input_message_content=InputTextMessageContent(
                f"📘 *{query}*\n\n{summary}",
                parse_mode="Markdown"
            ),
            description=summary[:100] + "..." if len(summary) > 100 else summary
        )
    ]

    # cache_time увеличен, чтобы Telegram не делал повторный запрос
    await update.inline_query.answer(results, cache_time=60)

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
