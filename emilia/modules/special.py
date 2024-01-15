import html
import json
import random
import PIL
import os
import urllib
import datetime
from typing import Optional, List
import time
import urbandict

import pyowm
from pyowm import timeutils, exceptions
from googletrans import Translator
import wikipedia
from kbbi import KBBI
import base64
from bs4 import BeautifulSoup
from emoji import UNICODE_EMOJI

import requests
from telegram.error import BadRequest, Unauthorized
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown

from emilia import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER, API_WEATHER, spamfilters
from emilia.__main__ import STATS, USER_INFO
from emilia.modules.disable import DisableAbleCommandHandler, DisableAbleRegexHandler
from emilia.modules.helper_funcs.extraction import extract_user
from emilia.modules.helper_funcs.filters import CustomFilters
from emilia.modules.sql import languages_sql as langsql

from emilia.modules.languages import tl
from emilia.modules.helper_funcs.alternate import send_message

@run_async
def stickerid(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	msg = update.effective_message
	if msg.reply_to_message and msg.reply_to_message.sticker:
		send_message(update.effective_message, tl(update.effective_message, "Hai {}, Id stiker yang anda balas adalah :\n```{}```").format(mention_markdown(msg.from_user.id, msg.from_user.first_name), msg.reply_to_message.sticker.file_id),
											parse_mode=ParseMode.MARKDOWN)
	else:
		send_message(update.effective_message, tl(update.effective_message, "Tolong balas pesan stiker untuk mendapatkan id stiker"),
											parse_mode=ParseMode.MARKDOWN)

@run_async
def getsticker(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	msg = update.effective_message
	chat_id = update.effective_chat.id
	if msg.reply_to_message and msg.reply_to_message.sticker:
		send_message(
			update.effective_message,
			(
				f"Hai [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})"
				+ ", Silahkan cek file yang anda minta dibawah ini."
				"\nTolong gunakan fitur ini dengan bijak!"
			),
			parse_mode=ParseMode.MARKDOWN,
		)
		bot.sendChatAction(chat_id, "upload_document")
		file_id = msg.reply_to_message.sticker.file_id
		newFile = bot.get_file(file_id)
		newFile.download('sticker.png')
		bot.sendDocument(chat_id, document=open('sticker.png', 'rb'))
		bot.sendChatAction(chat_id, "upload_photo")
		bot.send_photo(chat_id, photo=open('sticker.png', 'rb'))

	else:
		send_message(
			update.effective_message,
			f"Hai [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}), Tolong balas pesan stiker untuk mendapatkan gambar stiker",
			parse_mode=ParseMode.MARKDOWN,
		)

@run_async
def stiker(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat_id = update.effective_chat.id
	args = update.effective_message.text.split(None, 1)
	message = update.effective_message
	message.delete()
	if message.reply_to_message:
		bot.sendSticker(chat_id, args[1], reply_to_message_id=message.reply_to_message.message_id)
	else:
		bot.sendSticker(chat_id, args[1])

@run_async
def file(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat_id = update.effective_chat.id
	args = update.effective_message.text.split(None, 1)
	message = update.effective_message
	message.delete()
	if message.reply_to_message:
		bot.sendDocument(chat_id, args[1], reply_to_message_id=message.reply_to_message.message_id)
	else:
		bot.sendDocument(chat_id, args[1])

@run_async
def getlink(bot: Bot, update: Update, args: List[int]):
	if args:
		chat_id = int(args[0])
	else:
		send_message(update.effective_message, tl(update.effective_message, "Anda sepertinya tidak mengacu pada obrolan"))
	chat = bot.getChat(chat_id)
	bot_member = chat.get_member(bot.id)
	if bot_member.can_invite_users:
		titlechat = bot.get_chat(chat_id).title
		invitelink = bot.get_chat(chat_id).invite_link
		send_message(update.effective_message, tl(update.effective_message, "Sukses mengambil link invite di grup {}. \nInvite link : {}").format(titlechat, invitelink))
	else:
		send_message(update.effective_message, tl(update.effective_message, "Saya tidak memiliki akses ke tautan undangan!"))
	
@run_async
def leavechat(bot: Bot, update: Update, args: List[int]):
	if args:
		chat_id = int(args[0])
	else:
		send_message(update.effective_message, tl(update.effective_message, "Anda sepertinya tidak mengacu pada obrolan"))
	try:
		chat = bot.getChat(chat_id)
		titlechat = bot.get_chat(chat_id).title
		bot.sendMessage(chat_id, tl(update.effective_message, "Selamat tinggal semua 😁"))
		bot.leaveChat(chat_id)
		send_message(update.effective_message, tl(update.effective_message, "Saya telah keluar dari grup {}").format(titlechat))

	except BadRequest as excp:
		if excp.message == "Chat not found":
			send_message(update.effective_message, tl(update.effective_message, "Sepertinya saya sudah keluar atau di tendang di grup tersebut"))
		else:
			return

@run_async
def ping(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	start_time = time.time()
	test = send_message(update.effective_message, "Pong!")
	end_time = time.time()
	ping_time = float(end_time - start_time)
	bot.editMessageText(chat_id=update.effective_chat.id, message_id=test.message_id,
						text=tl(update.effective_message, "Pong!\nKecepatannya: {0:.2f} detik").format(round(ping_time, 2) % 60))

@run_async
def ramalan(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	text = ""
	if random.randint(1,10) >= 7:
		text += random.choice(tl(update.effective_message, "RAMALAN_FIRST"))
	text += random.choice(tl(update.effective_message, "RAMALAN_STRINGS"))
	send_message(update.effective_message, text)    

@run_async
def terjemah(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	msg = update.effective_message
	chat_id = update.effective_chat.id
	getlang = langsql.get_lang(update.effective_message.from_user.id)
	try:
		if msg.reply_to_message and msg.reply_to_message.text:
			args = update.effective_message.text.split()
			if len(args) >= 2:
				target = args[1]
				if "-" in target:
					target2 = target.split("-")[1]
					target = target.split("-")[0]
				else:
					target2 = None
			elif getlang:
				target = getlang
				target2 = None
			else:
				raise IndexError
			teks = msg.reply_to_message.text
			#teks = deEmojify(teks)
			exclude_list = UNICODE_EMOJI.keys()
			for emoji in exclude_list:
				if emoji in teks:
					teks = teks.replace(emoji, '')
			message = update.effective_message
			trl = Translator()
			if target2 is None:
				deteksibahasa = trl.detect(teks)
				tekstr = trl.translate(teks, dest=target)
				send_message(update.effective_message, tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
			else:
				tekstr = trl.translate(teks, dest=target2, src=target)
				send_message(update.effective_message, tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)

		else:
			args = update.effective_message.text.split(None, 2)
			if len(args) != 1:
				target = args[1]
				teks = args[2]
				target2 = None
				if "-" in target:
					target2 = target.split("-")[1]
					target = target.split("-")[0]
			else:
				target = getlang
				teks = args[1]
			#teks = deEmojify(teks)
			exclude_list = UNICODE_EMOJI.keys()
			for emoji in exclude_list:
				if emoji in teks:
					teks = teks.replace(emoji, '')
			message = update.effective_message
			trl = Translator()
			if target2 is None:
				deteksibahasa = trl.detect(teks)
				tekstr = trl.translate(teks, dest=target)
				return send_message(update.effective_message, tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
			else:
				tekstr = trl.translate(teks, dest=target2, src=target)
				send_message(update.effective_message, tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)
	except IndexError:
		send_message(update.effective_message, tl(update.effective_message, "Balas pesan atau tulis pesan dari bahasa lain untuk "
											"diterjemahkan kedalam bahasa yang di dituju\n\n"
											"Contoh: `/tr en-id` untuk menerjemahkan dari Bahasa inggris ke Bahasa Indonesia\n"
											"Atau gunakan: `/tr id` untuk deteksi otomatis dan menerjemahkannya kedalam bahasa indonesia"), parse_mode="markdown")
	except ValueError:
		send_message(update.effective_message, tl(update.effective_message, "Bahasa yang di tuju tidak ditemukan!"))
	else:
		return


@run_async
def wiki(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	msg = update.effective_message
	chat_id = update.effective_chat.id
	args = update.effective_message.text.split(None, 1)
	teks = args[1]
	message = update.effective_message
	getlang = langsql.get_lang(chat_id)
	if str(getlang) == "id":
		wikipedia.set_lang("id")
	else:
		wikipedia.set_lang("en")
	try:
		pagewiki = wikipedia.page(teks)
	except wikipedia.exceptions.PageError:
		send_message(update.effective_message, tl(update.effective_message, "Hasil tidak ditemukan"))
		return
	except wikipedia.exceptions.DisambiguationError as refer:
		rujuk = str(refer).split("\n")
		batas = min(len(rujuk), 6)
		teks = ""
		for x in range(batas):
			if x == 0:
				if getlang == "id":
					teks += rujuk[x].replace('may refer to', 'dapat merujuk ke')+"\n"
				else:
					teks += rujuk[x]+"\n"
			else:
				teks += f"- `{rujuk[x]}" + "`\n"
		send_message(update.effective_message, teks, parse_mode="markdown")
		return
	except IndexError:
		send_message(update.effective_message, tl(update.effective_message, "Tulis pesan untuk mencari dari sumber wikipedia"))
		return
	judul = pagewiki.title
	summary = pagewiki.summary
	if update.effective_message.chat.type == "private":
		send_message(update.effective_message, tl(update.effective_message, "Hasil dari {} adalah:\n\n<b>{}</b>\n{}").format(teks, judul, summary), parse_mode=ParseMode.HTML)
	else:
		if len(summary) >= 200:
			judul = pagewiki.title
			summary = f"{summary[:200]}..."
			button = InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton(
							text=tl(update.effective_message, "Baca Lebih Lengkap"),
							url=f"t.me/{bot.username}?start=wiki-{teks.replace(' ', '_')}",
						)
					]
				]
			)
		else:
			button = None
		send_message(update.effective_message, tl(update.effective_message, "Hasil dari {} adalah:\n\n<b>{}</b>\n{}").format(teks, judul, summary), parse_mode=ParseMode.HTML, reply_markup=button)


@run_async
def kamusbesarbahasaindonesia(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	msg = update.effective_message
	chat_id = update.effective_chat.id
	try:
		args = update.effective_message.text.split(None, 1)
		teks = args[1]
		message = update.effective_message
		try:
			api = requests.get(
				f'http://kateglo.com/api.php?format=json&phrase={teks}'
			).json()
		except json.decoder.JSONDecodeError:
			send_message(update.effective_message, "Hasil tidak ditemukan!", parse_mode=ParseMode.MARKDOWN)
			return
		#kamusid = KBBI(teks)
		parsing = f"***Hasil dari kata {api['kateglo']['phrase']} ({api['kateglo']['lex_class_name']}) di {api['kateglo']['ref_source_name']}***\n\n"
		if len(api['kateglo']['definition']) >= 6:
			jarak = 5
		else:
			jarak = len(api['kateglo']['definition'])
		for x in range(jarak):
			parsing += f"*{x + 1}.* {api['kateglo']['definition'][x]['def_text']}"
			if contoh := api['kateglo']['definition'][x]['sample']:
				parsing += f"""\nContoh: `{str(BeautifulSoup(contoh, "lxml")).replace('<html><body><p>', '').replace('</p></body></html>', '')}`"""
			parsing += "\n\n"
		send_message(update.effective_message, parsing, parse_mode=ParseMode.MARKDOWN)

	except IndexError:
		send_message(update.effective_message, "Tulis pesan untuk mencari dari kamus besar bahasa indonesia")
	except KBBI.TidakDitemukan:
		send_message(update.effective_message, "Hasil tidak ditemukan")
	else:
		return

@run_async
def kitabgaul(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	msg = update.effective_message
	chat_id = update.effective_chat.id
	message = update.effective_message
	try:
		args = update.effective_message.text.split(None, 1)
		teks = args[1]
	except IndexError:
		trend = requests.get("https://kitabgaul.com/api/entries;trending").json()
		best = requests.get("https://kitabgaul.com/api/entries;best").json()
		if len(trend.get('entries')) == 0:
			return send_message(update.effective_message, "Tidak ada Hasil yang ditampilkan!", parse_mode=ParseMode.MARKDOWN)
		tbalas = "".join(
			f"*{x + 1}. {trend.get('entries')[x].get('word')}*\n*Slug:* `{trend.get('entries')[x].get('slug')}`\n*Definisi:* `{trend.get('entries')[x].get('definition')}`\n*Contoh:* `{trend.get('entries')[x].get('example')}`\n\n"
			for x in range(3)
		)
		if len(best.get('entries')) == 0:
			return send_message(update.effective_message, "Tidak ada Hasil yang ditampilkan!", parse_mode=ParseMode.MARKDOWN)
		bbalas = "".join(
			f"*{x + 1}. {best.get('entries')[x].get('word')}*\n*Slug:* `{best.get('entries')[x].get('slug')}`\n*Definisi:* `{best.get('entries')[x].get('definition')}`\n*Contoh:* `{best.get('entries')[x].get('example')}`\n\n"
			for x in range(3)
		)
		balas = f"*<== Trending saat ini ==>*\n\n{tbalas}*<== Terbaik saat ini ==>*\n\n{bbalas}"
		send_message(update.effective_message, balas, parse_mode=ParseMode.MARKDOWN)
	kbgaul = requests.get(f"https://kitabgaul.com/api/entries/{teks}").json()
	balas = f"*Hasil dari {teks}*\n\n"
	if len(kbgaul.get('entries')) == 0:
		return send_message(
			update.effective_message,
			f"Tidak ada Hasil dari {teks}",
			parse_mode=ParseMode.MARKDOWN,
		)
	jarak = min(len(kbgaul.get('entries')), 3)
	for x in range(jarak):
		balas += f"*{x + 1}. {kbgaul.get('entries')[x].get('word')}*\n*Slug:* `{kbgaul.get('entries')[x].get('slug')}`\n*Definisi:* `{kbgaul.get('entries')[x].get('definition')}`\n*Contoh:* `{kbgaul.get('entries')[x].get('example')}`\n\n"
	send_message(update.effective_message, balas, parse_mode=ParseMode.MARKDOWN)

@run_async
def urbandictionary(bot: Bot, update: Update, args):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	msg = update.effective_message
	chat_id = update.effective_chat.id
	message = update.effective_message
	if args:
		text = " ".join(args)
		try:
			mean = urbandict.define(text)
		except Exception as err:
			send_message(update.effective_message, f"Error: {str(err)}")
			return
		if len(mean) >= 0:
			teks = ""
			if len(mean) >= 3:
				for x in range(3):
					teks = f'*Result of {text}*\n\n*{mean[x].get("word")[:-7]}*\n*Meaning:*\n`{mean[x].get("def")}`\n\n*Example:*\n`{mean[x].get("example")}`\n\n'
			else:
				for x in range(len(mean)):
					teks = f'*Result of {text}*\n\n*{mean[x].get("word")[:-7]}*\n**Meaning:*\n`{mean[x].get("def")}`\n\n*Example:*\n`{mean[x].get("example")}`\n\n'
			send_message(update.effective_message, teks, parse_mode=ParseMode.MARKDOWN)
		else:
			send_message(
				update.effective_message,
				f"{text} couldn't be found in urban dictionary!",
				parse_mode=ParseMode.MARKDOWN,
			)
	else:
		send_message(update.effective_message, "Use `/ud <text` for search meaning from urban dictionary.", parse_mode=ParseMode.MARKDOWN)

@run_async
def log(bot: Bot, update: Update):
	message = update.effective_message
	eventdict = message.to_dict()
	jsondump = json.dumps(eventdict, indent=4)
	send_message(update.effective_message, jsondump)

def deEmojify(inputString):
    return inputString.encode('ascii', 'ignore').decode('ascii')


__help__ = "exclusive_help"

__mod_name__ = "💖 Exclusive Emilia 💖"

STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
#GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)
PING_HANDLER = DisableAbleCommandHandler("ping", ping)
STIKER_HANDLER = CommandHandler("stiker", stiker, filters=Filters.user(OWNER_ID))
FILE_HANDLER = CommandHandler("file", file, filters=Filters.user(OWNER_ID))
GETLINK_HANDLER = CommandHandler("getlink", getlink, pass_args=True, filters=Filters.user(OWNER_ID))
LEAVECHAT_HANDLER = CommandHandler(["leavechat", "leavegroup", "leave"], leavechat, pass_args=True, filters=Filters.user(OWNER_ID))
RAMALAN_HANDLER = DisableAbleCommandHandler(["ramalan", "fortune"], ramalan)
TERJEMAH_HANDLER = DisableAbleCommandHandler(["tr", "tl"], terjemah)
WIKIPEDIA_HANDLER = DisableAbleCommandHandler("wiki", wiki)
KBBI_HANDLER = DisableAbleCommandHandler("kbbi", kamusbesarbahasaindonesia)
KBGAUL_HANDLER = DisableAbleCommandHandler("kbgaul", kitabgaul)
UD_HANDLER = DisableAbleCommandHandler("ud", urbandictionary, pass_args=True)
LOG_HANDLER = DisableAbleCommandHandler("log", log, filters=Filters.user(OWNER_ID))

dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
#dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(STIKER_HANDLER)
dispatcher.add_handler(FILE_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
dispatcher.add_handler(RAMALAN_HANDLER)
dispatcher.add_handler(TERJEMAH_HANDLER)
dispatcher.add_handler(WIKIPEDIA_HANDLER)
dispatcher.add_handler(KBBI_HANDLER)
dispatcher.add_handler(KBGAUL_HANDLER)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
