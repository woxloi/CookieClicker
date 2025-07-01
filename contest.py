import json
import os
import random
import time

EVENT_DATA_FILE = "event_data.json"
event_user_data = {}

event_running = False
event_type = None  # "contest" または "cooperation"
event_end_time = 0


def load_event_data():
    global event_user_data
    if os.path.exists(EVENT_DATA_FILE):
        with open(EVENT_DATA_FILE, "r", encoding="utf-8") as f:
            event_user_data = json.load(f)
    else:
        event_user_data = {}


def save_event_data():
    with open(EVENT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(event_user_data, f, indent=2, ensure_ascii=False)


def clear_event_data():
    global event_user_data
    event_user_data = {}
    save_event_data()


def default_event_user_data():
    return {
        "cookies": 0,
        **{f"{key}_count": 0 for key in [
            "click_power_1", "click_power_2", "click_power_3", "click_power_4", "click_power_5",
            "click_multiplier_2x", "click_multiplier_3x", "click_multiplier_4x",
            "auto_speed_1", "auto_speed_2", "auto_speed_3",
            "auto_mode_fast_1", "auto_mode_fast_2", "auto_mode_fast_3",
            "auto_mode_efficiency_1", "auto_mode_efficiency_2", "auto_mode_efficiency_3",
            "bonus_multiplier_1", "bonus_multiplier_2", "bonus_multiplier_3"
        ]}
    }


def start_event():
    global event_running, event_type, event_end_time
    if event_running:
        return False  # すでにイベント中

    clear_event_data()
    event_running = True
    event_type = random.choice(["contest", "cooperation"])
    event_end_time = time.time() + (180 if event_type == "cooperation" else 600)  # 協力:3分、コンテスト:10分
    return True


def is_event_running():
    return event_running


def get_current_event_type():
    return event_type


def check_event_timeout():
    if not event_running:
        return None
    if time.time() >= event_end_time:
        return event_type
    return None


def end_event():
    global event_running, event_type, event_end_time

    event_running = False
    t = event_type
    event_type = None
    event_end_time = 0

    results = event_user_data.copy()
    clear_event_data()

    return results, t


# ここから追加分 ------------------------------------------

async def send_mid_event_report(ctx):
    """
    イベント中間発表をDiscordのctxに送信する関数。
    イベント進行中なら上位3名の獲得コイン数を表示する。
    """
    if not is_event_running():
        await ctx.send("⚠️ イベントは現在開催されていません。")
        return

    if not event_user_data:
        await ctx.send("まだ参加者がいません。")
        return

    # cookies数で降順ソート
    sorted_users = sorted(
        event_user_data.items(),
        key=lambda x: x[1].get("cookies", 0),
        reverse=True
    )

    report_lines = ["📊 **イベント中間発表** 📊"]
    for i, (user_id, data) in enumerate(sorted_users[:3], 1):
        cookies = data.get("cookies", 0)
        # DiscordのユーザーIDとしてメンション形式にして送信
        report_lines.append(f"{i}位: <@{user_id}> さん - コイン {cookies}枚")

    await ctx.send("\n".join(report_lines))
NORMAL_DATA_FILE = "cookie_data.json"
EVENT_DATA_FILE = "event_data.json"

def load_data():
    filename = EVENT_DATA_FILE if event_running else NORMAL_DATA_FILE
    global event_user_data
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            event_user_data = json.load(f)
    else:
        event_user_data = {}

def save_data():
    filename = EVENT_DATA_FILE if event_running else NORMAL_DATA_FILE
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(event_user_data, f, indent=2, ensure_ascii=False)

def clear_data():
    global event_user_data
    event_user_data = {}
    save_data()
