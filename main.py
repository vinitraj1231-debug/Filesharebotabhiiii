"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 ULTRA ADVANCED MULTI-LEVEL FILESTORE BOT - FULLY FIXED v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL BUGS FIXED
✅ VIDEO/PHOTO CAPTION PRESERVED
✅ CLONE SYSTEM & MULTI-LEVEL BATCHING
✅ ANTI-FLOOD WITH PROPER PROPAGATION
✅ GLOBAL BAN / FORCE SUB MULTI-CHANNEL
✅ SHORTENER, REFERRAL, PREMIUM SYSTEM
✅ SEND_CACHED_MEDIA FIXED
✅ ASYNCIO.RUN() FIXED
✅ DUPLICATE CALLBACKS FIXED
✅ PRODUCTION READY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import json
import asyncio
import hashlib
import logging
import random
import shutil
import time
import aiohttp
from datetime import datetime, timedelta
from pyrogram import Client, filters, idle
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, BotCommand,
    InlineQueryResultArticle, InputTextMessageContent
)
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, InlineQueryHandler, ChatJoinRequestHandler

# ═══════════════════════════════════════════════════════════════
# 🔧 CONFIGURATION
# ═══════════════════════════════════════════════════════════════

API_ID = 23790796
API_HASH = "626eb31c9057007df4c2851b3074f27f"
MAIN_BOT_TOKEN = "8607033631:AAEEHymSzeLeP8wpH1TR4vnZSyai3kI1DTE"
MAIN_ADMIN = 8756786934
DB_CHANNEL = -1003982754680

FILE_CACHE_DURATION = 60 * 60  # 60 minutes
MAX_FORCE_SUB_CHANNELS = 3
MAX_FILE_SIZE_MB = 2000  # 2GB Telegram limit

DB_FOLDER = "database"
FILES_DB = f"{DB_FOLDER}/files.json"
BATCH_DB = f"{DB_FOLDER}/batches.json"
BOTS_DB = f"{DB_FOLDER}/bots.json"
USERS_DB = f"{DB_FOLDER}/users.json"
ADMINS_DB = f"{DB_FOLDER}/admins.json"
FILE_CACHE_DB = f"{DB_FOLDER}/file_cache.json"
CONFIG_DB = f"{DB_FOLDER}/config.json"

BOT_COMMANDS = [
    BotCommand("start", "🚀 Start the bot"),
    BotCommand("admin", "⚡ Admin Panel"),
    BotCommand("supreme", "👑 Supreme Panel"),
    BotCommand("clone", "🤖 Clone your own bot"),
    BotCommand("batch", "📦 Create batch files"),
    BotCommand("done", "✅ Finish batch"),
    BotCommand("cancel", "❌ Cancel operation"),
    BotCommand("setfs", "⚙️ Set force subscribe"),
    BotCommand("mybots", "🤖 Your cloned bots"),
    BotCommand("stats", "📊 View statistics"),
    BotCommand("help", "ℹ️ Help & guide"),
    BotCommand("broadcast", "📢 Broadcast message"),
    BotCommand("ban", "🚫 Ban user"),
    BotCommand("unban", "✅ Unban user"),
    BotCommand("setmsg", "💬 Custom welcome"),
    BotCommand("botinfo", "ℹ️ Bot information"),
    BotCommand("settimer", "⏱ Set auto-delete timer"),
    BotCommand("setwelcomeimg", "🖼 Set welcome image"),
    BotCommand("search", "🔍 Search for files"),
    BotCommand("points", "💰 Check your points"),
    BotCommand("refer", "🔗 Referral link"),
    BotCommand("premium", "🌟 Premium details"),
    BotCommand("shortener", "🔗 Manage URL Shortener"),
    BotCommand("buy_premium", "🎁 Buy Premium with Points"),
    BotCommand("setlog", "📝 Set Log Channel"),
    BotCommand("restart", "🔄 Restart all bots (Supreme Only)"),
    BotCommand("ping", "🏓 Check bot latency"),
    BotCommand("delfile", "🗑 Delete a file"),
    BotCommand("listfiles", "📋 List your files"),
    BotCommand("addpoints", "💰 Add points to user (Admin)"),
]

# ═══════════════════════════════════════════════════════════════
# 📝 LOGGING
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FileStore")

# ═══════════════════════════════════════════════════════════════
# 💾 DATABASE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

os.makedirs(DB_FOLDER, exist_ok=True)
DB_CACHE = {}
GLOBAL_CONFIG_CACHE = {}

def load_db(filename):
    if filename in DB_CACHE:
        return DB_CACHE[filename]
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump({}, f)
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            DB_CACHE[filename] = data
            return data
    except Exception:
        return {}

def save_db(filename, data):
    DB_CACHE[filename] = data
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def get_global_config():
    global GLOBAL_CONFIG_CACHE
    if not GLOBAL_CONFIG_CACHE:
        GLOBAL_CONFIG_CACHE = load_db(CONFIG_DB)
    return GLOBAL_CONFIG_CACHE

def update_global_config(key, value):
    global GLOBAL_CONFIG_CACHE
    config = load_db(CONFIG_DB)
    config[key] = value
    save_db(CONFIG_DB, config)
    GLOBAL_CONFIG_CACHE = config

async def backup_db_to_telegram():
    main_client = None
    for bid, bdata in ACTIVE_CLIENTS.items():
        if bdata.get("is_main"):
            main_client = bdata["app"]
            break
    if not main_client:
        return
    try:
        for file in os.listdir(DB_FOLDER):
            if file.endswith(".json"):
                await main_client.send_document(
                    DB_CHANNEL,
                    document=f"{DB_FOLDER}/{file}",
                    caption=(
                        f"📂 **Database Backup**\n"
                        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"📄 `{file}`"
                    )
                )
    except Exception as e:
        logger.error(f"Backup failed: {e}")

# ─── USER FUNCTIONS ─────────────────────────────────────────────

def add_user(user_id, bot_id, username=None, name=None, referred_by=None):
    users = load_db(USERS_DB)
    user_key = f"{bot_id}_{user_id}"
    is_new = user_key not in users
    if is_new:
        users[user_key] = {
            "user_id": user_id, "bot_id": bot_id,
            "username": username, "name": name,
            "join_date": str(datetime.now()),
            "is_banned": False, "files_uploaded": 0,
            "batches_created": 0, "bots_cloned": 0,
            "referred_by": referred_by, "referrals": 0,
            "points": 0, "is_premium": False
        }
        save_db(USERS_DB, users)
        if referred_by and referred_by != user_id:
            ref_key = f"{bot_id}_{referred_by}"
            if ref_key in users:
                users[ref_key]["referrals"] = users[ref_key].get("referrals", 0) + 1
                users[ref_key]["points"] = users[ref_key].get("points", 0) + 10
                save_db(USERS_DB, users)
    return users[user_key], is_new

def get_user(user_id, bot_id):
    return load_db(USERS_DB).get(f"{bot_id}_{user_id}")

def update_user_stats(user_id, bot_id, field, delta=1):
    users = load_db(USERS_DB)
    key = f"{bot_id}_{user_id}"
    if key in users:
        users[key][field] = users[key].get(field, 0) + delta
        save_db(USERS_DB, users)

def is_user_banned(user_id, bot_id):
    config = get_global_config()
    if user_id in config.get("global_bans", []):
        return True
    user = get_user(user_id, bot_id)
    return user.get("is_banned", False) if user else False

def ban_user(user_id, bot_id):
    users = load_db(USERS_DB)
    key = f"{bot_id}_{user_id}"
    if key in users:
        users[key]["is_banned"] = True
        save_db(USERS_DB, users)
        return True
    return False

def unban_user(user_id, bot_id):
    users = load_db(USERS_DB)
    key = f"{bot_id}_{user_id}"
    if key in users:
        users[key]["is_banned"] = False
        save_db(USERS_DB, users)
        return True
    return False

def get_all_users(bot_id=None):
    users = load_db(USERS_DB)
    if bot_id:
        return [u for u in users.values() if u['bot_id'] == bot_id and not u.get('is_banned')]
    return [u for u in users.values() if not u.get('is_banned')]

def is_admin(user_id):
    return user_id == MAIN_ADMIN or str(user_id) in load_db(ADMINS_DB)

# ─── BOT INFO FUNCTIONS ─────────────────────────────────────────

def save_bot_info(token, bot_id, bot_username, owner_id, owner_name, parent_bot_id=None):
    bots = load_db(BOTS_DB)
    bots[str(bot_id)] = {
        "token": token, "bot_id": bot_id,
        "bot_username": bot_username, "owner_id": owner_id,
        "owner_name": owner_name, "parent_bot_id": parent_bot_id,
        "created_on": str(datetime.now()), "is_active": True,
        "custom_welcome": None, "welcome_image": None,
        "auto_delete_time": 600, "auto_approve": False,
        "force_subs": [], "shortener_api": None,
        "shortener_url": None, "is_shortener_enabled": False,
        "log_channel": None
    }
    save_db(BOTS_DB, bots)
    if parent_bot_id:
        update_user_stats(owner_id, parent_bot_id, "bots_cloned")

def get_bot_info(bot_id):
    return load_db(BOTS_DB).get(str(bot_id))

def update_bot_info(bot_id, field, value):
    bots = load_db(BOTS_DB)
    if str(bot_id) in bots:
        bots[str(bot_id)][field] = value
        save_db(BOTS_DB, bots)
        return True
    return False

def get_all_bots():
    return load_db(BOTS_DB)

def get_child_bots(parent_bot_id):
    bots = load_db(BOTS_DB)
    return [b for b in bots.values() if isinstance(b, dict) and b.get('parent_bot_id') == parent_bot_id]

def get_all_descendant_bots(parent_bot_id):
    all_desc = []
    def recurse(bid):
        for child in get_child_bots(bid):
            all_desc.append(child)
            recurse(child['bot_id'])
    recurse(parent_bot_id)
    return all_desc

def cascade_force_subs(parent_bot_id, force_subs):
    descendants = get_all_descendant_bots(parent_bot_id)
    bots = load_db(BOTS_DB)
    count = 0
    for bot in descendants:
        k = str(bot['bot_id'])
        if k in bots:
            bots[k]['force_subs'] = force_subs
            count += 1
    save_db(BOTS_DB, bots)
    return count

# ─── FILE CACHE ─────────────────────────────────────────────────

def add_to_cache(file_id, message_id, chat_id, bot_id, caption=None):
    cache = load_db(FILE_CACHE_DB)
    cache[file_id] = {
        "message_id": message_id, "chat_id": chat_id,
        "bot_id": bot_id, "caption": caption,
        "cached_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(seconds=FILE_CACHE_DURATION)).isoformat()
    }
    save_db(FILE_CACHE_DB, cache)

def get_from_cache(file_id):
    cache = load_db(FILE_CACHE_DB)
    if file_id not in cache:
        return None
    try:
        expires_at = datetime.fromisoformat(cache[file_id]['expires_at'])
        if datetime.now() > expires_at:
            del cache[file_id]
            save_db(FILE_CACHE_DB, cache)
            return None
        return cache[file_id]
    except Exception:
        return None

