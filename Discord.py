import asyncio
import random
from dotenv import load_dotenv
import os

load_dotenv()
myToken = os.environ.get('DISCORD_TOKEN')

import discord
from discord.ext import commands
from discord import Interaction

stocks = {
    'AAPL': 150.0,
    'GOOGL': 2500.0,
    'MSFT': 300.0,
    'AMZN': 3500.0
}

user_balances = {}
user_stocks = {}  # 각 사용자의 주식 보유 상황을 기록하는 딕셔너리
initial_balance = 1000.0  # 초기 잔고 설정

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

async def 주식시세_업데이트():
    while True:
        for stock in list(stocks.keys()):  # 딕셔너리의 복사본을 만들어 순회
            new_price = stocks[stock] + random.uniform(-10, 10)  # 랜덤한 가격 변동
            stocks[stock] = round(new_price, 2)  # 가격을 소수점 둘째 자리까지 반올림
        await asyncio.sleep(120)  # 120초마다 가격 업데이트

async def 가격_변동_알림():
    while True:
        await asyncio.sleep(30)  # 30초마다 가격 변동 알림
        channel = bot.get_channel(1170630788350480425)  # 알림을 전송할 채널 ID
        async for message in channel.history(limit=10):
            if message.author == bot.user:
                await message.delete()  # 이전 알림 삭제

        for stock in list(stocks.keys()):  # 딕셔너리의 복사본을 만들어 순회
            price = stocks[stock]
            embed = discord.Embed(title="주식 가격 변동 알림", description=f"{stock}의 가격이 갱신되었습니다.", color=0x00ff00)
            embed.add_field(name="현재 가격", value=f"${price}", inline=False)
            await channel.send(embed=embed)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Streaming(name="개발", url="https://www.twitch.tv/kanetv8"))
    await bot.tree.sync()
    bot.loop.create_task(주식시세_업데이트())
    bot.loop.create_task(가격_변동_알림())

@bot.tree.command(name="사전예약", description="사전 예약을 합니다.")
async def 사전예약(interaction: Interaction):
    if interaction.channel.name != '사전예약':
        await interaction.response.send_message(content=f"{interaction.user.mention}님, 이 명령어는 '사전예약' 채널에서만 사용 가능합니다.")
        return

    role = discord.utils.get(interaction.guild.roles, name="예약") # "예약"은 부여하려는 역할의 이름입니다.
    if role is None:
        await interaction.response.send_message(content=f"'예약' 역할을 찾을 수 없습니다.")
        return

    if role in interaction.user.roles:
        await interaction.response.send_message(content=f"{interaction.user.mention}님, 이미 예약하셨습니다.")
        return

    await interaction.user.add_roles(role)
    await interaction.response.send_message(content=f"{interaction.user.mention}님, 예약 역할이 부여되었습니다.")

    # 예약 로그를 남기는 코드
    log_channel = discord.utils.get(interaction.guild.channels, name="예약-로그") # "예약로그"는 로그를 남길 채널의 이름입니다.
    if log_channel is None:
        await interaction.response.send_message(content=f"'예약-로그' 채널을 찾을 수 없습니다.")
        return

    await log_channel.send(content=f"{interaction.user.mention}님이 예약하였습니다.")

commands_grouped = {
    "사전예약 기능": ["사전예약"],
    "주식 기능": ["주식시세", "매수", "매도", "잔고", "입금", "송금", "주식추가", "보유주식"],
    # 추가로 그룹을 만들 수 있습니다.
}

@bot.tree.command(name="도움말", description="모든 명령어의 도움말을 표시합니다.")
async def 도움말(interaction: Interaction):
    embed = discord.Embed(title="도움말", description="사용 가능한 모든 명령어의 목록입니다.", color=0x0080ff)
    for group, commands in commands_grouped.items():
        embed.add_field(name=group, value="\u200b", inline=False)  # 그룹 이름 추가
        for command_name in commands:
            command = bot.tree.get_command(command_name)
            if command:
                embed.add_field(name=command.name, value=command.description, inline=False)
        embed.add_field(name='---------------', value='\u200b', inline=False)  # 수평선 추가
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="주식시세", description="주식의 현재 시세를 확인합니다.")
async def 주식시세(interaction: Interaction, stock: str):
    if stock.upper() in stocks:
        price = stocks[stock.upper()]
        await interaction.response.send_message(content=f"{stock.upper()}의 현재 시세는 ${price}입니다.")
    else:
        await interaction.response.send_message(content=f"{stock.upper()}은(는) 유효한 주식이 아닙니다.")

@bot.tree.command(name="매수", description="주식을 매수합니다. 사용법: /매수 [주식 종목] [수량]")
async def 매수(interaction: Interaction, stock: str, quantity: int):
    if stock.upper() in stocks:
        price = stocks[stock.upper()]
        total_cost = price * quantity

        if total_cost > user_balances.get(interaction.user.id, 0):
            await interaction.response.send_message(content=f"{stock.upper()} {quantity}주를 매수하기에 충분한 잔고가 없습니다.")
        else:
            user_balances[interaction.user.id] -= total_cost
            user_stocks[interaction.user.id] = user_stocks.get(interaction.user.id, {})
            user_stocks[interaction.user.id][stock.upper()] = user_stocks[interaction.user.id].get(stock.upper(), 0) + quantity
            await interaction.response.send_message(content=f"{stock.upper()} {quantity}주를 매수하였습니다.")
    else:
        await interaction.response.send_message(content=f"{stock.upper()}은(는) 유효한 주식이 아닙니다.")

