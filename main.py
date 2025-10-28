import os
import logging
import wikipedia
from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)
import hashlib

# ---------------- НАСТРОЙКИ ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не найден. Добавь его в переменные окружения Render!")

wikipedia.set_lang("ru")
SUMMARY_SENTENCES = 3

# ---------------- ЛОГИ ----------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- КОМАНДЫ ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "👋 Привет! Я бот для поиска в Википедии.\n"
        "Чтобы воспользоваться мной, напишите в любом чате:\n"
        "<code>@ishaSearch_bot [твой запрос]</code>"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Напишите: @ishaSearch_bot [ваш запрос] — и я покажу краткое содержание статьи."
    )

# ---------------- INLINE ПОИСК ----------------
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return

    logger.info(f"Поиск: {query}")

    try:
        summary = wikipedia.summary(query, sentences=SUMMARY_SENTENCES)
        page_url = wikipedia.page(query).url
        summary += f"\n\n🔗 [Открыть в Википедии]({page_url})"
    except wikipedia.exceptions.DisambiguationError as e:
        summary = "❗ Запрос неоднозначен. Возможные варианты:\n" + "\n".join(e.options[:5])
    except wikipedia.exceptions.PageError:
        summary = "❌ Статья не найдена в Википедии."
    except Exception as e:
        logger.exception("Ошибка при поиске статьи")
        summary = "⚠️ Произошла ошибка при поиске статьи."

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

    # отвечаем только через answer — больше никаких send_message
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
