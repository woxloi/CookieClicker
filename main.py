import discord
from discord.ext import commands, tasks
import json
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "cookie_data.json"
user_data = {}

def load_data():
    global user_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            user_data = json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)

load_data()

# アップグレードリスト（順番重要）
UPGRADES = [
    {"key": "click_power_1", "name": "クリック強化 Lv1", "cost": 100, "increase": 1, "requires": None},
    {"key": "click_power_2", "name": "クリック強化 Lv2", "cost": 300, "increase": 2, "requires": "click_power_1"},
    {"key": "click_power_3", "name": "クリック強化 Lv3", "cost": 800, "increase": 5, "requires": "click_power_2"},
    {"key": "auto_speed_1", "name": "自動焼き速度UP Lv1", "cost": 500, "increase": 1, "requires": None},
    {"key": "auto_speed_2", "name": "自動焼き速度UP Lv2", "cost": 1500, "increase": 2, "requires": "auto_speed_1"},
]

class CookieButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(self.BakeButton())

    class BakeButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="🔥 クッキーを焼く！", style=discord.ButtonStyle.primary, custom_id="cookie_bake")

        async def callback(self, interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            if user_id not in user_data:
                user_data[user_id] = {
                    "cookies": 0,
                    "auto": True,
                    "click_power_1": False,
                    "click_power_2": False,
                    "click_power_3": False,
                    "auto_speed_1": False,
                    "auto_speed_2": False,
                }
            user = user_data[user_id]

            # 一番高いクリック強化レベルの増加量を計算
            click_power = 1  # ベース
            for upgrade in ["click_power_1", "click_power_2", "click_power_3"]:
                if user.get(upgrade, False):
                    # それぞれの増加量はアップグレードのincrease値をUPGRADESから取得
                    level = next((u for u in UPGRADES if u["key"] == upgrade), None)
                    if level:
                        click_power += level["increase"]

            user["cookies"] = user.get("cookies", 0) + click_power
            save_data()
            await interaction.response.send_message(f"🍪 クッキーが焼けた！（+{click_power}）現在のクッキー数: {user['cookies']}", ephemeral=True)

@tasks.loop(seconds=1.0)
async def auto_bake():
    for user_id, data in user_data.items():
        if data.get("auto", True):
            # 自動焼き速度計算
            auto_speed = 1
            for upgrade in ["auto_speed_1", "auto_speed_2"]:
                if data.get(upgrade, False):
                    level = next((u for u in UPGRADES if u["key"] == upgrade), None)
                    if level:
                        auto_speed += level["increase"]
            data["cookies"] = data.get("cookies", 0) + auto_speed
    save_data()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    auto_bake.start()

@bot.command()
async def cookie(ctx, sub: str = None, *args):
    user_id = str(ctx.author.id)
    if user_id not in user_data:
        user_data[user_id] = {
            "cookies": 0,
            "auto": True,
            "click_power_1": False,
            "click_power_2": False,
            "click_power_3": False,
            "auto_speed_1": False,
            "auto_speed_2": False,
        }
        save_data()

    user = user_data[user_id]

    if sub == "button":
        view = CookieButton()
        await ctx.send("🍪 クッキーを焼こう！下のボタンを押してね👇", view=view)

    elif sub == "removebutton":
        async for msg in ctx.channel.history(limit=50):
            if msg.author == bot.user and msg.components:
                try:
                    await msg.delete()
                except:
                    pass
        await ctx.send("🧹 ボタン付きメッセージを削除しました！")

    elif sub == "stats":
        click_power = 1
        for upgrade in ["click_power_1", "click_power_2", "click_power_3"]:
            if user.get(upgrade, False):
                level = next((u for u in UPGRADES if u["key"] == upgrade), None)
                if level:
                    click_power += level["increase"]
        auto_speed = 1
        for upgrade in ["auto_speed_1", "auto_speed_2"]:
            if user.get(upgrade, False):
                level = next((u for u in UPGRADES if u["key"] == upgrade), None)
                if level:
                    auto_speed += level["increase"]

        await ctx.send(
            f"📊 {ctx.author.display_name} さんのステータス\n"
            f"🍪 クッキー: {user['cookies']}\n"
            f"👆 クリック強さ: {click_power}\n"
            f"⏱️ 自動焼き速度: {auto_speed} 秒毎にクッキー {auto_speed} 枚"
        )

    elif sub == "rank":
        sorted_users = sorted(user_data.items(), key=lambda x: x[1].get("cookies", 0), reverse=True)
        top = sorted_users[:10]
        msg = "🥇 **クッキーランキング** 🥇\n"
        for i, (uid, data) in enumerate(top, 1):
            try:
                user_obj = await bot.fetch_user(int(uid))
                name = user_obj.display_name if user_obj else f"User {uid}"
            except:
                name = f"User {uid}"
            msg += f"{i}. {name} - {data.get('cookies', 0)} 枚\n"
        if user_id not in dict(top):
            for i, (uid, data) in enumerate(sorted_users, 1):
                if uid == user_id:
                    msg += f"\n📍 あなたの順位：{i} 位（🍪 {data.get('cookies', 0)} 枚）"
                    break
        await ctx.send(msg)

    elif sub == "off":
        user["auto"] = False
        save_data()
        await ctx.send("⏸️ 自動焼きを停止しました。")

    elif sub == "on":
        user["auto"] = True
        save_data()
        await ctx.send("▶️ 自動焼きを再開しました。")

    elif sub == "shop":
        msg = "**🛍️ クッキーショップ**\n"
        for upgrade in UPGRADES:
            # 購入済みなら「購入済み」と表示
            owned = user.get(upgrade["key"], False)
            require = upgrade["requires"]
            # 購入可能か判定（requireがNoneか、かつrequireを持っている）
            can_buy = False
            if require is None or user.get(require, False):
                can_buy = True
            else:
                can_buy = False
            status = "✅購入済み" if owned else ("🟢購入可能" if can_buy else "❌前アイテムを購入してください")
            msg += f"`{upgrade['key']}`: {upgrade['name']} - 💰 {upgrade['cost']}クッキー - {status}\n"
        msg += "\n`!cookie buy <item_key>` で購入できます！"
        await ctx.send(msg)

    elif sub == "buy":
        if len(args) != 1:
            await ctx.send("🛒 使い方: `!cookie buy <item_key>` です。")
            return
        item_key = args[0]
        item = next((u for u in UPGRADES if u["key"] == item_key), None)
        if not item:
            await ctx.send("❌ そのアイテムは存在しません。`!cookie shop` で確認してください。")
            return

        if user.get(item_key, False):
            await ctx.send("❌ そのアイテムはすでに購入済みです。")
            return

        requires = item["requires"]
        if requires is not None and not user.get(requires, False):
            required_name = next((u["name"] for u in UPGRADES if u["key"] == requires), requires)
            await ctx.send(f"❌ そのアイテムを購入するには「{required_name}」を先に買う必要があります。")
            return

        if user["cookies"] < item["cost"]:
            await ctx.send("💸 クッキーが足りません！")
            return

        user["cookies"] -= item["cost"]
        user[item_key] = True
        save_data()
        await ctx.send(f"✅ 「{item['name']}」を購入しました！")

    else:
        await ctx.send("❓ `!cookie button`, `stats`, `rank`, `off`, `on`, `shop`, `buy`, `removebutton` が使えます。")

bot.run("YOUR_BOT_TOKEN")
