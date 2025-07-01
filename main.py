#とあるSさんからのタレコミでクッキーからコインに変えた。
#めんどくさかった。
import discord
from discord.ext import commands, tasks
from contest import (
    event_user_data,
    is_event_running,
    get_current_event_type,
    start_event,
    check_event_timeout,
    end_event,
    default_event_user_data,
    save_event_data
)
from contest import load_event_data
import json
import os
import random
import time

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MAIN_DATA_FILE = "cookie_data.json"
main_user_data = {}
# ==== プレイヤーデータ管理 ====
def load_main_data():
    global main_user_data
    if os.path.exists(MAIN_DATA_FILE):
        with open(MAIN_DATA_FILE, "r", encoding="utf-8") as f:
            main_user_data = json.load(f)
    else:
        main_user_data = {}

def save_main_data():
    with open(MAIN_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(main_user_data, f, indent=2, ensure_ascii=False)

load_main_data()
# ==== イベント監視タスク ====
@tasks.loop(seconds=1)
async def event_watcher():
    if is_event_running():
        event_type = check_event_timeout()
        if event_type:
            results, ended_type = end_event()

            # 処理：結果送信、報酬配布、データ復元など
            channel = discord.utils.get(bot.get_all_channels(), name="general")
            if channel:
                if ended_type == "contest":
                    sorted_results = sorted(results.items(), key=lambda x: x[1].get("cookies", 0), reverse=True)
                    top_user_id, top_data = sorted_results[0]
                    reward = 10_000_000

                    # 通常データに報酬を加算
                    if top_user_id in main_user_data:
                        main_user_data[top_user_id]["cookies"] += reward
                    else:
                        main_user_data[top_user_id] = default_event_user_data()
                        main_user_data[top_user_id]["cookies"] = reward

                    save_main_data()

                    await channel.send(f"🎉 コインコンテスト終了！<@{top_user_id}> が優勝し、{reward:,} コインを獲得しました！")
                elif ended_type == "cooperation":
                    total = sum([d.get("cookies", 0) for d in results.values()])
                    target = 1000
                    if total >= target:
                        reward_each = 1_000_000
                        for uid in results:
                            if uid in main_user_data:
                                main_user_data[uid]["cookies"] += reward_each
                            else:
                                main_user_data[uid] = default_event_user_data()
                                main_user_data[uid]["cookies"] = reward_each

                        save_main_data()
                        await channel.send(f"🤝 協力イベント成功！全体で {total:,} コインを集めました！参加者に {reward_each:,} コインずつ配布しました！")
                    else:
                        await channel.send(f"💔 協力イベント失敗... 合計 {total:,} コインでした。次こそ成功させよう！")

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
    # クリック強化系
    {
        "key": "click_power_1",
        "item_name": "手さばき強化 Lv1",
        "description": "クリック時のコイン増加量が+1ずつ増えます（購入回数に応じて効果上昇）",
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
        "item_name": "指先の極み Lv2",
        "description": "クリック時のコイン増加量が+2ずつ増えます（購入回数に応じて効果上昇）",
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
        "item_name": "技術スキルアップ Lv3",
        "description": "クリック時のコイン増加量が+5ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 800,
        "cost_increase_rate": 1.5,
        "increase": 5,
        "requires": "click_power_2",
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "click_power_4",
        "item_name": "コイン拳 Lv4",
        "description": "クリック時のコイン増加量が+10ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 2000,
        "cost_increase_rate": 1.5,
        "increase": 10,
        "requires": "click_power_3",
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "click_power_5",
        "item_name": "採掘職人の技 Lv5",
        "description": "クリック時のコイン増加量が+20ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 5000,
        "cost_increase_rate": 1.5,
        "increase": 20,
        "requires": "click_power_4",
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },

    # クリック倍率系
    {
        "key": "click_multiplier_2x",
        "item_name": "幸運アップ 2x",
        "description": "クリック時のコイン増加量の倍率が2倍ずつ上がります（購入回数に応じて倍率上昇）",
        "base_cost": 3000,
        "cost_increase_rate": 2.0,
        "increase": 0,
        "requires": "click_power_5",
        "multiplier": 2.0,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "click_multiplier_3x",
        "item_name": "幸運アップ 3x",
        "description": "クリック時のコイン増加量の倍率が3倍ずつ上がります（購入回数に応じて倍率上昇）",
        "base_cost": 9000,
        "cost_increase_rate": 2.0,
        "increase": 0,
        "requires": "click_multiplier_2x",
        "multiplier": 3.0,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "click_multiplier_4x",
        "item_name": "幸運アップ 4x",
        "description": "クリック時のコイン増加量の倍率が4倍ずつ上がります（購入回数に応じて倍率上昇）",
        "base_cost": 20000,
        "cost_increase_rate": 2.0,
        "increase": 0,
        "requires": "click_multiplier_3x",
        "multiplier": 4.0,
        "auto_interval": None,
        "auto_amount": None,
    },

    # 自動焼き速度系
    {
        "key": "auto_speed_1",
        "item_name": "マイニング Lv1",
        "description": "自動で採掘されるコインが秒毎に+1ずつ増えます（購入回数に応じて効果上昇）",
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
        "item_name": "マイニング Lv2",
        "description": "自動で採掘されるコインが秒毎に+2ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 1500,
        "cost_increase_rate": 1.5,
        "increase": 2,
        "requires": "auto_speed_1",
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "auto_speed_3",
        "item_name": "マイニング Lv3",
        "description": "自動で採掘されるコインが秒毎に+5ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 4000,
        "cost_increase_rate": 1.5,
        "increase": 5,
        "requires": "auto_speed_2",
        "multiplier": None,
        "auto_interval": None,
        "auto_amount": None,
    },

    # 高速自動焼きモード
    {
        "key": "auto_mode_fast_1",
        "item_name": "フレイムジェット Lv1",
        "description": "0.5秒ごとに2枚ずつ自動採掘が増えます（購入回数に応じて効果上昇）",
        "base_cost": 2500,
        "cost_increase_rate": 1.5,
        "increase": 0,
        "requires": "auto_speed_3",
        "multiplier": None,
        "auto_interval": 0.5,
        "auto_amount": 2,
    },
    {
        "key": "auto_mode_fast_2",
        "item_name": "フレイムジェット Lv2",
        "description": "0.4秒ごとに3枚ずつ自動採掘が増えます（購入回数に応じて効果上昇）",
        "base_cost": 7000,
        "cost_increase_rate": 1.5,
        "increase": 0,
        "requires": "auto_mode_fast_1",
        "multiplier": None,
        "auto_interval": 0.4,
        "auto_amount": 3,
    },
    {
        "key": "auto_mode_fast_3",
        "item_name": "フレイムジェット Lv3",
        "description": "0.3秒ごとに5枚ずつ自動採掘が増えます（購入回数に応じて効果上昇）",
        "base_cost": 15000,
        "cost_increase_rate": 1.5,
        "increase": 0,
        "requires": "auto_mode_fast_2",
        "multiplier": None,
        "auto_interval": 0.3,
        "auto_amount": 5,
    },

    # 超効率型焼きモード
    {
        "key": "auto_mode_efficiency_1",
        "item_name": "プレミアムピッケル Lv1",
        "description": "2秒ごとに10枚ずつ自動採掘が増えます（購入回数に応じて効果上昇）",
        "base_cost": 3000,
        "cost_increase_rate": 1.5,
        "increase": 0,
        "requires": "auto_mode_fast_3",
        "multiplier": None,
        "auto_interval": 2.0,
        "auto_amount": 10,
    },
    {
        "key": "auto_mode_efficiency_2",
        "item_name": "プレミアムピッケル Lv2",
        "description": "1.5秒ごとに15枚ずつ自動採掘が増えます（購入回数に応じて効果上昇）",
        "base_cost": 7000,
        "cost_increase_rate": 1.5,
        "increase": 0,
        "requires": "auto_mode_efficiency_1",
        "multiplier": None,
        "auto_interval": 1.5,
        "auto_amount": 15,
    },
    {
        "key": "auto_mode_efficiency_3",
        "item_name": "プレミアムピッケル Lv3",
        "description": "1秒ごとに25枚ずつ自動採掘が増えます（購入回数に応じて効果上昇）",
        "base_cost": 15000,
        "cost_increase_rate": 1.5,
        "increase": 0,
        "requires": "auto_mode_efficiency_2",
        "multiplier": None,
        "auto_interval": 1.0,
        "auto_amount": 25,
    },

    # ボーナス倍率系
    {
        "key": "bonus_multiplier_1",
        "item_name": "コインの祝福 +0.1%",
        "description": "コイン獲得量が0.1%ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 1000,
        "cost_increase_rate": 1.7,
        "increase": 0,
        "requires": None,
        "multiplier": 1.001,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "bonus_multiplier_2",
        "item_name": "コインの祝福 +0.2%",
        "description": "コイン獲得量が0.2%ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 3000,
        "cost_increase_rate": 1.7,
        "increase": 0,
        "requires": "bonus_multiplier_1",
        "multiplier": 1.002,
        "auto_interval": None,
        "auto_amount": None,
    },
    {
        "key": "bonus_multiplier_3",
        "item_name": "コインの祝福 +0.3%",
        "description": "コイン獲得量が0.3%ずつ増えます（購入回数に応じて効果上昇）",
        "base_cost": 7000,
        "cost_increase_rate": 1.7,
        "increase": 0,
        "requires": "bonus_multiplier_2",
        "multiplier": 1.003,  # ←ここを変更
        "auto_interval": None,
        "auto_amount": None,
    },
]


class CookieButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(self.BakeButton())

    class BakeButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="🔥 コインを掘る！", style=discord.ButtonStyle.primary, custom_id="cookie_bake")

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
                f"🪙 コインを見つけた！（+{click_power}）現在のコイン数: {user['cookies']}", ephemeral=True
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
    event_watcher.start()

@bot.command()
async def coin(ctx, sub: str = None, *args):
    user_id = str(ctx.author.id)
    if user_id not in user_data:
        user_data[user_id] = default_user_data()
        save_data()

    user = user_data[user_id]

    if sub == "button":
        view = CookieButton()
        await ctx.send("🪙 コインを掘り出そう！下のボタンを押してね👇", view=view)
    elif sub == "info":
        if not args:
            await ctx.send("❗使用方法: `/coin info <アイテム名 or 番号>`")
            return

        query = " ".join(args).lower()
        user_id = str(ctx.author.id)
        user = user_data.get(user_id, default_user_data())

        target_upgrade = None

        if query.isdigit():
            index = int(query) - 1
            if 0 <= index < len(UPGRADES):
                target_upgrade = UPGRADES[index]
        else:
            for upgrade in UPGRADES:
                if query in upgrade["item_name"].lower() or query in upgrade["key"].lower():
                    target_upgrade = upgrade
                    break

        if target_upgrade is None:
            await ctx.send("⚠️ そのアイテムは見つかりませんでした。")
            return

        requires = target_upgrade.get("requires")
        owned = user.get(f"{target_upgrade['key']}_count", 0)
        if requires and user.get(f"{requires}_count", 0) == 0 and owned == 0:
            embed = discord.Embed(
                title="❓ 未知のアイテム",
                description="前提のアイテムが必要です。\nこのアイテムの詳細を見るには、先に前提アイテムを購入してください。",
                color=discord.Color.dark_gray()
            )
            embed.set_footer(text=f"必要アイテム: {next((u['item_name'] for u in UPGRADES if u['key'] == requires), requires)}")
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"📦 {target_upgrade['item_name']}",
            description=target_upgrade["description"],
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)


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
            f"🪙 コイン: {user['cookies']}\n"
            f"👆 クリック強さ: {click_power}\n"
            f"⏱️ 自動採掘: {interval}秒ごとに {amount}枚"
        )

    elif sub == "rank":
        sorted_users = sorted(user_data.items(), key=lambda x: x[1].get("cookies", 0), reverse=True)
        top = sorted_users[:10]
        msg = "🥇 **コインランキング** 🥇\n"
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
                    msg += f"\n📍 あなたの順位：{i} 位（🪙 {data.get('cookies', 0)} 枚）"
                    break
        await ctx.send(msg)

    elif sub == "off":
        user["auto"] = False
        save_data()
        await ctx.send("⏸️ 自動採掘を停止しました。")

    elif sub == "on":
        user["auto"] = True
        save_data()
        await ctx.send("▶️ 自動採掘を再開しました。")

    elif sub == "shop":
        embed = discord.Embed(
            title="🛍️ コインショップ",
            description="アップグレード一覧です。番号またはキーで購入できます。",
            color=discord.Color.gold()
        )

        for index, upgrade in enumerate(UPGRADES, 1):
            owned = user.get(f"{upgrade['key']}_count", 0)
            requires = upgrade["requires"]
            can_buy = requires is None or user.get(f"{requires}_count", 0) > 0

            cost = int(upgrade["base_cost"] * (upgrade["cost_increase_rate"] ** owned))

            if not can_buy and owned == 0:
                name = f"**{index}. 未知のアイテム** (`{upgrade['key']}`)"
                status = "❌ 前提未達"
            else:
                name = f"**{index}. {upgrade['item_name']}** (`{upgrade['key']}`)"
                status = (
                    f"✅ 購入済（{owned}回）" if owned > 0
                    else "🟢 購入可能" if can_buy
                    else "❌ 前提未達"
                )

            embed.add_field(
                name=name,
                value=f"💰 {cost:,} - {status}",
                inline=False
            )

        embed.set_footer(text="購入: !coin buy <番号 or item_key> ｜ アイテム情報: !coin info <item_key>")
        await ctx.send(embed=embed)

    if sub == "start":
        if is_event_running():
            await ctx.send("⚠️ イベントはすでに進行中です！")
            return

        # イベント用データを読み込む
        load_event_data()  # もしモジュール分割してたら event.load_event_data()

        started = start_event()
        if not started:
            await ctx.send("⚠️ イベント開始に失敗しました。")
            return

        mode = get_current_event_type()
        if mode == "contest":
            await ctx.send("📢 **コインコンテスト**が始まりました！10分以内に最も多く稼いだ人が勝者です！")
        elif mode == "cooperation":
            await ctx.send("🤝 **協力イベント**が始まりました！みんなで3分間で1000コインを集めよう！")

    elif sub == "data":
        await ctx.send(json.dumps(event_user_data, indent=2, ensure_ascii=False))

    elif sub == "buy":
        if len(args) != 1:
            await ctx.send("🛒 使い方: `!coin buy <番号またはitem_key>` です。")
            return

        arg = args[0]
        item = None

        # 数字かどうかで分岐（番号指定）
        if arg.isdigit():
            index = int(arg) - 1
            if 0 <= index < len(UPGRADES):
                item = UPGRADES[index]
            else:
                await ctx.send("❌ 指定された番号のアイテムは存在しません。")
                return
        else:
            item = next((u for u in UPGRADES if u["key"] == arg), None)
            if not item:
                await ctx.send("❌ そのアイテムは存在しません。`!coin shop` で確認してください。")
                return

        item_key = item["key"]
        count_key = f"{item_key}_count"
        current_count = user.get(count_key, 0)

        requires = item["requires"]
        if requires is not None and user.get(f"{requires}_count", 0) == 0:
            required_name = next((u["item_name"] for u in UPGRADES if u["key"] == requires), requires)
            await ctx.send(f"❌ そのアイテムを購入するには「{required_name}」を先に買う必要があります。")
            return

        cost = int(item["base_cost"] * (item.get("cost_increase_rate", 1.0) ** current_count))

        if user["cookies"] < cost:
            await ctx.send(f"💸 コインが足りません！必要: {cost} コイン")
            return

        # 購入処理
        user["cookies"] -= cost
        user[count_key] = current_count + 1

        save_data()
        await ctx.send(f"✅ 「{item['item_name']}」をレベル {user[count_key]} に上げました！ 次回は {int(cost * item.get('cost_increase_rate', 1.0))} コインです。")

    else:
        help_msg = (
            "❓ **コインボット ヘルプ**\n"
            "`!coin button` - クッキーを焼くボタンを表示\n"
            "`!coin info アイテム名例(click_power_1)` - アイテムの説明を見る\n"
            "`!coin stats` - 現在のクッキー数や能力を見る\n"
            "`!coin rank` - クッキーランキングを表示\n"
            "`!coin off` - 自動焼きを停止\n"
            "`!coin on` - 自動焼きを再開\n"
            "`!coin shop` - ショップ一覧を見る\n"
            "`!coin buy <item_key>` - アイテムを購入\n"
            "`!coin removebutton` - ボタン付きメッセージを削除\n"
            "`!coin help` - このヘルプを表示\n"
        )
        await ctx.send(help_msg)