def clean_expired_cache():
    cache = load_db(FILE_CACHE_DB)
    expired = [
        k for k, v in cache.items()
        if datetime.now() > datetime.fromisoformat(v.get('expires_at', '2000-01-01'))
    ]
    for k in expired:
        del cache[k]
    if expired:
        save_db(FILE_CACHE_DB, cache)
    return len(expired)

# ─── UTILITIES ──────────────────────────────────────────────────

def format_size(size):
    if not size:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

def get_unique_id():
    return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:12]

def get_file_type_icon(file_name):
    if not file_name:
        return "📁"
    ext = file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
    icons = {
        'pdf': '📄', 'doc': '📝', 'docx': '📝', 'txt': '📃',
        'mp4': '🎬', 'mkv': '🎬', 'avi': '🎬', 'mov': '🎬',
        'mp3': '🎵', 'flac': '🎵', 'wav': '🎵', 'aac': '🎵',
        'jpg': '🖼', 'jpeg': '🖼', 'png': '🖼', 'gif': '🖼',
        'zip': '🗜', 'rar': '🗜', '7z': '🗜', 'tar': '🗜',
        'apk': '📱', 'exe': '💻', 'py': '🐍',
    }
    return icons.get(ext, '📁')

async def get_short_link(bot_info, link):
    if not (bot_info and bot_info.get("is_shortener_enabled")
            and bot_info.get("shortener_api") and bot_info.get("shortener_url")):
        return link
    api_url = f"https://{bot_info['shortener_url']}/api?api={bot_info['shortener_api']}&url={link}"
    try:
        session = await get_http_session()
        async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            data = await resp.json()
            if data.get("status") == "success":
                return data.get("shortenedUrl", link)
    except Exception as e:
        logger.warning(f"Shortener failed: {e}")
    return link

def get_main_bot_username():
    """FIX: Get main bot username from ACTIVE_CLIENTS (not MAIN_ADMIN user ID)."""
    for bid, bdata in ACTIVE_CLIENTS.items():
        if bdata.get("is_main"):
            return bdata.get("username")
    return "Admin"

# ═══════════════════════════════════════════════════════════════
# 🤖 BOT MANAGEMENT
# ═══════════════════════════════════════════════════════════════

START_TIME = datetime.now()
ACTIVE_CLIENTS = {}
TEMP_BATCH_DATA = {}
TEMP_BROADCAST_DATA = {}
USER_FLOOD = {}  # {user_id: [timestamps]}
HTTP_SESSION = None

async def get_http_session():
    global HTTP_SESSION
    if HTTP_SESSION is None or HTTP_SESSION.closed:
        HTTP_SESSION = aiohttp.ClientSession()
    return HTTP_SESSION

async def setup_bot_commands(app):
    try:
        await app.set_bot_commands(BOT_COMMANDS)
    except Exception as e:
        logger.warning(f"Commands setup error: {e}")

async def check_force_sub(client, user_id):
    """
    FIX: Returns (True, []) if subscribed, (False, links) if not.
    Previously returned (True, []) when not subscribed but links were empty — WRONG.
    """
    bot_info = get_bot_info(client.me.id)
    if not bot_info:
        return True, []

    force_subs = bot_info.get("force_subs", [])
    if not force_subs:
        return True, []

    must_join = []
    for fs in force_subs:
        channel_id = fs["channel_id"] if isinstance(fs, dict) else fs
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status in [
                ChatMemberStatus.BANNED,
                ChatMemberStatus.LEFT,
            ]:
                must_join.append(fs)
            # OWNER, ADMINISTRATOR, MEMBER are all OK
        except UserNotParticipant:
            must_join.append(fs)
        except Exception:
            continue  # Can't check — skip this channel

    if not must_join:
        return True, []

    links = []
    for fs in must_join:
        channel_id = fs["channel_id"] if isinstance(fs, dict) else fs
        invite_link = fs.get("invite_link") if isinstance(fs, dict) else None
        try:
            chat = await client.get_chat(channel_id)
            if not invite_link:
                invite_link = chat.invite_link or (
                    f"https://t.me/{chat.username}" if chat.username else None
                )
            if invite_link:
                links.append({"title": chat.title, "link": invite_link})
        except Exception:
            continue

    # FIX: Return (False, ...) regardless of whether links were found
    return False, links

async def broadcast_message(original_msg, bot_ids=None, status_msg=None):
    if bot_ids is None:
        bot_ids = list(ACTIVE_CLIENTS.keys())

    total_bots = len(bot_ids)
    success, failed = 0, 0
    start_time = datetime.now()

    for b_idx, bot_id in enumerate(bot_ids, 1):
        if bot_id not in ACTIVE_CLIENTS:
            continue
        client_data = ACTIVE_CLIENTS[bot_id]
        users = get_all_users(bot_id)

        for u_idx, user in enumerate(users, 1):
            try:
                await original_msg.copy(user['user_id'])
                success += 1
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
                try:
                    await original_msg.copy(user['user_id'])
                    success += 1
                except Exception:
                    failed += 1
            except Exception:
                failed += 1

            if status_msg and (success + failed) % 25 == 0:
                try:
                    elapsed = (datetime.now() - start_time).seconds
                    done = success + failed
                    total_est = sum(len(get_all_users(bid)) for bid in bot_ids)
                    pct = int((done / total_est) * 100) if total_est else 0
                    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
                    await status_msg.edit(
                        f"📢 **Broadcast Progress**\n\n"
                        f"`[{bar}]` {pct}%\n\n"
                        f"🤖 Bot: {b_idx}/{total_bots} (@{client_data['username']})\n"
                        f"✅ Success: `{success}`  ❌ Failed: `{failed}`\n"
                        f"⏱ Elapsed: `{elapsed}s`"
                    )
                except Exception:
                    pass
            await asyncio.sleep(0.05)

    return success, failed

async def start_bot(token, parent_bot_id=None):
    try:
        app = Client(
            f"bot_{token.split(':')[0]}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=token,
            in_memory=True
        )
        await app.start()
        me = await app.get_me()
        await setup_bot_commands(app)

        is_main = token == MAIN_BOT_TOKEN
        ACTIVE_CLIENTS[me.id] = {
            "app": app, "username": me.username,
            "is_main": is_main, "token": token,
            "parent_bot_id": parent_bot_id,
            "started_at": datetime.now()
        }

        register_handlers(app)
        logger.info(f"✅ {'[MAIN]' if is_main else '[CHILD]'} @{me.username} started")
        return app
    except Exception as e:
        logger.error(f"Bot start failed [{token[:10]}...]: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# 🎨 UI KEYBOARDS
# ═══════════════════════════════════════════════════════════════

def get_start_keyboard(bot_id, user_id):
    buttons = []
    bot_info = get_bot_info(bot_id)
    is_owner = bot_info and bot_info.get('owner_id') == user_id

    if user_id == MAIN_ADMIN:
        buttons.append([InlineKeyboardButton("👑 SUPREME PANEL", callback_data="supreme_panel")])
    if is_admin(user_id) or is_owner:
        buttons.append([InlineKeyboardButton("⚡ ADMIN PANEL", callback_data="admin_panel")])

    buttons.extend([
        [InlineKeyboardButton("📦 BATCH", callback_data="start_batch"),
         InlineKeyboardButton("🤖 CLONE", callback_data="clone_menu")],
        [InlineKeyboardButton("📊 DASHBOARD", callback_data="user_dashboard"),
         InlineKeyboardButton("🎁 REFERRAL", callback_data="referral_menu")],
        [InlineKeyboardButton("🎯 MY BOTS", callback_data="my_bots_menu"),
         InlineKeyboardButton("⚙️ SETTINGS", callback_data="bot_settings")],
        [InlineKeyboardButton("💎 PREMIUM", callback_data="premium_menu"),
         InlineKeyboardButton("ℹ️ HELP", callback_data="help_menu")],
    ])
    return InlineKeyboardMarkup(buttons)

def get_admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 BROADCAST", callback_data="broadcast_menu"),
         InlineKeyboardButton("📊 BOT STATS", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 MANAGE USERS", callback_data="manage_users"),
         InlineKeyboardButton("🤖 CLONED BOTS", callback_data="my_bots_admin")],
        [InlineKeyboardButton("⚙️ BOT SETTINGS", callback_data="bot_settings_admin"),
         InlineKeyboardButton("🔒 FORCE SUB", callback_data="forcesub_admin")],
        [InlineKeyboardButton("🔗 SHORTENER", callback_data="shortener_admin"),
         InlineKeyboardButton("⏱ DELETE TIMER", callback_data="edit_timer")],
        [InlineKeyboardButton("🖼 WELCOME IMG", callback_data="set_welcome_img"),
         InlineKeyboardButton("✅ AUTO APPROVE", callback_data="toggle_auto_approve")],
        [InlineKeyboardButton("🔙 BACK TO HOME", callback_data="back_to_start")],
    ])

def get_supreme_panel_keyboard():
    config = get_global_config()
    maint = config.get("maintenance", False)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 GLOBAL BROADCAST", callback_data="global_broadcast"),
         InlineKeyboardButton("🖥 SYSTEM STATS", callback_data="system_stats")],
        [InlineKeyboardButton("🤖 ALL BOTS", callback_data="all_bots_list"),
         InlineKeyboardButton("👑 ADMINS", callback_data="manage_admins")],
        [InlineKeyboardButton(
            f"🛠 MAINTENANCE: {'ON' if maint else 'OFF'}",
            callback_data="toggle_maintenance"
        ),
         InlineKeyboardButton("📢 GLOBAL MSG", callback_data="global_msg_set")],
        [InlineKeyboardButton("💾 BACKUP DB", callback_data="manual_backup"),
         InlineKeyboardButton("🧹 CLEAN CACHE", callback_data="manual_clean_cache")],
        [InlineKeyboardButton("🔄 RESTART SYSTEM", callback_data="restart_all_bots")],
        [InlineKeyboardButton("🔙 BACK TO HOME", callback_data="back_to_start")],
    ])

# ═══════════════════════════════════════════════════════════════
# 📝 HANDLERS
# ═══════════════════════════════════════════════════════════════

