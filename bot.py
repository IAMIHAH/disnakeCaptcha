import json, aiohttp, disnake, os
from disnake import ChannelType, TextChannel
from disnake import Intents
from disnake.ext import commands
from disnake.utils import get

bot = commands.Bot("!", intents=Intents.all())

Captcha = { 'channel': { }, 'chance': { }, 'text': { }, 'msg': { }, 'capid': { } }

CapUser = 0

CHANNEL_ID = 000000000000000000
GENERAL_CHAT = 000000000000000000

@bot.remove_command('help')

@bot.event
async def on_ready():
	print("Ready!")

@bot.event
async def on_member_join(member:disnake.Member):
	if not member.bot:
		global CapUser
		CapUser = member.id
		cha : TextChannel = bot.get_channel(CHANNEL_ID)
		ch = await cha.create_thread(name=f"{member.name} 님의 캡챠", type=ChannelType.public_thread)

		async with aiohttp.ClientSession() as session:
			async with session.get("http://khsdev.xyz:3000/7Z2s7ISg/captcha") as req:
				r = json.loads(await req.text())
				captchaText = r['imagecode']
				image = r['imageurl']
		
		Captcha['channel'][f'{member.id}'] = ch.id
		Captcha['chance'][f'{member.id}'] = 5
		Captcha['text'][f'{member.id}'] = captchaText

		msg = await ch.send(
			content=f"{member.mention}\n📝 **텍스트 캡챠를 발급했어요.**\n\n> **재발급**을 원하시면, **재발급**이라고 입력해주세요.",
			embed=disnake.Embed().set_image(url=image)
		)
		Captcha['msg'][f'{member.id}'] = msg.id

@bot.event
async def on_member_remove(member:disnake.Member):
	if not member.get_role(941966090827862107):
		await DelCaptchaUserVar(member.id)

async def DelCaptchaUserVar(id: int):
	cha = bot.get_channel(CHANNEL_ID)
	ch = cha.get_thread(Captcha['channel'][f'{id}'])
	await ch.delete()
	capmsg = bot.get_channel(CHANNEL_ID)
	mm = await capmsg.fetch_message(Captcha['capid'][f'{id}'])
	await mm.delete()
	try:
		if Captcha['channel'][f'{id}']:
			try:
				cha : TextChannel = bot.get_channel(CHANNEL_ID)
				ch = cha.get_thread(Captcha['channel'][f'{id}'])
				await ch.delete()
			except AttributeError:
				pass
		del(
			Captcha['channel'][f'{id}'], 
			Captcha['chance'][f'{id}'],
			Captcha['text'][f'{id}'],
			Captcha['msg'][f'{id}'],
			Captcha['capid'][f'{id}']
		)
	except KeyError:
		pass
	if os.path.exists(f'file/captcha_{id}.png'):
		os.remove(f'file/captcha_{id}.png')

@bot.event
async def on_message(msg:disnake.Message):
	global Captcha, CapUser
	if msg.author.id == 940201663795433503:
		if "님의 캡챠" in msg.content:
			Captcha['capid'][f'{CapUser}'] = msg.id
			CapUser = 0
	if not msg.author.bot:
		if "캡챠" in msg.channel.name:
			if msg.channel.id == Captcha['channel'][f'{msg.author.id}']:
				if msg.content == Captcha['text'][f'{msg.author.id}']:
					role = get(msg.guild.roles, name="여행자")
					await msg.author.add_roles(role)
					await DelCaptchaUserVar(msg.author.id)
					ch = bot.get_channel(GENERAL_CHAT)
					await ch.send(f"{msg.author.mention}님이 인증을 마치고 날아왔어요!")
				elif msg.content == "재발급":
					async with aiohttp.ClientSession() as session:
						async with session.get("http://khsdev.xyz:3000/7Z2s7ISg/captcha") as req:
							r = json.loads(await req.text())
							captchaText = r['imagecode']
							image = r['imageurl']
					
					Captcha['text'][f'{msg.author.id}'] = captchaText

					m = await msg.reply(
						content=f"📝 **텍스트 캡챠를 발급했어요.**\n\n> **재발급**을 원하시면, **재발급**이라고 입력해주세요.",
						embed=disnake.Embed().set_image(url=image)
					)

					capmsg = bot.get_channel(Captcha['channel'][f'{msg.author.id}'])
					mm = await capmsg.fetch_message(Captcha['msg'][f'{msg.author.id}'])
					await mm.delete()
					del(mm)

					Captcha['chance'][f'{msg.author.id}'] = 5
					Captcha['msg'][f'{msg.author.id}'] = m.id
				else:
					Captcha['chance'][f'{msg.author.id}'] -= 1
					if Captcha['chance'][f'{msg.author.id}'] > 0:
						await msg.reply(f"캡챠 코드가 일치하지 않습니다.\n남은 기회: {Captcha['chance'][f'{msg.author.id}']}회")
					else:
						await msg.author.kick(reason="캡챠 인증 실패 (5회 이상 불일치)")
						cha : TextChannel = bot.get_channel(CHANNEL_ID)
						ch = cha.get_thread(Captcha['channel'][f'{msg.author.id}'])
						await ch.delete(reason="캡챠 인증 실패 (5회 이상 불일치)")
						await DelCaptchaUserVar(msg.author.id)

bot.run("TOKEN")
