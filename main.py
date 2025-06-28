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
    {
        "key": "click_power_1",
        "item_name": "クリック強化 Lv1",
        "description": "クリック時のクッキー増加量が+1ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 100,
        "cost_increase_rate": 1.5,
        "increase": 1,
        "requires": None,
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "click_power_2",
        "item_name": "クリック強化 Lv2",
        "description": "クリック時のクッキー増加量が+2ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 300,
        "cost_increase_rate": 1.5,
        "increase": 2,
        "requires": "click_power_1",
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "click_power_3",
        "item_name": "クリック強化 Lv3",
        "description": "クリック時のクッキー増加量が+5ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 800,
        "cost_increase_rate": 1.5,
        "increase": 5,
        "requires": "click_power_2",
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "click_multiplier_2x",
        "item_name": "クリック倍率 2倍",
        "description": "クリック時のクッキー増加量の倍率が2倍ずつ上がります（購入回数に応じて倍率上昇）",
        "base_cost": 2000,
        "cost_increase_rate": 1.5,
        "increase": 0,
        "requires": "click_power_3",
        "multiplier": 2.0,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "auto_speed_1",
        "item_name": "自動焼き速度UP Lv1",
        "description": "自動で焼けるクッキーが秒毎に+1ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 500,
        "cost_increase_rate": 1.5,
        "increase": 1,
        "requires": None,
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "auto_speed_2",
        "item_name": "自動焼き速度UP Lv2",
        "description": "自動で焼けるクッキーが秒毎に+2ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 1500,
        "cost_increase_rate": 1.5,
        "increase": 2,
        "requires": "auto_speed_1",
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "auto_mode_fast",
        "item_name": "自動高速焼きモード",
        "description": "0.5秒ごとに2枚ずつ自動焼きが増えます（購入回数に応じて効果上昇）",
        "base_cost": 2500,
        "cost_increase_rate": 1.5,
        "increase": 0,
        "requires": "auto_speed_2",
        "multiplier": None,
        "auto_interval": 0.5,
        "auto_amount": 2,
    },
    {
        "key": "auto_mode_efficiency",
        "item_name": "超効率型焼き",
        "description": "2秒ごとに10枚ずつ自動焼きが増えます（購入回数に応じて効果上昇）",
        "base_cost": 3000,
        "cost_increase_rate": 1.5,
        "increase": 0,
        "requires": "auto_mode_fast",
        "multiplier": None,
        "auto_interval": 2.0,
        "auto_amount": 10,
    },
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
                user_data[user_id] = default_user_data()
            user = user_data[user_id]

            click_power = 1  # ベース

            # クリック強化合計
            for upgrade in UPGRADES:
                if upgrade["increase"] is not None and upgrade["increase"] > 0:
                    count = user.get(f"{upgrade['key']}_count", 0)
                    # クリック強化だけ計算（クリック強化Lv1～3だけ加算）
                    if upgrade["key"].startswith("click_power"):
                        click_power += upgrade["increase"] * count

            # クリック倍率系（購入回数に応じて2の累乗倍）
            mult_upgrade = next((u for u in UPGRADES if u["key"] == "click_multiplier_2x"), None)
            if mult_upgrade:
                count = user.get("click_multiplier_2x_count", 0)
                if count > 0:
                    click_power = int(click_power * (mult_upgrade["multiplier"] ** count))

            user["cookies"] = user.get("cookies", 0) + click_power
            save_data()
            await interaction.response.send_message(
                f"🍪 クッキーが焼けた！（+{click_power}）現在のクッキー数: {user['cookies']}", ephemeral=True
            )

def default_user_data():
    return {
        "cookies": 0,
        "auto": True,
        "auto_interval": 1.0,
        "auto_amount": 1,
        "auto_timer": 0.0,
        # 各アップグレードの購入回数を0で初期化
        **{f"{upgrade['key']}_count": 0 for upgrade in UPGRADES},
    }

@tasks.loop(seconds=0.2)
async def auto_bake():
    for user_id, data in user_data.items():
        if data.get("auto", True):
            # 自動焼きの枚数と間隔計算（購入回数に応じて増加）
            interval = 1.0
            amount = 0

            # 自動焼き速度系アップグレードの効果を合算
            for upgrade in UPGRADES:
                count = data.get(f"{upgrade['key']}_count", 0)
                if count == 0:
                    continue
                if upgrade["auto_interval"] is not None:
                    # 最も短いintervalを採用（または購入回数分だけ短くできる拡張も可）
                    # ここでは単純に購入があればそのintervalに置き換え（複数の組み合わせは後で調整可）
                    interval = min(interval, upgrade["auto_interval"])
                if upgrade["auto_amount"] is not None:
                    amount += upgrade["auto_amount"] * count
                elif upgrade["increase"] is not None:
                    # 自動速度アップ系のincreaseは秒あたりの増加量として加算
                    amount += upgrade["increase"] * count

            # もしamountが0なら最低1枚にする（初期状態）
            if amount == 0:
                amount = 1

            timer = data.get("auto_timer", 0.0)
            timer += 0.2
            if timer >= interval:
                timer = 0.0
                data["cookies"] = data.get("cookies", 0) + amount
            data["auto_timer"] = timer

    save_data()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    auto_bake.start()