def register_handlers(app: Client):

    # ── FLOOD CONTROL (Group 0 — runs before commands) ──────────
    @app.on_message(filters.private, group=0)
    async def flood_control_handler(client, message):
        user_id = message.from_user.id
        now = time.time()

        if user_id not in USER_FLOOD:
            USER_FLOOD[user_id] = []

        # Keep only timestamps within last 5 seconds
        USER_FLOOD[user_id] = [t for t in USER_FLOOD[user_id] if now - t < 5]
        USER_FLOOD[user_id].append(now)

        if len(USER_FLOOD[user_id]) > 5:
            await message.reply(
                "⚠️ **Anti-Flood!** Aap bahut tez message kar rahe hain. Thoda ruko."
            )
            message.stop_propagation()

    # ── JOIN REQUEST AUTO-APPROVE ────────────────────────────────
    @app.on_chat_join_request()
    async def join_request_handler(client, request):
        bot_info = get_bot_info(client.me.id)
        if bot_info and bot_info.get("auto_approve"):
            try:
                await client.approve_chat_join_request(request.chat.id, request.from_user.id)
            except Exception as e:
                logger.warning(f"Auto-approve failed: {e}")

    # ── /ping ────────────────────────────────────────────────────
    @app.on_message(filters.command("ping") & filters.private, group=1)
    async def ping_cmd(client, message):
        start = time.time()
        sent = await message.reply("🏓 Pong...")
        ms = round((time.time() - start) * 1000, 2)
        uptime = str(datetime.now() - START_TIME).split('.')[0]
        await sent.edit(
            f"🏓 **Pong!**\n\n"
            f"⚡ Latency: `{ms}ms`\n"
            f"⏳ Uptime: `{uptime}`\n"
            f"🤖 Bots Online: `{len(ACTIVE_CLIENTS)}`"
        )

    # ── /restart ─────────────────────────────────────────────────
    @app.on_message(filters.command("restart") & filters.private, group=1)
    async def restart_cmd(client, message):
        if message.from_user.id != MAIN_ADMIN:
            return
        await message.reply("🔄 Restarting system...")
        logger.info("System restart triggered.")
        os.execl(sys.executable, sys.executable, *sys.argv)

    # ── /start ───────────────────────────────────────────────────
    @app.on_message(filters.command("start") & filters.private, group=1)
    async def start_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id

        config = get_global_config()
        if config.get("maintenance") and user_id != MAIN_ADMIN:
            return await message.reply(
                "🚧 **Maintenance Mode**\n\nBot temporarily down. Please try later."
            )

        if is_user_banned(user_id, bot_id):
            return await message.reply("🚫 You are banned from this bot!")

        # Parse referral
        referred_by = None
        deep_arg = message.command[1] if len(message.command) > 1 else ""
        if deep_arg.startswith("ref_"):
            try:
                ref_id = int(deep_arg[4:])
                if ref_id != user_id:
                    referred_by = ref_id
            except ValueError:
                pass

        user_data, is_new = add_user(
            user_id, bot_id,
            message.from_user.username,
            message.from_user.first_name,
            referred_by
        )

        # Force Subscribe check
        is_subbed, sub_links = await check_force_sub(client, user_id)
        if not is_subbed:
            buttons = [
                [InlineKeyboardButton(f"📢 Join {item['title']}", url=item['link'])]
                for item in sub_links
            ]
            retry_url = f"https://t.me/{client.me.username}?start={deep_arg}"
            buttons.append([InlineKeyboardButton("🔄 I Joined — Try Again", url=retry_url)])
            return await message.reply(
                "⚠️ **Force Subscribe Required!**\n\n"
                "Please join the channels below to use this bot:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        # Handle deep links
        bot_info = get_bot_info(bot_id)  # Single call — FIX
        auto_delete_time = bot_info.get("auto_delete_time", 600) if bot_info else 600

        if deep_arg.startswith("f_"):
            unique_id = deep_arg[2:]
            files = load_db(FILES_DB)
            file_data = files.get(unique_id)

            if not file_data:
                return await message.reply("❌ File not found or has been deleted.")

            # Increment access count
            files[unique_id]["access_count"] = files[unique_id].get("access_count", 0) + 1
            save_db(FILES_DB, files)

            sent_msg = None

            # 1. Try DB Channel copy (most reliable)
            try:
                sent_msg = await client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=DB_CHANNEL,
                    message_id=file_data['db_msg_id'],
                    caption=file_data.get('caption')
                )
            except Exception as e1:
                logger.warning(f"DB Channel copy failed: {e1}")

            # 2. Try cache
            if not sent_msg:
                cached = get_from_cache(file_data['file_id'])
                if cached and cached['bot_id'] in ACTIVE_CLIENTS:
                    try:
                        cached_app = ACTIVE_CLIENTS[cached['bot_id']]['app']
                        sent_msg = await cached_app.copy_message(
                            message.chat.id,
                            cached['chat_id'],
                            cached['message_id'],
                            caption=file_data.get('caption')
                        )
                    except Exception as e2:
                        logger.warning(f"Cache copy failed: {e2}")

            # 3. FIX: Use send_cached_media (not reply_cached_media — that method doesn't exist)
            if not sent_msg:
                try:
                    sent_msg = await client.send_cached_media(
                        chat_id=message.chat.id,
                        file_id=file_data['file_id'],
                        caption=file_data.get('caption') or f"📁 {file_data.get('file_name', 'File')}"
                    )
                    add_to_cache(
                        file_data['file_id'], sent_msg.id,
                        message.chat.id, bot_id, file_data.get('caption')
                    )
                except Exception as e3:
                    return await message.reply(f"❌ File unavailable! It may have been deleted.\n`{e3}`")

            # Auto-delete for non-premium users
            if sent_msg:
                is_premium = user_data.get("is_premium", False)
                if not is_premium:
                    asyncio.create_task(_auto_delete(sent_msg, auto_delete_time))
                    await message.reply(
                        f"⏳ **Auto-Delete Notice**\n\n"
                        f"This file will be deleted in `{auto_delete_time // 60}` min(s).\n"
                        f"Please save it! 💾"
                    )
                else:
                    await message.reply("🌟 **Premium User:** Auto-delete disabled for you!")
            return

        elif deep_arg.startswith("b_"):
            batch_id = deep_arg[2:]
            batches = load_db(BATCH_DB)
            batch_data = batches.get(batch_id)

            if not batch_data:
                return await message.reply("❌ Batch not found or expired.")

            files = load_db(FILES_DB)
            total = len(batch_data['files'])
            status = await message.reply(f"📦 Sending batch ({total} files)...")
            sent = 0

            for fid in batch_data['files']:
                f_data = files.get(fid)
                if not f_data:
                    continue
                try:
                    await client.copy_message(
                        chat_id=message.chat.id,
                        from_chat_id=DB_CHANNEL,
                        message_id=f_data['db_msg_id'],
                        caption=f_data.get('caption')
                    )
                    sent += 1
                except Exception:
                    try:
                        await client.send_cached_media(
                            chat_id=message.chat.id,
                            file_id=f_data['file_id'],
                            caption=f_data.get('caption') or f"📁 {f_data.get('file_name', 'File')}"
                        )
                        sent += 1
                    except Exception:
                        pass
                await asyncio.sleep(0.5)

            await status.delete()
            await message.reply(f"✅ Delivered **{sent}/{total}** files!")
            return

        # ── Standard Welcome ─────────────────────────────────────
        global_msg = config.get("global_msg", "")
        welcome = bot_info.get('custom_welcome') if bot_info else None
        welcome_image = bot_info.get('welcome_image') if bot_info else None

        if global_msg:
            await message.reply(f"📢 **System Announcement**\n\n{global_msg}")

        if not welcome:
            greets = ["Hello", "Hey", "Welcome", "Namaste", "Greetings"]
            welcome = (
                f"✨ **{random.choice(greets)}, {message.from_user.first_name}!**\n\n"
                f"Welcome to the most **Advanced & Secure FileStore System**.\n\n"
                f"🛠 **Features:**\n"
                f" ├ 📂 **Cloud Storage** — Unlimited & Permanent\n"
                f" ├ 📦 **Batch Mode** — Multiple files, single link\n"
                f" ├ 🤖 **Bot Cloning** — Create your own copy\n"
                f" ├ 🔐 **Auto-Destruct** — Files delete for privacy\n"
                f" └ ⚡ **Fast Delivery** — Instant file access\n\n"
                f"{'🆕 Welcome to our community!' if is_new else '👋 Good to see you again!'}"
            )

        keyboard = get_start_keyboard(bot_id, user_id)
        if welcome_image:
            try:
                await message.reply_photo(welcome_image, caption=welcome, reply_markup=keyboard)
                return
            except Exception:
                pass
        await message.reply(welcome, reply_markup=keyboard)

    # ── /admin ───────────────────────────────────────────────────
    @app.on_message(filters.command("admin") & filters.private, group=1)
    async def admin_panel_cmd(client, message):
        user_id = message.from_user.id
        bot_info = get_bot_info(client.me.id)
        if not is_admin(user_id) and (not bot_info or bot_info.get('owner_id') != user_id):
            return
        await message.reply("⚡ **Admin Panel**", reply_markup=get_admin_panel_keyboard())

    # ── /supreme ─────────────────────────────────────────────────
    @app.on_message(filters.command("supreme") & filters.private, group=1)
    async def supreme_panel_cmd(client, message):
        if message.from_user.id != MAIN_ADMIN:
            return
        users = load_db(USERS_DB)
        await message.reply(
            f"👑 **Supreme Admin Panel**\n\n"
            f"🤖 Active Bots: `{len(ACTIVE_CLIENTS)}`\n"
            f"👥 Total Users: `{len(users)}`\n"
            f"📁 Total Files: `{len(load_db(FILES_DB))}`",
            reply_markup=get_supreme_panel_keyboard()
        )

    # ── /stats ───────────────────────────────────────────────────
    @app.on_message(filters.command("stats") & filters.private, group=1)
    async def stats_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id

        if user_id == MAIN_ADMIN:
            await message.reply(
                "🌐 **Global Analytics**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 Total Bots: `{len(get_all_bots())}`\n"
                f"🟢 Online Now: `{len(ACTIVE_CLIENTS)}`\n"
                f"👥 Total Users: `{len(load_db(USERS_DB))}`\n"
                f"📁 Total Files: `{len(load_db(FILES_DB))}`\n"
                f"⏳ Uptime: `{str(datetime.now() - START_TIME).split('.')[0]}`"
            )
        else:
            ud = get_user(user_id, bot_id)
            user_bots = [
                b for b in get_all_bots().values()
                if isinstance(b, dict) and b.get('owner_id') == user_id
            ]
            await message.reply(
                "📊 **Your Dashboard**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📤 Files Uploaded: `{ud.get('files_uploaded', 0) if ud else 0}`\n"
                f"📦 Batches: `{ud.get('batches_created', 0) if ud else 0}`\n"
                f"🤖 Bots Cloned: `{len(user_bots)}`\n"
                f"💰 Points: `{ud.get('points', 0) if ud else 0}`\n"
                f"👥 Referrals: `{ud.get('referrals', 0) if ud else 0}`\n"
                f"💎 Premium: `{'Yes' if ud and ud.get('is_premium') else 'No'}`"
            )

    # ── /mybots ──────────────────────────────────────────────────
    @app.on_message(filters.command("mybots") & filters.private, group=1)
    async def my_bots_cmd(client, message):
        user_id = message.from_user.id
        user_bots = [
            b for b in get_all_bots().values()
            if isinstance(b, dict) and b.get('owner_id') == user_id
        ]
        if not user_bots:
            return await message.reply(
                "🤖 **No Bots Yet!**\n\nUse `/clone TOKEN` to create one.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 BotFather", url="https://t.me/BotFather")]
                ])
            )
        text = f"🤖 **Your Bots ({len(user_bots)})**\n\n"
        for i, bot in enumerate(user_bots[:10], 1):
            status = "🟢" if bot['bot_id'] in ACTIVE_CLIENTS else "🔴"
            text += f"{i}. {status} @{bot['bot_username']}\n"
        await message.reply(text)

    # ── /ban /unban /info /setpremium /gban /ungban ──────────────
    @app.on_message(
        filters.command(["ban", "unban", "info", "setpremium", "gban", "ungban"]) & filters.private,
        group=1
    )
    async def admin_utils_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if not (user_id == MAIN_ADMIN or is_admin(user_id) or
                (bot_info and bot_info.get('owner_id') == user_id)):
            return

        if len(message.command) < 2:
            return await message.reply(f"Usage: `/{message.command[0]} USER_ID`")

        try:
            target = int(message.command[1])
        except ValueError:
            return await message.reply("❌ Invalid User ID!")

        cmd = message.command[0]

        if cmd == "ban":
            result = ban_user(target, bot_id)
            await message.reply(f"🚫 User `{target}` banned." if result else "❌ User not found.")
        elif cmd == "unban":
            result = unban_user(target, bot_id)
            await message.reply(f"✅ User `{target}` unbanned." if result else "❌ User not found.")
        elif cmd == "setpremium":
            users = load_db(USERS_DB)
            key = f"{bot_id}_{target}"
            if key in users:
                users[key]["is_premium"] = True
                save_db(USERS_DB, users)
                await message.reply(f"💎 User `{target}` is now Premium!")
            else:
                await message.reply("❌ User not found.")
        elif cmd == "gban":
            if user_id != MAIN_ADMIN:
                return
            config = get_global_config()
            gbans = config.get("global_bans", [])
            if target not in gbans:
                gbans.append(target)
                update_global_config("global_bans", gbans)
                await message.reply(f"🌍 Globally banned `{target}`!")
            else:
                await message.reply("Already globally banned.")
        elif cmd == "ungban":
            if user_id != MAIN_ADMIN:
                return
            config = get_global_config()
            gbans = config.get("global_bans", [])
            if target in gbans:
                gbans.remove(target)
                update_global_config("global_bans", gbans)
                await message.reply(f"✅ Globally unbanned `{target}`!")
            else:
                await message.reply("Not in global ban list.")
        elif cmd == "info":
            user = get_user(target, bot_id)
            if not user:
                return await message.reply("❌ User not found in database.")
            await message.reply(
                f"👤 **User Info**\n\n"
                f"🆔 ID: `{user['user_id']}`\n"
                f"🏷 Name: {user.get('name', 'Unknown')}\n"
                f"🔗 Username: @{user.get('username') or 'None'}\n"
                f"📅 Joined: {user.get('join_date', 'N/A')}\n"
                f"🚫 Banned: {'Yes' if user.get('is_banned') else 'No'}\n"
                f"💎 Premium: {'Yes' if user.get('is_premium') else 'No'}\n\n"
                f"📊 **Stats:**\n"
                f"📤 Uploaded: `{user.get('files_uploaded', 0)}`\n"
                f"📦 Batches: `{user.get('batches_created', 0)}`\n"
                f"🤖 Clones: `{user.get('bots_cloned', 0)}`\n"
                f"💰 Points: `{user.get('points', 0)}`\n"
                f"👥 Referrals: `{user.get('referrals', 0)}`"
            )

    # ── /addpoints ───────────────────────────────────────────────
    @app.on_message(filters.command("addpoints") & filters.private, group=1)
    async def addpoints_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        if not (user_id == MAIN_ADMIN or is_admin(user_id) or
                (bot_info and bot_info.get('owner_id') == user_id)):
            return
        if len(message.command) < 3:
            return await message.reply("Usage: `/addpoints USER_ID AMOUNT`")
        try:
            target = int(message.command[1])
            amount = int(message.command[2])
        except ValueError:
            return await message.reply("❌ Invalid values!")
        update_user_stats(target, bot_id, "points", amount)
        await message.reply(f"✅ Added `{amount}` points to `{target}`!")

    # ── /delfile ─────────────────────────────────────────────────
    @app.on_message(filters.command("delfile") & filters.private, group=1)
    async def del_file_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if len(message.command) < 2:
            return await message.reply("Usage: `/delfile FILE_ID`\n\nUse `/listfiles` to find file IDs.")

        unique_id = message.command[1]
        files = load_db(FILES_DB)

        if unique_id not in files:
            return await message.reply("❌ File not found!")

        file_data = files[unique_id]
        is_owner_of_file = file_data.get('user_id') == user_id
        can_delete = (user_id == MAIN_ADMIN or is_admin(user_id) or
                      (bot_info and bot_info.get('owner_id') == user_id) or
                      is_owner_of_file)

        if not can_delete:
            return await message.reply("❌ You can only delete your own files!")

        del files[unique_id]
        save_db(FILES_DB, files)
        await message.reply(
            f"🗑 **File Deleted**\n\n"
            f"📁 `{file_data.get('file_name', 'Unknown')}`\n"
            f"🆔 ID: `{unique_id}`"
        )

    # ── /listfiles ───────────────────────────────────────────────
    @app.on_message(filters.command("listfiles") & filters.private, group=1)
    async def list_files_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        files = load_db(FILES_DB)

        # Admin sees all, users see their own
        bot_info = get_bot_info(bot_id)
        is_admin_or_owner = (user_id == MAIN_ADMIN or is_admin(user_id) or
                             (bot_info and bot_info.get('owner_id') == user_id))

        if is_admin_or_owner:
            user_files = [(uid, f) for uid, f in files.items() if f.get('bot_id') == bot_id]
        else:
            user_files = [(uid, f) for uid, f in files.items()
                         if f.get('bot_id') == bot_id and f.get('user_id') == user_id]

        if not user_files:
            return await message.reply("📭 No files found!")

        # Show last 10 files
        recent = sorted(user_files, key=lambda x: x[1].get('upload_date', ''), reverse=True)[:10]
        text = f"📋 **{'All Files' if is_admin_or_owner else 'Your Files'}** ({len(user_files)} total)\n\n"
        buttons = []
        for uid, f in recent:
            icon = get_file_type_icon(f.get('file_name', ''))
            name = (f.get('file_name', 'Unknown'))[:30]
            link = f"https://t.me/{client.me.username}?start=f_{uid}"
            text += f"{icon} `{uid}` — {name}\n"
            text += f"   📊 {format_size(f.get('file_size', 0))} | 👁 {f.get('access_count', 0)} views\n\n"
            buttons.append([InlineKeyboardButton(f"{icon} {name[:25]}...", url=link)])

        await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)

    # ── /setmsg ──────────────────────────────────────────────────
    @app.on_message(filters.command("setmsg") & filters.private, group=1)
    async def set_msg_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        if not bot_info or (bot_info.get('owner_id') != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Only bot owner can do this!")
        if not message.reply_to_message or not message.reply_to_message.text:
            return await message.reply("💬 Reply to a message with `/setmsg` to set it as welcome.")
        update_bot_info(bot_id, 'custom_welcome', message.reply_to_message.text)
        await message.reply("✅ Welcome message updated!")

    # ── /settimer ────────────────────────────────────────────────
    @app.on_message(filters.command("settimer") & filters.private, group=1)
    async def set_timer_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        if not bot_info or (bot_info.get('owner_id') != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")
        if len(message.command) < 2:
            curr = bot_info.get('auto_delete_time', 600)
            return await message.reply(
                f"⏱ Current timer: `{curr}s` ({curr//60} min)\n\n"
                f"Usage: `/settimer SECONDS`"
            )
        try:
            secs = int(message.command[1])
            if secs < 60:
                return await message.reply("❌ Minimum 60 seconds!")
            update_bot_info(bot_id, 'auto_delete_time', secs)
            await message.reply(f"✅ Auto-delete set to `{secs}s` ({secs//60} min).")
        except ValueError:
            await message.reply("❌ Please enter a valid number of seconds!")

    # ── /shortener ───────────────────────────────────────────────
    @app.on_message(filters.command("shortener") & filters.private, group=1)
    async def set_shortener_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        if not bot_info or (bot_info.get('owner_id') != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")

        if len(message.command) < 2:
            status = "✅ Enabled" if bot_info.get("is_shortener_enabled") else "❌ Disabled"
            return await message.reply(
                f"🔗 **URL Shortener Settings**\n\n"
                f"Status: {status}\n"
                f"URL: `{bot_info.get('shortener_url') or 'Not set'}`\n"
                f"API: `{bot_info.get('shortener_api') or 'Not set'}`\n\n"
                f"**Commands:**\n"
                f"• `/shortener on` — Enable\n"
                f"• `/shortener off` — Disable\n"
                f"• `/shortener set URL API` — Configure\n"
                f"Example: `/shortener set shareus.io APIKEY123`"
            )

        cmd = message.command[1].lower()
        if cmd == "on":
            if not bot_info.get("shortener_url") or not bot_info.get("shortener_api"):
                return await message.reply("❌ Set URL and API first: `/shortener set URL API`")
            update_bot_info(bot_id, "is_shortener_enabled", True)
            await message.reply("✅ URL Shortener enabled!")
        elif cmd == "off":
            update_bot_info(bot_id, "is_shortener_enabled", False)
            await message.reply("✅ URL Shortener disabled!")
        elif cmd == "set":
            if len(message.command) < 4:
                return await message.reply("❌ Usage: `/shortener set URL APIKEY`")
            update_bot_info(bot_id, "shortener_url", message.command[2])
            update_bot_info(bot_id, "shortener_api", message.command[3])
            await message.reply(f"✅ Shortener configured: `{message.command[2]}`")
        else:
            await message.reply("❌ Unknown command. Use: `on`, `off`, or `set`")

    # ── /setlog ──────────────────────────────────────────────────
    @app.on_message(filters.command("setlog") & filters.private, group=1)
    async def set_log_channel_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        if not bot_info or (bot_info.get('owner_id') != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")

        if len(message.command) < 2:
            curr = bot_info.get('log_channel') or 'Not Set'
            return await message.reply(
                f"📝 **Log Channel**\n\nCurrent: `{curr}`\n\n"
                f"Usage: `/setlog CHANNEL_ID` or `/setlog off`"
            )

        if message.command[1].lower() == "off":
            update_bot_info(bot_id, 'log_channel', None)
            return await message.reply("✅ Log channel disabled!")

        try:
            channel_id = int(message.command[1])
            # Verify bot is member
            try:
                await client.get_chat(channel_id)
            except Exception:
                return await message.reply("❌ Cannot access that channel! Make sure I'm a member.")
            update_bot_info(bot_id, 'log_channel', channel_id)
            await message.reply(f"✅ Log channel set to `{channel_id}`.")
        except ValueError:
            await message.reply("❌ Invalid Channel ID!")

    # ── /setwelcomeimg ───────────────────────────────────────────
    @app.on_message(filters.command("setwelcomeimg") & filters.private, group=1)
    async def set_welcome_img_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        if not bot_info or (bot_info.get('owner_id') != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("🖼 Reply to a **photo** with `/setwelcomeimg`!")
        update_bot_info(bot_id, 'welcome_image', message.reply_to_message.photo.file_id)
        await message.reply("✅ Welcome image updated!")

    # ── /help ────────────────────────────────────────────────────
    @app.on_message(filters.command("help") & filters.private, group=1)
    async def help_cmd(client, message):
        await message.reply(
            "🚀 **FileStore Bot — Help Guide**\n\n"
            "**📂 File Sharing:**\n"
            " └ Send any file → Get a secure shareable link.\n\n"
            "**📦 Batch Mode:**\n"
            " 1. `/batch` — Start batch\n"
            " 2. Send multiple files\n"
            " 3. `/done` — Generate master link\n"
            " 4. `/cancel` — Cancel anytime\n\n"
            "**🤖 Bot Cloning:**\n"
            " 1. Create bot at @BotFather → /newbot\n"
            " 2. Copy the API Token\n"
            " 3. `/clone YOUR_TOKEN` here\n\n"
            "**⚙️ Admin Commands:**\n"
            " • `/setfs add -100xxx` — Force subscribe\n"
            " • `/settimer 600` — Auto-delete timer\n"
            " • `/setwelcomeimg` — Welcome photo\n"
            " • `/setmsg` — Welcome text\n"
            " • `/ban` `/unban` `/info` — User management\n\n"
            "**🆕 New Commands:**\n"
            " • `/ping` — Check latency\n"
            " • `/delfile ID` — Delete a file\n"
            " • `/listfiles` — View your files\n"
            " • `/addpoints ID AMOUNT` — Add points\n\n"
            "**📊 Stats:** `/stats` — View usage analytics"
        )

    # ── /setglobal ───────────────────────────────────────────────
    @app.on_message(filters.command("setglobal") & filters.private, group=1)
    async def set_global_msg(client, message):
        if message.from_user.id != MAIN_ADMIN:
            return
        if len(message.command) < 2:
            return await message.reply("Usage: `/setglobal YOUR_MESSAGE`\nUse `/setglobal off` to clear.")
        txt = message.text.split(None, 1)[1]
        if txt.lower() == "off":
            update_global_config("global_msg", "")
            return await message.reply("✅ Global message cleared!")
        update_global_config("global_msg", txt)
        await message.reply("✅ Global message set!")

    # ── /addadmin /deladmin ──────────────────────────────────────
    @app.on_message(filters.command(["addadmin", "deladmin"]) & filters.private, group=1)
    async def manage_admin_handler(client, message):
        if message.from_user.id != MAIN_ADMIN:
            return
        if len(message.command) < 2:
            return await message.reply(f"Usage: `/{message.command[0]} USER_ID`")
        target = message.command[1]
        admins = load_db(ADMINS_DB)
        if message.command[0] == "addadmin":
            admins[target] = str(datetime.now())
            save_db(ADMINS_DB, admins)
            await message.reply(f"✅ `{target}` is now a Global Admin.")
        else:
            if target in admins:
                del admins[target]
                save_db(ADMINS_DB, admins)
                await message.reply(f"✅ Admin `{target}` removed.")
            else:
                await message.reply("❌ Not an admin!")

    # ── /refer ───────────────────────────────────────────────────
    @app.on_message(filters.command("refer") & filters.private, group=1)
    async def refer_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        ud = get_user(user_id, bot_id)
        link = f"https://t.me/{client.me.username}?start=ref_{user_id}"
        await message.reply(
            f"🔗 **Referral Program**\n\n"
            f"Invite friends & earn **10 points** per referral!\n"
            f"500 points = **1 Month Premium** 🌟\n\n"
            f"💰 Your Points: `{ud.get('points', 0) if ud else 0}`\n"
            f"👥 Your Referrals: `{ud.get('referrals', 0) if ud else 0}`\n\n"
            f"🚀 **Your Link:**\n`{link}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={link}&text=Join+this+amazing+bot!")]
            ])
        )

    # ── /points ──────────────────────────────────────────────────
    @app.on_message(filters.command("points") & filters.private, group=1)
    async def points_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        ud = get_user(user_id, bot_id)
        pts = ud.get('points', 0) if ud else 0
        await message.reply(
            f"💰 **Your Points: `{pts}`**\n\n"
            f"🌟 Premium costs 500 points.\n"
            f"👥 Earn 10 points per referral.\n"
            f"🛒 Use `/buy_premium` to redeem."
        )

    # ── /premium ─────────────────────────────────────────────────
    @app.on_message(filters.command("premium") & filters.private, group=1)
    async def premium_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        ud = get_user(user_id, bot_id)
        is_premium = ud.get("is_premium", False) if ud else False
        # FIX: get main bot username properly (not ACTIVE_CLIENTS[MAIN_ADMIN])
        main_uname = get_main_bot_username()
        await message.reply(
            f"🌟 **Premium Membership**\n\n"
            f"Status: {'✅ Active' if is_premium else '❌ Inactive'}\n\n"
            f"**Benefits:**\n"
            f" ├ 🚀 No Auto-Delete on files\n"
            f" ├ 🎯 Priority file delivery\n"
            f" ├ 📂 Unlimited batch size\n"
            f" └ 🛡 Ad-free experience\n\n"
            f"**Cost:** 500 points or contact @{main_uname}\n\n"
            f"Use `/buy_premium` to redeem with points."
        )

    # ── /buy_premium ─────────────────────────────────────────────
    @app.on_message(filters.command("buy_premium") & filters.private, group=1)
    async def buy_premium_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        # FIX: Use get_user() and null-check properly
        ud = get_user(user_id, bot_id)
        if not ud:
            return await message.reply("❌ Please start the bot first with /start")

        if ud.get("is_premium"):
            return await message.reply("✅ You are already a Premium user!")

        if ud.get("points", 0) < 500:
            needed = 500 - ud.get("points", 0)
            return await message.reply(
                f"❌ Not enough points!\n\n"
                f"💰 You have: `{ud.get('points', 0)}` pts\n"
                f"🎯 Need: `{needed}` more pts\n\n"
                f"Refer friends to earn points! Use `/refer`"
            )

        users = load_db(USERS_DB)
        key = f"{bot_id}_{user_id}"
        users[key]["points"] -= 500
        users[key]["is_premium"] = True
        save_db(USERS_DB, users)
        await message.reply(
            "🎉 **Congratulations! You are now Premium!**\n\n"
            "✅ Auto-delete disabled for your files\n"
            "✅ All premium features unlocked!"
        )

    # ── /botinfo ─────────────────────────────────────────────────
    @app.on_message(filters.command("botinfo") & filters.private, group=1)
    async def bot_info_cmd(client, message):
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        if not bot_info:
            return await message.reply("ℹ️ Bot info not found in DB.")
        children = len(get_child_bots(bot_id))
        fs_count = len(bot_info.get('force_subs', []))
        await message.reply(
            f"ℹ️ **Bot Info**\n\n"
            f"🤖 @{client.me.username}\n"
            f"👤 Owner: {bot_info.get('owner_name', 'Unknown')}\n"
            f"🌳 Cloned Bots: `{children}`\n"
            f"📢 Force Sub: `{fs_count}` channels\n"
            f"⏱ Auto-Delete: `{bot_info.get('auto_delete_time', 600)}s`\n"
            f"🔗 Shortener: `{'ON' if bot_info.get('is_shortener_enabled') else 'OFF'}`\n"
            f"✅ Auto-Approve: `{'ON' if bot_info.get('auto_approve') else 'OFF'}`"
        )

    # ── /clone ───────────────────────────────────────────────────
    @app.on_message(filters.command("clone") & filters.private, group=1)
    async def clone_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id

        if is_user_banned(user_id, bot_id):
            return await message.reply("🚫 You are banned!")

        user_bots = [
            b for b in get_all_bots().values()
            if isinstance(b, dict) and b.get('owner_id') == user_id
        ]

        if len(message.command) < 2:
            return await message.reply(
                f"🤖 **Clone Bot**\n\n"
                f"Your active bots: `{len(user_bots)}`\n\n"
                f"**Steps:**\n"
                f"1. Go to @BotFather → /newbot\n"
                f"2. Get your bot token\n"
                f"3. Send here: `/clone YOUR_TOKEN`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 Open BotFather", url="https://t.me/BotFather")]
                ])
            )

        token = message.command[1]
        msg = await message.reply("🔄 Cloning your bot, please wait...")

        # Check if token already registered
        for b in get_all_bots().values():
            if isinstance(b, dict) and b.get("token") == token:
                return await msg.edit("❌ This token is already registered!")

        try:
            new_app = await start_bot(token, parent_bot_id=bot_id)
            if new_app:
                me = await new_app.get_me()
                save_bot_info(token, me.id, me.username, user_id, message.from_user.first_name, bot_id)
                await msg.edit(
                    f"✅ **Bot Cloned Successfully!**\n\n"
                    f"🤖 @{me.username}\n"
                    f"🆔 `{me.id}`\n\n"
                    f"Add your bot to channels as Admin for Force Subscribe.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🚀 Open Bot", url=f"https://t.me/{me.username}")]
                    ])
                )
            else:
                await msg.edit("❌ Failed! Invalid token or bot start error.")
        except Exception as e:
            await msg.edit(f"❌ Error: `{str(e)}`")

    # ── /setfs ───────────────────────────────────────────────────
    @app.on_message(filters.command("setfs") & filters.private, group=1)
    async def set_fs_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if not bot_info or (bot_info.get('owner_id') != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Only bot owner can manage Force Subscribe!")

        force_subs = bot_info.get("force_subs", [])

        if len(message.command) < 2:
            text = f"⚙️ **Force Subscribe** (Max {MAX_FORCE_SUB_CHANNELS} channels)\n\n"
            if not force_subs:
                text += "No channels configured.\n"
            else:
                for i, fs in enumerate(force_subs, 1):
                    cid = fs['channel_id'] if isinstance(fs, dict) else fs
                    link = fs.get('invite_link', 'Auto') if isinstance(fs, dict) else 'Auto'
                    text += f"{i}. `{cid}` — {link}\n"
            text += (
                f"\n**Commands:**\n"
                f"• `/setfs add -100xxx` — Add channel\n"
                f"• `/setfs add -100xxx LINK` — Add with custom link\n"
                f"• `/setfs del -100xxx` — Remove channel\n"
                f"• `/setfs clear` — Clear all\n\n"
                f"⚠️ Bot must be Admin in channels!"
            )
            return await message.reply(text)

        cmd = message.command[1].lower()

        if cmd in ("clear", "off"):
            update_bot_info(bot_id, 'force_subs', [])
            count = cascade_force_subs(bot_id, [])
            return await message.reply(f"✅ All Force Sub channels cleared! ({count} child bots updated)")

        if cmd == "add":
            if len(force_subs) >= MAX_FORCE_SUB_CHANNELS:
                return await message.reply(f"❌ Maximum {MAX_FORCE_SUB_CHANNELS} channels allowed!")
            if len(message.command) < 3:
                return await message.reply("Usage: `/setfs add -100CHANNEL_ID [invite_link]`")
            try:
                channel_id = int(message.command[2])
            except ValueError:
                return await message.reply("❌ Invalid Channel ID!")

            invite_link = message.command[3] if len(message.command) > 3 else None

            try:
                await client.get_chat_member(channel_id, client.me.id)
            except Exception:
                return await message.reply("❌ I'm not a member/admin of that channel!")

            force_subs.append({"channel_id": channel_id, "invite_link": invite_link})
            update_bot_info(bot_id, 'force_subs', force_subs)
            count = cascade_force_subs(bot_id, force_subs)
            return await message.reply(
                f"✅ Channel `{channel_id}` added!\n({count} child bots updated)"
            )

        if cmd == "del":
            if len(message.command) < 3:
                return await message.reply("Usage: `/setfs del -100CHANNEL_ID`")
            try:
                channel_id = int(message.command[2])
            except ValueError:
                return await message.reply("❌ Invalid Channel ID!")
            new_fs = [fs for fs in force_subs
                      if (fs['channel_id'] if isinstance(fs, dict) else fs) != channel_id]
            if len(new_fs) == len(force_subs):
                return await message.reply("❌ Channel not in Force Sub list!")
            update_bot_info(bot_id, 'force_subs', new_fs)
            count = cascade_force_subs(bot_id, new_fs)
            return await message.reply(
                f"✅ Channel `{channel_id}` removed! ({count} child bots updated)"
            )

        await message.reply("❌ Unknown command. Use: `add`, `del`, `clear`")

    # ── /broadcast ───────────────────────────────────────────────
    @app.on_message(filters.command("broadcast") & filters.private, group=1)
    async def broadcast_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        can_broadcast = False
        target_bot_ids = []

        if user_id == MAIN_ADMIN:
            can_broadcast = True
            target_bot_ids = list(ACTIVE_CLIENTS.keys())
        elif bot_info and bot_info.get('owner_id') == user_id:
            can_broadcast = True
            target_bot_ids = [bot_id]
            for desc in get_all_descendant_bots(bot_id):
                if desc['bot_id'] in ACTIVE_CLIENTS:
                    target_bot_ids.append(desc['bot_id'])

        if not can_broadcast:
            return await message.reply("❌ No broadcast permission!")

        if not message.reply_to_message:
            total = sum(len(get_all_users(bid)) for bid in target_bot_ids)
            return await message.reply(
                f"📢 **Broadcast**\n\n"
                f"🤖 Target Bots: `{len(target_bot_ids)}`\n"
                f"👥 Target Users: `{total}`\n\n"
                f"Reply to any message/media with `/broadcast` to send."
            )

        TEMP_BROADCAST_DATA[user_id] = {
            "message": message.reply_to_message,
            "bot_ids": target_bot_ids
        }
        await message.reply(
            f"⚠️ **Confirm Broadcast?**\n\n"
            f"🤖 Bots: `{len(target_bot_ids)}`\n"
            f"This will message ALL users.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Send", callback_data="confirm_broadcast"),
                 InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
            ])
        )

    # ── /batch /done /cancel ─────────────────────────────────────
    @app.on_message(filters.command("batch") & filters.private, group=1)
    async def batch_start(client, message):
        user_id = message.from_user.id
        if is_user_banned(user_id, client.me.id):
            return await message.reply("🚫 Banned!")
        TEMP_BATCH_DATA[user_id] = []
        await message.reply(
            "📦 **Batch Mode Active!**\n\n"
            "Send files one by one.\n"
            "When done, type `/done` to generate the batch link.\n"
            "Type `/cancel` to abort."
        )

    @app.on_message(filters.command("done") & filters.private, group=1)
    async def batch_done(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if user_id not in TEMP_BATCH_DATA or not TEMP_BATCH_DATA[user_id]:
            return await message.reply("❌ No files in batch! Start with `/batch`.")

        file_ids = TEMP_BATCH_DATA.pop(user_id)
        batch_id = get_unique_id()

        batches = load_db(BATCH_DB)
        batches[batch_id] = {
            "files": file_ids, "created_by": user_id,
            "bot_id": bot_id, "date": str(datetime.now())
        }
        save_db(BATCH_DB, batches)
        update_user_stats(user_id, bot_id, "batches_created")

        link = f"https://t.me/{client.me.username}?start=b_{batch_id}"
        short_link = await get_short_link(bot_info, link)

        await message.reply(
            f"✅ **Batch Created!**\n\n"
            f"📦 Files: `{len(file_ids)}`\n"
            f"🆔 ID: `{batch_id}`\n\n"
            f"🔗 **Link:**\n`{short_link}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Batch", url=f"https://t.me/share/url?url={short_link}")]
            ])
        )

    @app.on_message(filters.command("cancel") & filters.private, group=1)
    async def batch_cancel(client, message):
        user_id = message.from_user.id
        if user_id in TEMP_BATCH_DATA:
            del TEMP_BATCH_DATA[user_id]
            await message.reply("❌ Batch cancelled!")
        else:
            await message.reply("Nothing to cancel.")

    # ── INLINE SEARCH ────────────────────────────────────────────
    @app.on_inline_query()
    async def inline_search_handler(client, query):
        bot_id = client.me.id
        q = query.query.strip().lower()
        if not q:
            return await query.answer([], cache_time=1)

        files = load_db(FILES_DB)
        results = []

        for uid, f in files.items():
            if f.get('bot_id') == bot_id and q in f.get('file_name', '').lower():
                icon = get_file_type_icon(f.get('file_name', ''))
                link = f"https://t.me/{client.me.username}?start=f_{uid}"
                results.append(
                    InlineQueryResultArticle(
                        title=f"{icon} {f.get('file_name', 'Unknown')}",
                        description=f"📊 {format_size(f.get('file_size', 0))} | 👁 {f.get('access_count', 0)} views",
                        input_message_content=InputTextMessageContent(
                            f"{icon} **{f.get('file_name')}**\n"
                            f"📊 Size: `{format_size(f.get('file_size', 0))}`\n"
                            f"🔗 {link}"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🚀 Get File", url=link)]
                        ])
                    )
                )
            if len(results) >= 20:
                break

        await query.answer(results, cache_time=1)

    # ── /search ──────────────────────────────────────────────────
    @app.on_message(filters.command("search") & filters.private, group=1)
    async def search_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id

        if is_user_banned(user_id, bot_id):
            return await message.reply("🚫 Banned!")

        if len(message.command) < 2:
            return await message.reply("🔍 Usage: `/search FILENAME`\n\nYou can also use inline search: `@BotUsername query`")

        query = message.text.split(None, 1)[1].lower()
        files = load_db(FILES_DB)

        results = [
            (uid, f) for uid, f in files.items()
            if f.get('bot_id') == bot_id and query in f.get('file_name', '').lower()
        ][:10]

        if not results:
            return await message.reply(f"❌ No files found for: `{query}`")

        text = f"🔍 **Results for** `{query}` ({len(results)} found)\n\n"
        buttons = []
        for uid, f in results:
            icon = get_file_type_icon(f.get('file_name', ''))
            name = f.get('file_name', 'Unknown')
            link = f"https://t.me/{client.me.username}?start=f_{uid}"
            text += f"{icon} `{name[:40]}`\n   📊 {format_size(f.get('file_size', 0))}\n\n"
            buttons.append([InlineKeyboardButton(f"{icon} {name[:30]}", url=link)])

        await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))

    # ── FILE HANDLER ─────────────────────────────────────────────
    @app.on_message(
        (filters.document | filters.video | filters.audio | filters.photo) & filters.private,
        group=1
    )
    async def file_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id

        if is_user_banned(user_id, bot_id):
            return await message.reply("🚫 Banned!")

        # Forward to DB Channel for centralized storage
        try:
            db_msg = await message.forward(DB_CHANNEL)
        except Exception as e:
            logger.error(f"DB Channel forward failed: {e}")
            return await message.reply(
                "❌ **DB Channel Error!**\n\n"
                "Cannot save file. Contact admin to verify DB Channel configuration."
            )

        original_caption = message.caption  # Preserve original caption

        # Extract file details from forwarded message
        if db_msg.photo:
            file_id = db_msg.photo.file_id
            file_name = f"photo_{db_msg.photo.file_unique_id}.jpg"
            file_size = db_msg.photo.file_size or 0
        elif db_msg.video:
            file_id = db_msg.video.file_id
            file_name = db_msg.video.file_name or f"video_{db_msg.video.file_unique_id}.mp4"
            file_size = db_msg.video.file_size or 0
        elif db_msg.audio:
            file_id = db_msg.audio.file_id
            file_name = db_msg.audio.file_name or f"audio_{db_msg.audio.file_unique_id}.mp3"
            file_size = db_msg.audio.file_size or 0
        elif db_msg.document:
            file_id = db_msg.document.file_id
            file_name = db_msg.document.file_name or f"file_{db_msg.document.file_unique_id}"
            file_size = db_msg.document.file_size or 0
        else:
            return  # Unknown type

        unique_id = get_unique_id()
        files = load_db(FILES_DB)
        files[unique_id] = {
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "caption": original_caption,
            "user_id": user_id,
            "bot_id": bot_id,
            "upload_date": str(datetime.now()),
            "db_msg_id": db_msg.id,
            "access_count": 0
        }
        save_db(FILES_DB, files)

        add_to_cache(file_id, db_msg.id, DB_CHANNEL, bot_id, original_caption)
        update_user_stats(user_id, bot_id, "files_uploaded")

        # Log to log channel
        bot_info = get_bot_info(bot_id)
        if bot_info and bot_info.get("log_channel"):
            try:
                icon = get_file_type_icon(file_name)
                await client.copy_message(
                    bot_info["log_channel"], message.chat.id, message.id,
                    caption=(
                        f"📤 **New File Uploaded**\n\n"
                        f"{icon} `{file_name}`\n"
                        f"📊 {format_size(file_size)}\n"
                        f"👤 User: `{user_id}`\n"
                        f"🆔 File ID: `{unique_id}`"
                    )
                )
            except Exception as e:
                logger.warning(f"Log channel failed: {e}")

        # Batch mode check
        if user_id in TEMP_BATCH_DATA:
            TEMP_BATCH_DATA[user_id].append(unique_id)
            icon = get_file_type_icon(file_name)
            await message.reply(
                f"✅ **Added to Batch!**\n\n"
                f"{icon} `{file_name}`\n"
                f"📦 Total in batch: `{len(TEMP_BATCH_DATA[user_id])}`",
                quote=True
            )
        else:
            link = f"https://t.me/{client.me.username}?start=f_{unique_id}"
            short_link = await get_short_link(bot_info, link)
            icon = get_file_type_icon(file_name)

            await message.reply(
                f"✅ **File Saved!**\n\n"
                f"{icon} `{file_name}`\n"
                f"📊 {format_size(file_size)}\n"
                f"🆔 ID: `{unique_id}`\n\n"
                f"🔗 **Your Link:**\n`{short_link}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={short_link}")]
                ])
            )

    # ── CALLBACK QUERY HANDLER ───────────────────────────────────
    @app.on_callback_query(group=1)
    async def callback_handler(client, callback):
        user_id = callback.from_user.id
        data = callback.data
        bot_id = client.me.id

        if is_user_banned(user_id, bot_id):
            return await callback.answer("🚫 You are banned!", show_alert=True)

        # ── START BATCH ────────────────────────────────────────
        if data == "start_batch":
            TEMP_BATCH_DATA[user_id] = []
            await callback.message.edit(
                "📦 **Batch Mode Active**\n\nSend files now...\nType `/done` when finished.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel Batch", callback_data="cancel_batch")]
                ])
            )
            await callback.answer("Batch mode started!")

        elif data == "cancel_batch":
            TEMP_BATCH_DATA.pop(user_id, None)
            await callback.message.edit("❌ Batch cancelled!")
            await callback.answer()

        elif data == "clone_menu":
            user_bots = [b for b in get_all_bots().values()
                        if isinstance(b, dict) and b.get('owner_id') == user_id]
            await callback.message.edit(
                f"🤖 **Clone Your Bot**\n\n"
                f"Your Bots: `{len(user_bots)}`\n\n"
                f"1. @BotFather → /newbot\n"
                f"2. Copy token\n"
                f"3. Send: `/clone TOKEN`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 Open BotFather", url="https://t.me/BotFather")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "user_dashboard":
            ud = get_user(user_id, bot_id)
            user_bots = [b for b in get_all_bots().values()
                        if isinstance(b, dict) and b.get('owner_id') == user_id]
            await callback.message.edit(
                f"📊 **Your Dashboard**\n\n"
                f"📁 Files Uploaded: `{ud.get('files_uploaded', 0) if ud else 0}`\n"
                f"📦 Batches Created: `{ud.get('batches_created', 0) if ud else 0}`\n"
                f"🤖 Bots Cloned: `{len(user_bots)}`\n"
                f"💰 Points: `{ud.get('points', 0) if ud else 0}`\n"
                f"👥 Referrals: `{ud.get('referrals', 0) if ud else 0}`\n"
                f"💎 Premium: `{'Yes ✅' if ud and ud.get('is_premium') else 'No'}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 My Bots", callback_data="my_bots_menu")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "my_bots_menu":
            user_bots = [b for b in get_all_bots().values()
                        if isinstance(b, dict) and b.get('owner_id') == user_id]
            if not user_bots:
                text = "🤖 **No Bots Yet!**\n\nCreate your first cloned bot!"
                buttons = [[InlineKeyboardButton("➕ Clone Bot", callback_data="clone_menu")]]
            else:
                text = f"🤖 **Your Bots ({len(user_bots)})**\n\n"
                for i, bot in enumerate(user_bots[:10], 1):
                    status = "🟢" if bot['bot_id'] in ACTIVE_CLIENTS else "🔴"
                    text += f"{i}. {status} @{bot['bot_username']}\n"
                buttons = [[InlineKeyboardButton("➕ Clone More", callback_data="clone_menu")]]
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="user_dashboard")])
            await callback.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))
            await callback.answer()

        elif data == "bot_settings":
            bot_info = get_bot_info(bot_id)
            if bot_info:
                fs = len(bot_info.get('force_subs', []))
                timer = bot_info.get('auto_delete_time', 600)
                await callback.message.edit(
                    f"⚙️ **Bot Settings**\n\n"
                    f"🤖 @{client.me.username}\n"
                    f"📢 Force Sub: `{fs}` channels\n"
                    f"⏱ Auto-Delete: `{timer}s` ({timer//60}min)\n"
                    f"💬 Custom Welcome: `{'Yes' if bot_info.get('custom_welcome') else 'No'}`\n"
                    f"🔗 Shortener: `{'ON' if bot_info.get('is_shortener_enabled') else 'OFF'}`",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                    ])
                )
            await callback.answer()

        elif data == "help_menu":
            await callback.message.edit(
                "ℹ️ **Help Guide**\n\n"
                "• Send any file → get shareable link\n"
                "• `/batch` → group multiple files in one link\n"
                "• `/clone TOKEN` → create your own bot\n"
                "• `/refer` → earn points by inviting friends\n"
                "• `/ping` → check bot status\n"
                "• `/listfiles` → browse your files\n"
                "• `/delfile ID` → delete a file",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "referral_menu":
            ud = get_user(user_id, bot_id)
            link = f"https://t.me/{client.me.username}?start=ref_{user_id}"
            await callback.message.edit(
                f"🎁 **Referral Program**\n\n"
                f"Invite friends → earn **10 points** each!\n"
                f"500 points = 1 Month Premium 🌟\n\n"
                f"👥 Your Referrals: `{ud.get('referrals', 0) if ud else 0}`\n"
                f"💰 Your Points: `{ud.get('points', 0) if ud else 0}`\n\n"
                f"🔗 Your Link:\n`{link}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={link}")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "premium_menu":
            ud = get_user(user_id, bot_id)
            status = "💎 Active" if ud and ud.get("is_premium") else "🆓 Free"
            # FIX: Get main bot username from ACTIVE_CLIENTS is_main flag
            main_uname = get_main_bot_username()
            await callback.message.edit(
                f"💎 **Premium Membership**\n\n"
                f"Status: **{status}**\n\n"
                f"**Benefits:**\n"
                f"• 🚀 No auto-delete on files\n"
                f"• 🎯 Priority delivery\n"
                f"• 📂 Unlimited batch size\n"
                f"• 🛡 Ad-free experience\n\n"
                f"**Cost:** 500 points or contact @{main_uname}\n"
                f"Use `/buy_premium` to redeem with points.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "admin_panel":
            bot_info = get_bot_info(bot_id)
            if not (is_admin(user_id) or (bot_info and bot_info.get('owner_id') == user_id)):
                return await callback.answer("❌ No access!", show_alert=True)
            await callback.message.edit("⚡ **Admin Panel**", reply_markup=get_admin_panel_keyboard())
            await callback.answer()

        elif data == "broadcast_menu":
            bot_info = get_bot_info(bot_id)
            if not (is_admin(user_id) or user_id == MAIN_ADMIN or
                    (bot_info and bot_info.get('owner_id') == user_id)):
                return await callback.answer("❌ No access!", show_alert=True)
            count = len(get_all_users(bot_id))
            await callback.message.edit(
                f"📢 **Broadcast**\n\n👥 Users: `{count}`\n\nReply to any message with `/broadcast`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "admin_stats":
            bot_files = [f for f in load_db(FILES_DB).values() if f.get('bot_id') == bot_id]
            total_access = sum(f.get('access_count', 0) for f in bot_files)
            await callback.message.edit(
                f"📊 **Bot Statistics**\n\n"
                f"👥 Users: `{len(get_all_users(bot_id))}`\n"
                f"📁 Files: `{len(bot_files)}`\n"
                f"👁 Total File Views: `{total_access}`\n"
                f"⏳ Uptime: `{str(datetime.now() - START_TIME).split('.')[0]}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "manage_users":
            all_u = load_db(USERS_DB)
            banned = sum(1 for u in all_u.values()
                        if u.get('bot_id') == bot_id and u.get('is_banned'))
            await callback.message.edit(
                f"👥 **User Management**\n\n"
                f"🟢 Active: `{len(get_all_users(bot_id))}`\n"
                f"🚫 Banned: `{banned}`\n\n"
                f"Commands:\n"
                f"• `/ban USER_ID` — Ban user\n"
                f"• `/unban USER_ID` — Unban user\n"
                f"• `/info USER_ID` — User details\n"
                f"• `/setpremium USER_ID` — Give premium",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "my_bots_admin":
            user_bots = [b for b in get_all_bots().values()
                        if isinstance(b, dict) and b.get('owner_id') == user_id]
            text = f"🤖 **Your Bots ({len(user_bots)})**\n\n"
            for i, bot in enumerate(user_bots[:15], 1):
                st = "🟢" if bot['bot_id'] in ACTIVE_CLIENTS else "🔴"
                text += f"{i}. {st} @{bot['bot_username']}\n"
            if not user_bots:
                text += "No bots yet!"
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Clone New", callback_data="clone_menu")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "bot_settings_admin":
            bot_info = get_bot_info(bot_id)
            if not bot_info:
                return await callback.answer("Bot info not found!", show_alert=True)
            timer = bot_info.get('auto_delete_time', 600)
            await callback.message.edit(
                f"⚙️ **Bot Settings**\n\n"
                f"🤖 @{bot_info['bot_username']}\n"
                f"💬 Custom Welcome: `{'Enabled' if bot_info.get('custom_welcome') else 'Disabled'}`\n"
                f"🖼 Welcome Image: `{'Enabled' if bot_info.get('welcome_image') else 'Disabled'}`\n"
                f"⏱ Auto-Delete: `{timer}s` ({timer//60}min)\n"
                f"✅ Auto-Approve: `{'ON' if bot_info.get('auto_approve') else 'OFF'}`\n"
                f"📝 Log Channel: `{bot_info.get('log_channel') or 'Not Set'}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 Set Welcome", callback_data="set_welcome_msg")],
                    [InlineKeyboardButton("⏱ Set Timer", callback_data="set_delete_timer")],
                    [InlineKeyboardButton("📝 Set Log Channel", callback_data="set_log_info")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "set_welcome_msg":
            await callback.message.edit(
                "💬 **Set Custom Welcome**\n\nReply to any message with `/setmsg`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="bot_settings_admin")]
                ])
            )
            await callback.answer()

        elif data == "set_log_info":
            await callback.message.edit(
                "📝 **Set Log Channel**\n\nUse: `/setlog CHANNEL_ID`\nDisable: `/setlog off`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="bot_settings_admin")]
                ])
            )
            await callback.answer()

        elif data == "set_delete_timer":
            bot_info = get_bot_info(bot_id)
            curr = bot_info.get('auto_delete_time', 600) if bot_info else 600
            await callback.message.edit(
                f"⏱ **Auto-Delete Timer**\n\n"
                f"Current: `{curr}s` ({curr//60} min)\n\n"
                f"Use: `/settimer SECONDS`\n"
                f"Example: `/settimer 300` = 5 minutes",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="bot_settings_admin")]
                ])
            )
            await callback.answer()

        # FIX: forcesub_admin — single block, properly sends message
        elif data == "forcesub_admin":
            bot_info = get_bot_info(bot_id)
            if not bot_info:
                return await callback.answer("Bot info not found!", show_alert=True)
            force_subs = bot_info.get("force_subs", [])
            text = f"🔒 **Force Subscribe ({len(force_subs)}/{MAX_FORCE_SUB_CHANNELS} channels)**\n\n"
            if not force_subs:
                text += "No channels configured.\n"
            else:
                for i, fs in enumerate(force_subs, 1):
                    cid = fs['channel_id'] if isinstance(fs, dict) else fs
                    lnk = (fs.get('invite_link') if isinstance(fs, dict) else None) or 'Auto'
                    text += f"{i}. `{cid}` — {lnk}\n"
            text += "\nManage via `/setfs` command."
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "toggle_auto_approve":
            bot_info = get_bot_info(bot_id)
            if not bot_info:
                return await callback.answer("Bot info not found!", show_alert=True)
            curr = bot_info.get("auto_approve", False)
            update_bot_info(bot_id, "auto_approve", not curr)
            await callback.answer(
                f"Auto-Approve: {'ENABLED ✅' if not curr else 'DISABLED ❌'}",
                show_alert=True
            )
            await callback.message.edit("⚡ **Admin Panel**", reply_markup=get_admin_panel_keyboard())

        elif data == "edit_timer":
            bot_info = get_bot_info(bot_id)
            curr = bot_info.get('auto_delete_time', 600) if bot_info else 600
            await callback.message.edit(
                f"⏱ **Edit Auto-Delete Timer**\n\n"
                f"Current: `{curr}s` ({curr//60}min)\n\n"
                f"Use: `/settimer SECONDS`\nMin: 60 seconds",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "set_welcome_img":
            await callback.message.edit(
                "🖼 **Set Welcome Image**\n\nReply to any photo with `/setwelcomeimg`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "shortener_admin":
            bot_info = get_bot_info(bot_id)
            if not bot_info:
                return await callback.answer("Bot info not found!", show_alert=True)
            status = "✅ Enabled" if bot_info.get("is_shortener_enabled") else "❌ Disabled"
            await callback.message.edit(
                f"🔗 **URL Shortener**\n\n"
                f"Status: {status}\n"
                f"URL: `{bot_info.get('shortener_url') or 'Not set'}`\n\n"
                f"Manage via `/shortener` command.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "supreme_panel":
            if user_id != MAIN_ADMIN:
                return await callback.answer("❌ Supreme access only!", show_alert=True)
            await callback.message.edit("👑 **Supreme Panel**", reply_markup=get_supreme_panel_keyboard())
            await callback.answer()

        elif data == "global_broadcast":
            if user_id != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            total = len(get_all_users())
            await callback.message.edit(
                f"🌍 **Global Broadcast**\n\n"
                f"👥 Total Users: `{total}`\n"
                f"🤖 Active Bots: `{len(ACTIVE_CLIENTS)}`\n\n"
                f"Reply to any message with `/broadcast`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]
                ])
            )
            await callback.answer()

        elif data == "system_stats":
            if user_id != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            total, used, free = shutil.disk_usage("/")
            uptime = str(datetime.now() - START_TIME).split('.')[0]
            await callback.message.edit(
                f"🖥 **System Status**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 Total Bots: `{len(get_all_bots())}`\n"
                f"🟢 Online: `{len(ACTIVE_CLIENTS)}`\n"
                f"👥 Users: `{len(load_db(USERS_DB))}`\n"
                f"📁 Files: `{len(load_db(FILES_DB))}`\n"
                f"💾 Disk: `{used//(2**30)}GB / {total//(2**30)}GB`\n"
                f"🆓 Free: `{free//(2**30)}GB`\n"
                f"⏳ Uptime: `{uptime}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ All Systems Operational",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="system_stats")],
                    [InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]
                ])
            )
            await callback.answer()

        elif data == "all_bots_list":
            if user_id != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            all_bots = get_all_bots()
            text = f"🤖 **All Bots ({len(all_bots)})**\n\n"
            for i, (bk, b) in enumerate(list(all_bots.items())[:20], 1):
                if isinstance(b, dict):
                    st = "🟢" if int(bk) in ACTIVE_CLIENTS else "🔴"
                    text += f"{i}. {st} @{b['bot_username']} — {b.get('owner_name', 'Unknown')}\n"
            if len(all_bots) > 20:
                text += f"\n...and {len(all_bots) - 20} more"
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]
                ])
            )
            await callback.answer()

        elif data == "manage_admins":
            if user_id != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            admins = load_db(ADMINS_DB)
            text = (
                f"👑 **Admin Management**\n\n"
                f"🌟 Main Owner: `{MAIN_ADMIN}`\n\n"
                f"👥 Secondary Admins ({len(admins)}):\n"
            )
            for aid in admins.keys():
                text += f"  • `{aid}`\n"
            text += "\n`/addadmin ID` — Add\n`/deladmin ID` — Remove"
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]
                ])
            )
            await callback.answer()

        elif data == "toggle_maintenance":
            if user_id != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            config = get_global_config()
            curr = config.get("maintenance", False)
            update_global_config("maintenance", not curr)
            await callback.answer(
                f"🛠 Maintenance: {'ON ⚠️' if not curr else 'OFF ✅'}",
                show_alert=True
            )
            # Refresh panel to update button label
            await callback.message.edit("👑 **Supreme Panel**", reply_markup=get_supreme_panel_keyboard())

        elif data == "global_msg_set":
            if user_id != MAIN_ADMIN:
                return await callback.answer()
            await callback.message.edit(
                "📢 **Global Message**\n\n"
                "Set a message shown to ALL users on ALL bots.\n\n"
                "Use: `/setglobal YOUR_MESSAGE`\n"
                "Clear: `/setglobal off`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]
                ])
            )
            await callback.answer()

        elif data == "manual_backup":
            if user_id != MAIN_ADMIN:
                return await callback.answer()
            await callback.answer("⏳ Backup in progress...", show_alert=True)
            await backup_db_to_telegram()
            await callback.answer("✅ Backup sent to DB Channel!", show_alert=True)

        elif data == "manual_clean_cache":
            if user_id != MAIN_ADMIN:
                return await callback.answer()
            count = clean_expired_cache()
            await callback.answer(f"🧹 Cleaned {count} expired cache entries!", show_alert=True)

        elif data == "restart_all_bots":
            if user_id != MAIN_ADMIN:
                return await callback.answer()
            await callback.answer("🔄 Restarting... Please wait.", show_alert=True)
            logger.info(f"Restart triggered by admin {user_id}")
            os.execl(sys.executable, sys.executable, *sys.argv)

        elif data == "confirm_broadcast":
            bdata = TEMP_BROADCAST_DATA.get(user_id)
            if not bdata:
                return await callback.answer("❌ Session expired!", show_alert=True)

            status_msg = await callback.message.edit("📢 **Starting broadcast...**")
            success, failed = await broadcast_message(
                bdata["message"], bdata["bot_ids"], status_msg=status_msg
            )
            TEMP_BROADCAST_DATA.pop(user_id, None)
            await status_msg.edit(
                f"✅ **Broadcast Complete!**\n\n"
                f"✅ Success: `{success}`\n"
                f"❌ Failed: `{failed}`\n"
                f"🤖 Bots: `{len(bdata['bot_ids'])}`"
            )

        elif data == "cancel_broadcast":
            TEMP_BROADCAST_DATA.pop(user_id, None)
            await callback.message.edit("❌ Broadcast cancelled!")
            await callback.answer()

        elif data == "back_to_start":
            bot_info = get_bot_info(bot_id)
            config = get_global_config()
            welcome = (bot_info.get('custom_welcome') if bot_info else None) or (
                f"✨ **Welcome Back!**\n\n"
                f"🤖 @{client.me.username}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✨ Ultra Advanced FileStore Bot"
            )
            welcome_image = bot_info.get('welcome_image') if bot_info else None
            keyboard = get_start_keyboard(bot_id, user_id)

            try:
                if welcome_image:
                    await callback.message.delete()
                    await client.send_photo(
                        callback.message.chat.id, welcome_image,
                        caption=welcome, reply_markup=keyboard
                    )
                else:
                    await callback.message.edit(welcome, reply_markup=keyboard)
            except Exception:
                await callback.message.edit(
                    f"👋 **Welcome Back!**\n\n🤖 @{client.me.username}",
                    reply_markup=keyboard
                )
            await callback.answer()

        else:
            await callback.answer("⚠️ Unknown action.", show_alert=False)