@bot.tree.command(name="매도", description="주식을 매도합니다. 사용법: /매도 [주식 종목] [수량]")
async def 매도(interaction: Interaction, stock: str, quantity: int):
    if stock.upper() in stocks:
        if interaction.user.id not in user_stocks or stock.upper() not in user_stocks[interaction.user.id] or user_stocks[interaction.user.id][stock.upper()] < quantity:
            await interaction.response.send_message(content=f"{stock.upper()} {quantity}주를 매도할 수 없습니다. 매도하려는 주식을 충분히 보유하고 있는지 확인해주세요.")
            return

        price = stocks[stock.upper()]
        total_value = price * quantity

        if interaction.user.id not in user_balances:
            user_balances[interaction.user.id] = 0

        user_balances[interaction.user.id] += total_value
        user_stocks[interaction.user.id][stock.upper()] -= quantity
        await interaction.response.send_message(content=f"{stock.upper()} {quantity}주를 매도하였습니다.")
    else:
        await interaction.response.send_message(content=f"{stock.upper()}은(는) 유효한 주식이 아닙니다.")

@bot.tree.command(name="잔고", description="사용자의 주식 잔고를 확인합니다.")
async def 잔고(interaction: Interaction):
    if interaction.user.id not in user_balances:
        user_balances[interaction.user.id] = initial_balance
    balance = user_balances[interaction.user.id]
    await interaction.response.send_message(content=f"{interaction.user.mention}님의 주식 잔고는 ${balance}입니다.")

@bot.tree.command(name="입금", description="지정된 사용자의 잔고에 금액을 입금합니다.")
async def 입금(interaction: Interaction, user: discord.User, amount: float):
    guild = interaction.guild
    member = await guild.fetch_member(interaction.user.id)
    if member.guild_permissions.administrator:
        if amount <= 0:
            await interaction.response.send_message(content="입금 금액은 양수여야 합니다.")
            return

        if user.id not in user_balances:
            user_balances[user.id] = 0

        user_balances[user.id] += amount
        await interaction.response.send_message(content=f"{user.mention}님의 잔고에 ${amount}를 입금하였습니다.")
    else:
        await interaction.response.send_message(content="관리자만 사용할 수 있는 명령어입니다.")

@bot.tree.command(name="송금", description="지정된 사용자에게 금액을 송금합니다.")
async def 송금(interaction: Interaction, recipient: discord.User, amount: float):
    sender_id = interaction.user.id
    recipient_id = recipient.id

    if sender_id not in user_balances:
        user_balances[sender_id] = initial_balance

    if recipient_id not in user_balances:
        user_balances[recipient_id] = initial_balance

    # 소수점 이하 세 번째 자리에서 반올림하여 소수점 둘째 자리까지만 허용
    amount = round(amount, 2)

    if amount <= 0:
        await interaction.response.send_message(content="송금 금액은 양수 이거나 소수점 둘째 자리까지만 허용 합니다.")
        return

    if user_balances[sender_id] < amount:
        await interaction.response.send_message(content="잔고가 부족하여 송금을 진행할 수 없습니다.")
        return

    user_balances[sender_id] -= amount
    user_balances[recipient_id] += amount

    await interaction.response.send_message(content=f"{interaction.user.mention}님께서 {recipient.mention}님에게 ${amount}를 송금하였습니다.")

@bot.tree.command(name="주식추가", description="관리자만 가능")
async def 주식추가(interaction: Interaction, stock: str, price: float):
    guild = interaction.guild
    member = await guild.fetch_member(interaction.user.id)

    if member.guild_permissions.administrator:
        if stock.upper() in stocks:
            await interaction.response.send_message(content=f"{stock.upper()}은(는) 이미 존재하는 주식입니다.")
            return

        if price <= 0:
            await interaction.response.send_message(content="주식 가격은 양수여야 합니다.")
            return

        stocks[stock.upper()] = price
        await interaction.response.send_message(content=f"새로운 주식 {stock.upper()}가 추가되었습니다. 초기 가격은 ${price}입니다.")
    else:
        await interaction.response.send_message(content="관리자만 사용할 수 있는 명령어입니다.")

@bot.tree.command(name="보유주식", description="사용자가 보유한 주식을 조회합니다. 사용법: /보유주식")
async def 보유주식(interaction: Interaction):
    user_id = interaction.user.id
    if user_id not in user_stocks or not user_stocks[user_id]:
        await interaction.response.send_message(content=f"{interaction.user.mention}님은 어떤 주식도 보유하고 있지 않습니다.")
        return

    embed = discord.Embed(title="보유 주식", description=f"{interaction.user.mention}님의 보유 주식입니다.", color=0x0080ff)
    for stock, quantity in user_stocks[user_id].items():
        embed.add_field(name=stock, value=f"{quantity}주", inline=False)
    await interaction.response.send_message(embed=embed)


bot.run(myToken)