@bot.command()
async def cookie(ctx, sub: str = None, *args):
    user_id = str(ctx.author.id)
    if user_id not in user_data:
        user_data[user_id] = default_user_data()
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
        for upgrade in UPGRADES:
            if upgrade["increase"] is not None and upgrade["increase"] > 0:
                count = user.get(f"{upgrade['key']}_count", 0)
                if upgrade["key"].startswith("click_power"):
                    click_power += upgrade["increase"] * count

        mult_upgrade = next((u for u in UPGRADES if u["key"] == "click_multiplier_2x"), None)
        if mult_upgrade:
            count = user.get("click_multiplier_2x_count", 0)
            if count > 0:
                click_power = int(click_power * (mult_upgrade["multiplier"] ** count))

        # 自動焼きの効果を合算
        interval = 1.0
        amount = 0
        for upgrade in UPGRADES:
            count = user.get(f"{upgrade['key']}_count", 0)
            if count == 0:
                continue
            if upgrade["auto_interval"] is not None:
                interval = min(interval, upgrade["auto_interval"])
            if upgrade["auto_amount"] is not None:
                amount += upgrade["auto_amount"] * count
            elif upgrade["increase"] is not None:
                amount += upgrade["increase"] * count
        if amount == 0:
            amount = 1

        await ctx.send(
            f"📊 {ctx.author.display_name} さんのステータス\n"
            f"🍪 クッキー: {user['cookies']}\n"
            f"👆 クリック強さ: {click_power}\n"
            f"⏱️ 自動焼き: {interval}秒ごとに {amount}枚"
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
            count = user.get(f"{upgrade['key']}_count", 0)
            require = upgrade["requires"]
            can_buy = False
            if require is None or user.get(f"{require}_count", 0) > 0:
                can_buy = True
            else:
                can_buy = False
            cost = int(upgrade["base_cost"] * (upgrade.get("cost_increase_rate", 1.0) ** count))
            status = ""
            if count > 0:
                status = f"✅購入済み（レベル {count}）"
            elif can_buy:
                status = "🟢購入可能"
            else:
                status = "❌前アイテムを購入してください"
            msg += f"`{upgrade['key']}`: **{upgrade['item_name']}** - 💰 {cost}クッキー - {status}\n"
            msg += f"    説明: {upgrade['description']}\n"
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

        count_key = f"{item_key}_count"
        current_count = user.get(count_key, 0)

        # 必要なアップグレードの購入回数チェック
        requires = item["requires"]
        if requires is not None and user.get(f"{requires}_count", 0) == 0:
            required_name = next((u["item_name"] for u in UPGRADES if u["key"] == requires), requires)
            await ctx.send(f"❌ そのアイテムを購入するには「{required_name}」を先に買う必要があります。")
            return

        cost = int(item["base_cost"] * (item.get("cost_increase_rate", 1.0) ** current_count))

        if user["cookies"] < cost:
            await ctx.send(f"💸 クッキーが足りません！必要: {cost} クッキー")
            return

        # 購入処理
        user["cookies"] -= cost
        user[count_key] = current_count + 1

        save_data()
        await ctx.send(f"✅ 「{item['item_name']}」をレベル {user[count_key]} に上げました！ 次回は {int(cost * item.get('cost_increase_rate', 1.0))} クッキーです。")

    else:
        help_msg = (
            "❓ **クッキーボット ヘルプ**\n"
            "`!cookie button` - クッキーを焼くボタンを表示\n"
            "`!cookie stats` - 現在のクッキー数や能力を見る\n"
            "`!cookie rank` - クッキーランキングを表示\n"
            "`!cookie off` - 自動焼きを停止\n"
            "`!cookie on` - 自動焼きを再開\n"
            "`!cookie shop` - ショップ一覧を見る\n"
            "`!cookie buy <item_key>` - アイテムを購入\n"
            "`!cookie removebutton` - ボタン付きメッセージを削除\n"
            "`!cookie help` - このヘルプを表示\n"
        )
        await ctx.send(help_msg)

bot.run("")