# ═══════════════════════════════════════════════════════════════
# 🔧 HELPER — AUTO DELETE
# ═══════════════════════════════════════════════════════════════

async def _auto_delete(msg, delay: int):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# ⏰ BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════

async def background_tasks():
    while True:
        await asyncio.sleep(600)  # Every 10 minutes
        try:
            # 1. Clean flood data (memory leak prevention)
            USER_FLOOD.clear()

            # 2. Clean expired file cache
            count = clean_expired_cache()
            if count:
                logger.info(f"🗑 Cleaned {count} expired cache entries")

            # 3. Backup databases
            await backup_db_to_telegram()
            logger.info("💾 Database backup completed")

        except Exception as e:
            logger.error(f"Background task error: {e}")


# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║   🚀 ULTRA FILESTORE BOT v2.0 — FIXED & ADVANCED   ║")
    print("╚══════════════════════════════════════════════════════╝")

    if DB_CHANNEL == -1000000000000:
        logger.error("❌ DB_CHANNEL not configured!")
        return

    # Start main bot
    logger.info("🔥 Starting Main Bot...")
    main_app = await start_bot(MAIN_BOT_TOKEN)
    if not main_app:
        logger.error("❌ Main bot failed to start! Check token.")
        return

    # Start all saved clone bots
    all_bots = get_all_bots()
    if all_bots:
        logger.info(f"🔄 Loading {len(all_bots)} saved bot(s)...")
        tasks = [
            start_bot(b["token"], parent_bot_id=b.get("parent_bot_id"))
            for b in all_bots.values()
            if isinstance(b, dict) and b.get("token") and b["token"] != MAIN_BOT_TOKEN
        ]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            ok = sum(1 for r in results if r and not isinstance(r, Exception))
            logger.info(f"✅ {ok}/{len(tasks)} clone bots started")

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║          ✅ ALL SYSTEMS OPERATIONAL ✅               ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"👑 Admin ID   : {MAIN_ADMIN}")
    print(f"🤖 Active Bots: {len(ACTIVE_CLIENTS)}")
    print(f"📅 Started At : {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("⏳ Running... Press Ctrl+C to stop.")

    asyncio.create_task(background_tasks())
    await idle()

    # Graceful shutdown
    logger.info("🛑 Shutting down...")
    global HTTP_SESSION
    if HTTP_SESSION and not HTTP_SESSION.closed:
        await HTTP_SESSION.close()
    for cd in ACTIVE_CLIENTS.values():
        try:
            await cd["app"].stop()
        except Exception:
            pass
    logger.info("✅ Shutdown complete!")


if __name__ == "__main__":
    # FIX: Use asyncio.run() instead of deprecated get_event_loop()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
