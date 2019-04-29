#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

from bs4 import BeautifulSoup
import json
import os
import re
import requests
import time
from uuid import uuid4


from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent, MessageEntity, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, InlineQueryHandler, CommandHandler, run_async

# the secret configuration specific things
ENV = bool(os.environ.get("ENV", False))
if ENV:
    from sample_config import Config
else:
    from config import Config


import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# this method will save the url with the mp3 to the current working directory
# with the name provided.
def DownLoadFile(url, file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=Config.CHUNK_SIZE):
            fd.write(chunk)
    return file_name


# the Telegram trackings
from chatbase import Message


def TRChatBase(chat_id, message_text, intent):
    msg = Message(api_key=Config.CBTOKEN,
                  platform="Telegram",
                  version="1.3",
                  user_id=chat_id,
                  message=message_text,
                  intent=intent)
    resp = msg.send()


def SearchMyDramaList(query):
    url = "https://mydramalist.com/search"
    payload = {"q": query}
    drama_page_resp = requests.get(url, params=payload)
    drama_page_bsoup = BeautifulSoup(drama_page_resp.text, "html.parser")
    arry = []
    mydivs = drama_page_bsoup.findAll("div", {"class": "box"})
    # 0: support MyDramaList
    # 1: advanced search
    # 2: recent Discussions
    # 3: featured trailers
    selectable_divs = mydivs[4:13]
    # take only the first 9 results,
    for sdiv in selectable_divs:
        url = "https://mydramalist.com/{}".format(sdiv.find("a")["href"])
        sub_title = sdiv.find("span", {"class": "text-muted"}).text
        rating = sdiv.find("span", {"class": "score"}).text
        description = sdiv.findAll("p")[-1].text
        image_url = sdiv.find("img")["src"]
        image_alt = sdiv.find("img")["alt"]
        arry.append({
            "url": url,
            "sub_title": sub_title,
            "rating": rating,
            "description": description,
            "image_url": image_url,
            "title": image_alt
        })
    return arry


@run_async
def version(bot, update):
    TRChatBase(update.message.chat_id, update.message.text, "version")
    bot.send_message(
        chat_id=update.message.chat_id,
        reply_to_message_id=update.message.message_id,
        text="10.01.2019 19:45:30"
    )


@run_async
def rate(bot, update):
    TRChatBase(update.message.chat_id, update.message.text, "rate")
    bot.send_message(
        chat_id=update.message.chat_id,
        disable_web_page_preview=True,
        reply_to_message_id=update.message.message_id,
        text="""If you like me, please give 5 star ⭐️⭐️⭐️⭐️⭐️ rating at: https://t.me/tlgrmcbot?start=mydramalistbot-bot
You can also recommend me @MyDramaListBot to your friends.
Have a nice day!"""
    )


@run_async
def donate(bot, update):
    TRChatBase(update.message.chat_id, update.message.text, "donate")
    inline_keyboard = []
    inline_keyboard.append([
        InlineKeyboardButton(text="Use Google Pay", url="https://g.co/payinvite/p48pZ")
    ])
    inline_keyboard.append([
        InlineKeyboardButton(text="Use PhonePe", url="https://phon.pe/ru_shri636w3")
    ])
    inline_keyboard.append([
        InlineKeyboardButton(text="Donate to Developer", url="https://donate.shrimadhavuk.me")
    ])
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    bot.send_message(
        chat_id=update.message.chat_id,
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id,
        text="There are multiple ways to donate: 👇"
    )


@run_async
def start(bot, update):
    TRChatBase(update.message.chat_id, update.message.text, "start")
    inline_keyboard = []
    inline_keyboard.append([
        InlineKeyboardButton("Search InLine",
                             switch_inline_query_current_chat="")
    ])
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    bot.send_message(
        chat_id=update.message.chat_id,
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id,
        text="Use Me InLine. /donate to Support my Developer"
    )


@run_async
def inlinequery(bot, update):
    TRChatBase(update.inline_query.from_user.id,
               update.inline_query.query, "InLine")
    """Handle the inline query."""
    query = update.inline_query.query
    search_results = SearchMyDramaList(query)
    results = []
    for k in search_results:
        title = k["title"]
        url = k["url"]
        description = k["description"]
        image_url = k["image_url"]
        sub_title = k["sub_title"]
        rating = k["rating"]
        message_text = """<a href='{}'>{}</a><b>{}</b>
⭐️{} <a href='{}'>MyDramaList</a>

{}

{}""".format(image_url, '&#8203;', title, rating, url, sub_title, description)
        results.append(
            InlineQueryResultArticle(
                id=uuid4(),
                title=title,
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False
                ),
                url=url,
                hide_url=False,
                description=description,
                thumb_url=image_url,
                # thumb_width=,
                # thumb_height=,
            )
        )
    update.inline_query.answer(results)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    # TRChatBase(update.message.chat_id, update.message.text, "error")
    logger.warning('Update "%s" caused error "%s"', update, error)


if __name__ == "__main__":
    updater = Updater(token=Config.TG_BOT_TOKEN)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('donate', donate))
    updater.dispatcher.add_handler(CommandHandler('rate', rate))
    updater.dispatcher.add_handler(CommandHandler('version', version))
    updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))
    updater.dispatcher.add_error_handler(error)
    if ENV:
        updater.start_webhook(
            listen="0.0.0.0", port=Config.PORT, url_path=Config.TG_BOT_TOKEN)
        updater.bot.set_webhook(url=Config.URL + Config.TG_BOT_TOKEN)
    else:
        updater.start_polling()
    updater.idle()
