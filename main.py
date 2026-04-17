"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 ULTRA ADVANCED FILESTORE BOT v3.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL BUGS FIXED (v2.0)
✅ CAPTION EDITOR — Live edit file captions
✅ THUMBNAIL EDITOR — Custom thumbnails for docs/videos/audio
✅ JOIN REQUEST ACCESS — Pending join = bot access (auto_approve OFF)
✅ CENTRALIZED deliver_file() — All delivery paths use one function
✅ TEMP_EDIT_DATA FSM — Step-by-step edit flow
✅ EDIT MENU in /listfiles — Inline per-file edit panel
✅ PENDING_JOIN_REQUESTS — In-memory + persisted to DB
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
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.enums import ChatMemberStatus

# ═══════════════════════════════════════════════════════════════
# 🔧 CONFIGURATION
# ═══════════════════════════════════════════════════════════════

API_ID = 23790796
API_HASH = "626eb31c9057007df4c2851b3074f27f"
MAIN_BOT_TOKEN = "8607033631:AAEEHymSzeLeP8wpH1TR4vnZSyai3kI1DTE"
MAIN_ADMIN = 8756786934
DB_CHANNEL = -1003982754680

FILE_CACHE_DURATION = 60 * 60   # 60 min
MAX_FORCE_SUB_CHANNELS = 3
PENDING_REQUEST_TTL_DAYS = 30   # pending join request valid for 30 days

# ─── Database paths ─────────────────────────────────────────────
DB_FOLDER        = "database"
FILES_DB         = f"{DB_FOLDER}/files.json"
BATCH_DB         = f"{DB_FOLDER}/batches.json"
BOTS_DB          = f"{DB_FOLDER}/bots.json"
USERS_DB         = f"{DB_FOLDER}/users.json"
ADMINS_DB        = f"{DB_FOLDER}/admins.json"
FILE_CACHE_DB    = f"{DB_FOLDER}/file_cache.json"
CONFIG_DB        = f"{DB_FOLDER}/config.json"
PENDING_REQ_DB   = f"{DB_FOLDER}/pending_requests.json"   # NEW

BOT_COMMANDS = [
    BotCommand("start",         "🚀 Start the bot"),
    BotCommand("admin",         "⚡ Admin Panel"),
    BotCommand("supreme",       "👑 Supreme Panel"),
    BotCommand("clone",         "🤖 Clone your own bot"),
    BotCommand("batch",         "📦 Create batch"),
    BotCommand("done",          "✅ Finish batch"),
    BotCommand("cancel",        "❌ Cancel operation"),
    BotCommand("setfs",         "⚙️ Force subscribe"),
    BotCommand("mybots",        "🤖 Your cloned bots"),
    BotCommand("stats",         "📊 Statistics"),
    BotCommand("help",          "ℹ️ Help & guide"),
    BotCommand("broadcast",     "📢 Broadcast message"),
    BotCommand("ban",           "🚫 Ban user"),
    BotCommand("unban",         "✅ Unban user"),
    BotCommand("setmsg",        "💬 Custom welcome"),
    BotCommand("botinfo",       "ℹ️ Bot information"),
    BotCommand("settimer",      "⏱ Auto-delete timer"),
    BotCommand("setwelcomeimg", "🖼 Set welcome image"),
    BotCommand("search",        "🔍 Search files"),
    BotCommand("points",        "💰 Check points"),
    BotCommand("refer",         "🔗 Referral link"),
    BotCommand("premium",       "🌟 Premium details"),
    BotCommand("shortener",     "🔗 URL Shortener"),
    BotCommand("buy_premium",   "🎁 Buy Premium"),
    BotCommand("setlog",        "📝 Log Channel"),
    BotCommand("restart",       "🔄 Restart (Supreme)"),
    BotCommand("ping",          "🏓 Check latency"),
    BotCommand("listfiles",     "📋 Your files"),
    BotCommand("editfile",      "✏️ Edit file caption/thumb"),
    BotCommand("delfile",       "🗑 Delete a file"),
    BotCommand("addpoints",     "💰 Add points (Admin)"),
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

# ─── PENDING JOIN REQUESTS ──────────────────────────────────────
# Structure: {str(channel_id): {str(user_id): "iso_timestamp"}}
# Persisted in PENDING_REQ_DB. Loaded into memory at startup.

PENDING_JOIN_REQUESTS: dict = {}   # in-memory mirror

def _load_pending_requests():
    global PENDING_JOIN_REQUESTS
    data = load_db(PENDING_REQ_DB)
    # Convert all keys to ints and clean expired entries
    now = datetime.now()
    result = {}
    for cid, users in data.items():
        if not isinstance(users, dict):
            continue
        clean = {}
        for uid, ts in users.items():
            try:
                if (now - datetime.fromisoformat(ts)).days <= PENDING_REQUEST_TTL_DAYS:
                    clean[int(uid)] = ts
            except Exception:
                pass
        if clean:
            result[int(cid)] = clean
    PENDING_JOIN_REQUESTS = result

def _save_pending_requests():
    # Serialise (int keys → str for JSON)
    data = {
        str(cid): {str(uid): ts for uid, ts in users.items()}
        for cid, users in PENDING_JOIN_REQUESTS.items()
    }
    save_db(PENDING_REQ_DB, data)

def mark_join_request(channel_id: int, user_id: int):
    """Called when user sends a join request to a force-sub channel."""
    if channel_id not in PENDING_JOIN_REQUESTS:
        PENDING_JOIN_REQUESTS[channel_id] = {}
    PENDING_JOIN_REQUESTS[channel_id][user_id] = datetime.now().isoformat()
    _save_pending_requests()

def clear_join_request(channel_id: int, user_id: int):
    """Called when user is actually approved."""
    if channel_id in PENDING_JOIN_REQUESTS:
        PENDING_JOIN_REQUESTS[channel_id].pop(user_id, None)
        _save_pending_requests()

def has_pending_request(channel_id: int, user_id: int) -> bool:
    users = PENDING_JOIN_REQUESTS.get(channel_id, {})
    if user_id not in users:
        return False
    try:
        ts = datetime.fromisoformat(users[user_id])
        return (datetime.now() - ts).days <= PENDING_REQUEST_TTL_DAYS
    except Exception:
        return False

# ─── USER FUNCTIONS ─────────────────────────────────────────────

def add_user(user_id, bot_id, username=None, name=None, referred_by=None):
    users = load_db(USERS_DB)
    key = f"{bot_id}_{user_id}"
    is_new = key not in users
    if is_new:
        users[key] = {
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
                users[ref_key]["points"]    = users[ref_key].get("points", 0) + 10
                save_db(USERS_DB, users)
    return users[key], is_new

def get_user(user_id, bot_id):
    return load_db(USERS_DB).get(f"{bot_id}_{user_id}")

def update_user_stats(user_id, bot_id, field, delta=1):
    users = load_db(USERS_DB)
    key = f"{bot_id}_{user_id}"
    if key in users:
        users[key][field] = users[key].get(field, 0) + delta
        save_db(USERS_DB, users)

def is_user_banned(user_id, bot_id):
    if user_id in get_global_config().get("global_bans", []):
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

# ─── BOT INFO ───────────────────────────────────────────────────

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
    return [b for b in load_db(BOTS_DB).values()
            if isinstance(b, dict) and b.get('parent_bot_id') == parent_bot_id]

def get_all_descendant_bots(parent_bot_id):
    result = []
    def recurse(bid):
        for child in get_child_bots(bid):
            result.append(child)
            recurse(child['bot_id'])
    recurse(parent_bot_id)
    return result

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
        if datetime.now() > datetime.fromisoformat(cache[file_id]['expires_at']):
            del cache[file_id]
            save_db(FILE_CACHE_DB, cache)
            return None
        return cache[file_id]
    except Exception:
        return None

def clean_expired_cache():
    cache = load_db(FILE_CACHE_DB)
    expired = [k for k, v in cache.items()
               if datetime.now() > datetime.fromisoformat(v.get('expires_at', '2000-01-01'))]
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
    return {
        'pdf': '📄', 'doc': '📝', 'docx': '📝', 'txt': '📃', 'xlsx': '📊', 'pptx': '📑',
        'mp4': '🎬', 'mkv': '🎬', 'avi': '🎬', 'mov': '🎬', 'webm': '🎬',
        'mp3': '🎵', 'flac': '🎵', 'wav': '🎵', 'aac': '🎵', 'm4a': '🎵',
        'jpg': '🖼', 'jpeg': '🖼', 'png': '🖼', 'gif': '🖼', 'webp': '🖼',
        'zip': '🗜', 'rar': '🗜', '7z': '🗜', 'tar': '🗜', 'gz': '🗜',
        'apk': '📱', 'exe': '💻', 'py': '🐍', 'js': '🌐', 'html': '🌐',
    }.get(ext, '📁')

async def get_short_link(bot_info, link):
    if not (bot_info and bot_info.get("is_shortener_enabled")
            and bot_info.get("shortener_api") and bot_info.get("shortener_url")):
        return link
    url = f"https://{bot_info['shortener_url']}/api?api={bot_info['shortener_api']}&url={link}"
    try:
        session = await get_http_session()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            data = await resp.json()
            if data.get("status") == "success":
                return data.get("shortenedUrl", link)
    except Exception as e:
        logger.warning(f"Shortener failed: {e}")
    return link

def get_main_bot_username():
    for bdata in ACTIVE_CLIENTS.values():
        if bdata.get("is_main"):
            return bdata.get("username", "Admin")
    return "Admin"

async def backup_db_to_telegram():
    main_client = next((d["app"] for d in ACTIVE_CLIENTS.values() if d.get("is_main")), None)
    if not main_client:
        return
    try:
        for file in os.listdir(DB_FOLDER):
            if file.endswith(".json"):
                await main_client.send_document(
                    DB_CHANNEL,
                    document=f"{DB_FOLDER}/{file}",
                    caption=f"📂 **DB Backup** | `{file}` | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
    except Exception as e:
        logger.error(f"Backup failed: {e}")

# ═══════════════════════════════════════════════════════════════
# 📤 CENTRALIZED FILE DELIVERY
# ═══════════════════════════════════════════════════════════════

async def deliver_file(client, chat_id: int, file_data: dict) -> object:
    """
    Single function that handles ALL file delivery paths.
    Priority:
      1. Custom thumbnail → send_document/video/audio with thumb
      2. DB Channel copy_message  (preserves caption from file_data)
      3. In-memory cache copy
      4. send_cached_media fallback
    Returns the sent Message or raises.
    """
    caption       = file_data.get('caption') or ""
    custom_thumb  = file_data.get('custom_thumbnail')
    media_type    = file_data.get('media_type', 'document')
    file_id       = file_data['file_id']

    # ── Path 1: Custom Thumbnail ────────────────────────────────
    if custom_thumb and media_type in ('document', 'video', 'audio'):
        try:
            if media_type == 'document':
                return await client.send_document(
                    chat_id, document=file_id,
                    thumb=custom_thumb, caption=caption
                )
            elif media_type == 'video':
                return await client.send_video(
                    chat_id, video=file_id,
                    thumb=custom_thumb, caption=caption
                )
            elif media_type == 'audio':
                return await client.send_audio(
                    chat_id, audio=file_id,
                    thumb=custom_thumb, caption=caption
                )
        except Exception as e:
            logger.warning(f"Custom thumb delivery failed: {e}")

    # ── Path 2: DB Channel copy ─────────────────────────────────
    try:
        return await client.copy_message(
            chat_id=chat_id,
            from_chat_id=DB_CHANNEL,
            message_id=file_data['db_msg_id'],
            caption=caption or None          # None = keep original
        )
    except Exception as e:
        logger.warning(f"DB copy failed: {e}")

    # ── Path 3: Cache ───────────────────────────────────────────
    cached = get_from_cache(file_id)
    if cached and cached['bot_id'] in ACTIVE_CLIENTS:
        try:
            cached_app = ACTIVE_CLIENTS[cached['bot_id']]['app']
            return await cached_app.copy_message(
                chat_id, cached['chat_id'], cached['message_id'],
                caption=caption or None
            )
        except Exception as e:
            logger.warning(f"Cache delivery failed: {e}")

    # ── Path 4: send_cached_media ───────────────────────────────
    return await client.send_cached_media(
        chat_id=chat_id,
        file_id=file_id,
        caption=caption or f"📁 {file_data.get('file_name', 'File')}"
    )

# ═══════════════════════════════════════════════════════════════
# 🤖 BOT MANAGEMENT
# ═══════════════════════════════════════════════════════════════

START_TIME  = datetime.now()
ACTIVE_CLIENTS: dict = {}
TEMP_BATCH_DATA: dict = {}
TEMP_BROADCAST_DATA: dict = {}
TEMP_EDIT_DATA: dict = {}   # {user_id: {"mode": "caption"|"thumbnail", "uid": file_unique_id}}
USER_FLOOD: dict = {}
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

async def check_force_sub(client, user_id: int):
    """
    Returns (True, []) if user passes force-sub check.
    Returns (False, links) if user must join channels.

    NEW: If auto_approve is OFF, users who sent a join request
    (even pending approval) are treated as subscribed.
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
            if member.status in (ChatMemberStatus.BANNED, ChatMemberStatus.LEFT):
                must_join.append(fs)
            # OWNER / ADMINISTRATOR / MEMBER → OK
        except UserNotParticipant:
            # ── NEW: Check pending join request ─────────────────
            if has_pending_request(channel_id, user_id):
                logger.info(f"User {user_id} has pending request in {channel_id} — granting access")
                continue   # Treat as subscribed
            must_join.append(fs)
        except Exception:
            continue   # Can't verify → skip

    if not must_join:
        return True, []

    links = []
    for fs in must_join:
        channel_id   = fs["channel_id"] if isinstance(fs, dict) else fs
        invite_link  = fs.get("invite_link") if isinstance(fs, dict) else None
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

    return False, links

async def broadcast_message(original_msg, bot_ids=None, status_msg=None):
    if bot_ids is None:
        bot_ids = list(ACTIVE_CLIENTS.keys())
    success = failed = 0
    start = datetime.now()

    for b_idx, bot_id in enumerate(bot_ids, 1):
        if bot_id not in ACTIVE_CLIENTS:
            continue
        uname = ACTIVE_CLIENTS[bot_id]['username']
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
                    elapsed = (datetime.now() - start).seconds
                    total_est = sum(len(get_all_users(bid)) for bid in bot_ids)
                    pct  = int(((success + failed) / max(total_est, 1)) * 100)
                    bar  = "█" * (pct // 10) + "░" * (10 - pct // 10)
                    await status_msg.edit(
                        f"📢 **Broadcast**\n\n"
                        f"`[{bar}]` {pct}%\n"
                        f"🤖 Bot {b_idx}/{len(bot_ids)} @{uname}\n"
                        f"✅ `{success}` ❌ `{failed}` ⏱ `{elapsed}s`"
                    )
                except Exception:
                    pass
            await asyncio.sleep(0.05)

    return success, failed

async def start_bot(token, parent_bot_id=None):
    try:
        app = Client(
            f"bot_{token.split(':')[0]}",
            api_id=API_ID, api_hash=API_HASH,
            bot_token=token, in_memory=True
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
        logger.info(f"✅ {'[MAIN]' if is_main else '[CHILD]'} @{me.username}")
        return app
    except Exception as e:
        logger.error(f"Bot start failed [{token[:10]}...]: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# 🎨 KEYBOARDS
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
        [InlineKeyboardButton("📦 BATCH",      callback_data="start_batch"),
         InlineKeyboardButton("🤖 CLONE",      callback_data="clone_menu")],
        [InlineKeyboardButton("📊 DASHBOARD",  callback_data="user_dashboard"),
         InlineKeyboardButton("🎁 REFERRAL",   callback_data="referral_menu")],
        [InlineKeyboardButton("🎯 MY BOTS",    callback_data="my_bots_menu"),
         InlineKeyboardButton("⚙️ SETTINGS",   callback_data="bot_settings")],
        [InlineKeyboardButton("💎 PREMIUM",    callback_data="premium_menu"),
         InlineKeyboardButton("ℹ️ HELP",        callback_data="help_menu")],
    ])
    return InlineKeyboardMarkup(buttons)

def get_admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 BROADCAST",      callback_data="broadcast_menu"),
         InlineKeyboardButton("📊 STATS",           callback_data="admin_stats")],
        [InlineKeyboardButton("👥 USERS",           callback_data="manage_users"),
         InlineKeyboardButton("🤖 CLONED BOTS",     callback_data="my_bots_admin")],
        [InlineKeyboardButton("⚙️ BOT SETTINGS",    callback_data="bot_settings_admin"),
         InlineKeyboardButton("🔒 FORCE SUB",        callback_data="forcesub_admin")],
        [InlineKeyboardButton("🔗 SHORTENER",       callback_data="shortener_admin"),
         InlineKeyboardButton("⏱ TIMER",            callback_data="edit_timer")],
        [InlineKeyboardButton("🖼 WELCOME IMG",      callback_data="set_welcome_img"),
         InlineKeyboardButton("✅ AUTO APPROVE",     callback_data="toggle_auto_approve")],
        [InlineKeyboardButton("🔙 HOME",             callback_data="back_to_start")],
    ])

def get_supreme_panel_keyboard():
    maint = get_global_config().get("maintenance", False)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 GLOBAL BROADCAST", callback_data="global_broadcast"),
         InlineKeyboardButton("🖥 SYSTEM STATS",     callback_data="system_stats")],
        [InlineKeyboardButton("🤖 ALL BOTS",          callback_data="all_bots_list"),
         InlineKeyboardButton("👑 ADMINS",             callback_data="manage_admins")],
        [InlineKeyboardButton(
            f"🛠 MAINTENANCE: {'ON ⚠️' if maint else 'OFF ✅'}",
            callback_data="toggle_maintenance"),
         InlineKeyboardButton("📢 GLOBAL MSG",        callback_data="global_msg_set")],
        [InlineKeyboardButton("💾 BACKUP DB",          callback_data="manual_backup"),
         InlineKeyboardButton("🧹 CLEAN CACHE",        callback_data="manual_clean_cache")],
        [InlineKeyboardButton("🔄 RESTART SYSTEM",     callback_data="restart_all_bots")],
        [InlineKeyboardButton("🔙 HOME",               callback_data="back_to_start")],
    ])

def get_file_edit_keyboard(uid: str):
    """Inline keyboard shown in /editfile or /listfiles edit panel."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Edit Caption",    callback_data=f"edit_caption_{uid}"),
         InlineKeyboardButton("🖼 Edit Thumbnail",  callback_data=f"edit_thumb_{uid}")],
        [InlineKeyboardButton("🗑 Delete File",      callback_data=f"del_file_{uid}"),
         InlineKeyboardButton("📤 Get File",         callback_data=f"get_file_{uid}")],
        [InlineKeyboardButton("🔙 My Files",         callback_data="my_files_back")],
    ])

# ═══════════════════════════════════════════════════════════════
# 📝 HANDLERS
# ═══════════════════════════════════════════════════════════════

def register_handlers(app: Client):

    # ── FLOOD CONTROL (group 0 → runs before all commands) ──────
    @app.on_message(filters.private, group=0)
    async def flood_control(client, message):
        uid = message.from_user.id
        now = time.time()
        USER_FLOOD[uid] = [t for t in USER_FLOOD.get(uid, []) if now - t < 5]
        USER_FLOOD[uid].append(now)
        if len(USER_FLOOD[uid]) > 5:
            await message.reply("⚠️ **Anti-Flood!** Thoda slow karo bhai.")
            message.stop_propagation()

    # ── JOIN REQUEST HANDLER ────────────────────────────────────
    @app.on_chat_join_request()
    async def join_request_handler(client, request):
        bot_info = get_bot_info(client.me.id)
        user_id   = request.from_user.id
        channel_id = request.chat.id

        if bot_info and bot_info.get("auto_approve"):
            # Auto approve enabled → approve immediately
            try:
                await client.approve_chat_join_request(channel_id, user_id)
                clear_join_request(channel_id, user_id)
                logger.info(f"Auto-approved {user_id} in {channel_id}")
            except Exception as e:
                logger.warning(f"Auto-approve failed: {e}")
        else:
            # ── NEW: Track pending request so user gets bot access ──
            mark_join_request(channel_id, user_id)
            logger.info(f"Marked pending request: user={user_id} channel={channel_id}")

    # ── /ping ────────────────────────────────────────────────────
    @app.on_message(filters.command("ping") & filters.private, group=1)
    async def ping_cmd(client, message):
        t0   = time.time()
        sent = await message.reply("🏓 Pong...")
        ms   = round((time.time() - t0) * 1000, 2)
        await sent.edit(
            f"🏓 **Pong!**\n\n"
            f"⚡ Latency: `{ms}ms`\n"
            f"⏳ Uptime: `{str(datetime.now() - START_TIME).split('.')[0]}`\n"
            f"🤖 Bots Online: `{len(ACTIVE_CLIENTS)}`"
        )

    # ── /restart ─────────────────────────────────────────────────
    @app.on_message(filters.command("restart") & filters.private, group=1)
    async def restart_cmd(client, message):
        if message.from_user.id != MAIN_ADMIN:
            return
        await message.reply("🔄 Restarting...")
        os.execl(sys.executable, sys.executable, *sys.argv)

    # ── /start ───────────────────────────────────────────────────
    @app.on_message(filters.command("start") & filters.private, group=1)
    async def start_handler(client, message):
        user_id = message.from_user.id
        bot_id  = client.me.id

        config = get_global_config()
        if config.get("maintenance") and user_id != MAIN_ADMIN:
            return await message.reply("🚧 **Maintenance Mode**\n\nBot is temporarily down.")

        if is_user_banned(user_id, bot_id):
            return await message.reply("🚫 You are banned from this bot!")

        deep_arg   = message.command[1] if len(message.command) > 1 else ""
        referred_by = None
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
            buttons.append([InlineKeyboardButton(
                "🔄 I Joined / Sent Request — Try Again",
                url=f"https://t.me/{client.me.username}?start={deep_arg}"
            )])
            return await message.reply(
                "⚠️ **Membership Required!**\n\n"
                "Please join the channels below.\n"
                "Agar join request bhej di hai toh bhi **Try Again** dabao 👇",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        bot_info        = get_bot_info(bot_id)
        auto_delete_time = bot_info.get("auto_delete_time", 600) if bot_info else 600

        # ── Deep link: single file ────────────────────────────
        if deep_arg.startswith("f_"):
            uid = deep_arg[2:]
            files = load_db(FILES_DB)
            file_data = files.get(uid)
            if not file_data:
                return await message.reply("❌ File not found or deleted.")

            files[uid]["access_count"] = files[uid].get("access_count", 0) + 1
            save_db(FILES_DB, files)

            try:
                sent_msg = await deliver_file(client, message.chat.id, file_data)
            except Exception as e:
                return await message.reply(f"❌ File unavailable!\n`{e}`")

            if sent_msg:
                is_premium = user_data.get("is_premium", False)
                if not is_premium:
                    asyncio.create_task(_auto_delete(sent_msg, auto_delete_time))
                    await message.reply(
                        f"⏳ **Auto-Delete Notice**\n\n"
                        f"File will be deleted in `{auto_delete_time // 60}` min(s).\n"
                        f"Save it! 💾"
                    )
                else:
                    await message.reply("🌟 **Premium:** Auto-delete disabled for you!")
            return

        # ── Deep link: batch ──────────────────────────────────
        elif deep_arg.startswith("b_"):
            batch_id   = deep_arg[2:]
            batches    = load_db(BATCH_DB)
            batch_data = batches.get(batch_id)
            if not batch_data:
                return await message.reply("❌ Batch not found or expired.")

            files  = load_db(FILES_DB)
            total  = len(batch_data['files'])
            status = await message.reply(f"📦 Sending batch ({total} files)...")
            sent   = 0

            for fid in batch_data['files']:
                f_data = files.get(fid)
                if not f_data:
                    continue
                try:
                    await deliver_file(client, message.chat.id, f_data)
                    sent += 1
                except Exception:
                    pass
                await asyncio.sleep(0.5)

            await status.delete()
            await message.reply(f"✅ Delivered **{sent}/{total}** files!")
            return

        # ── Standard welcome ──────────────────────────────────
        global_msg    = config.get("global_msg", "")
        welcome       = (bot_info.get('custom_welcome') if bot_info else None)
        welcome_image = (bot_info.get('welcome_image')  if bot_info else None)

        if global_msg:
            await message.reply(f"📢 **System Announcement**\n\n{global_msg}")

        if not welcome:
            greets = ["Hello", "Hey", "Welcome", "Namaste", "Greetings"]
            welcome = (
                f"✨ **{random.choice(greets)}, {message.from_user.first_name}!**\n\n"
                f"Welcome to the most **Advanced & Secure FileStore System**.\n\n"
                f"🛠 **Features:**\n"
                f" ├ 📂 Unlimited Cloud Storage\n"
                f" ├ 📦 Batch Mode (Multiple files → 1 link)\n"
                f" ├ 🤖 Bot Cloning\n"
                f" ├ ✏️ Caption & Thumbnail Editor\n"
                f" ├ 🔐 Auto-Destruct Files\n"
                f" └ ⚡ Instant Delivery\n\n"
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
        uid = message.from_user.id
        bi  = get_bot_info(client.me.id)
        if not (is_admin(uid) or (bi and bi.get('owner_id') == uid)):
            return
        await message.reply("⚡ **Admin Panel**", reply_markup=get_admin_panel_keyboard())

    # ── /supreme ─────────────────────────────────────────────────
    @app.on_message(filters.command("supreme") & filters.private, group=1)
    async def supreme_panel_cmd(client, message):
        if message.from_user.id != MAIN_ADMIN:
            return
        await message.reply(
            f"👑 **Supreme Panel**\n\n"
            f"🤖 Active Bots: `{len(ACTIVE_CLIENTS)}`\n"
            f"👥 Total Users: `{len(load_db(USERS_DB))}`\n"
            f"📁 Files: `{len(load_db(FILES_DB))}`",
            reply_markup=get_supreme_panel_keyboard()
        )

    # ── /stats ───────────────────────────────────────────────────
    @app.on_message(filters.command("stats") & filters.private, group=1)
    async def stats_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        if uid == MAIN_ADMIN:
            await message.reply(
                "🌐 **Global Analytics**\n━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 Total Bots: `{len(get_all_bots())}`\n"
                f"🟢 Online: `{len(ACTIVE_CLIENTS)}`\n"
                f"👥 Users: `{len(load_db(USERS_DB))}`\n"
                f"📁 Files: `{len(load_db(FILES_DB))}`\n"
                f"⏳ Uptime: `{str(datetime.now() - START_TIME).split('.')[0]}`"
            )
        else:
            ud   = get_user(uid, bot_id)
            ubts = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == uid]
            await message.reply(
                "📊 **Your Dashboard**\n━━━━━━━━━━━━━━━━━━━━\n"
                f"📤 Uploaded: `{ud.get('files_uploaded', 0) if ud else 0}`\n"
                f"📦 Batches: `{ud.get('batches_created', 0) if ud else 0}`\n"
                f"🤖 Bots Cloned: `{len(ubts)}`\n"
                f"💰 Points: `{ud.get('points', 0) if ud else 0}`\n"
                f"👥 Referrals: `{ud.get('referrals', 0) if ud else 0}`\n"
                f"💎 Premium: `{'Yes ✅' if ud and ud.get('is_premium') else 'No'}`"
            )

    # ═══════════════════════════════════════════════════════════
    # ✏️ CAPTION & THUMBNAIL EDITOR
    # ═══════════════════════════════════════════════════════════

    @app.on_message(filters.command("editfile") & filters.private, group=1)
    async def editfile_cmd(client, message):
        """Show the edit panel for a specific file."""
        uid    = message.from_user.id
        bot_id = client.me.id

        if len(message.command) < 2:
            return await message.reply(
                "✏️ **File Editor**\n\n"
                "Usage: `/editfile FILE_ID`\n\n"
                "Find your File IDs using `/listfiles`\n"
                "Or use the **Edit** button next to each file in `/listfiles`."
            )

        file_uid  = message.command[1]
        files     = load_db(FILES_DB)
        file_data = files.get(file_uid)

        if not file_data:
            return await message.reply("❌ File not found!")

        bi = get_bot_info(bot_id)
        can_edit = (uid == MAIN_ADMIN or is_admin(uid) or
                    (bi and bi.get('owner_id') == uid) or
                    file_data.get('user_id') == uid)
        if not can_edit:
            return await message.reply("❌ You can only edit your own files!")

        icon    = get_file_type_icon(file_data.get('file_name', ''))
        caption = file_data.get('caption') or '_(none)_'
        thumb   = '✅ Set' if file_data.get('custom_thumbnail') else '❌ Not set'
        mt      = file_data.get('media_type', 'document')

        await message.reply(
            f"✏️ **File Editor**\n\n"
            f"{icon} **{file_data.get('file_name', 'Unknown')}**\n"
            f"🆔 ID: `{file_uid}`\n"
            f"📊 Size: {format_size(file_data.get('file_size', 0))}\n"
            f"🎭 Type: `{mt}`\n"
            f"💬 Caption: {caption}\n"
            f"🖼 Thumbnail: {thumb}\n"
            f"👁 Views: `{file_data.get('access_count', 0)}`",
            reply_markup=get_file_edit_keyboard(file_uid)
        )

    @app.on_message(filters.command("editcaption") & filters.private, group=1)
    async def editcaption_cmd(client, message):
        """
        Usage:
          /editcaption FILE_ID New caption here
          OR  reply to text message with  /editcaption FILE_ID
        """
        uid    = message.from_user.id
        bot_id = client.me.id

        if len(message.command) < 2:
            return await message.reply(
                "✏️ **Edit Caption**\n\n"
                "Usage: `/editcaption FILE_ID New caption text`\n"
                "Or reply to a text message with `/editcaption FILE_ID`\n\n"
                "To remove caption: `/editcaption FILE_ID -clear`"
            )

        file_uid  = message.command[1]
        files     = load_db(FILES_DB)
        file_data = files.get(file_uid)

        if not file_data:
            return await message.reply("❌ File not found!")

        bi = get_bot_info(bot_id)
        can_edit = (uid == MAIN_ADMIN or is_admin(uid) or
                    (bi and bi.get('owner_id') == uid) or
                    file_data.get('user_id') == uid)
        if not can_edit:
            return await message.reply("❌ You can only edit your own files!")

        # Check if new caption provided inline
        if len(message.command) >= 3:
            raw = message.text.split(None, 2)
            new_caption = "" if raw[2].strip() == "-clear" else raw[2].strip()
            files[file_uid]['caption'] = new_caption or None
            save_db(FILES_DB, files)
            return await message.reply(
                f"✅ **Caption Updated!**\n\n"
                f"New caption: `{new_caption or '(removed)'}`",
                reply_markup=get_file_edit_keyboard(file_uid)
            )

        # Check if replying to a message
        if message.reply_to_message and message.reply_to_message.text:
            new_caption = message.reply_to_message.text.strip()
            files[file_uid]['caption'] = new_caption
            save_db(FILES_DB, files)
            return await message.reply(
                f"✅ **Caption Updated!**\n\n"
                f"New caption: `{new_caption}`",
                reply_markup=get_file_edit_keyboard(file_uid)
            )

        # Put user in caption-edit mode (FSM)
        TEMP_EDIT_DATA[uid] = {"mode": "caption", "uid": file_uid}
        await message.reply(
            f"✏️ **Enter New Caption**\n\n"
            f"File: `{file_data.get('file_name', file_uid)}`\n\n"
            f"Send the new caption text now.\n"
            f"Send `-clear` to remove caption.\n"
            f"Send /cancel to abort.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_edit")]
            ])
        )

    @app.on_message(filters.command("editthumbnail") & filters.private, group=1)
    async def editthumbnail_cmd(client, message):
        """
        Usage:
          Reply to a photo with  /editthumbnail FILE_ID
          Or just send  /editthumbnail FILE_ID  → bot will ask for photo next
        """
        uid    = message.from_user.id
        bot_id = client.me.id

        if len(message.command) < 2:
            return await message.reply(
                "🖼 **Edit Thumbnail**\n\n"
                "Usage:\n"
                "1. Reply to a photo with `/editthumbnail FILE_ID`\n"
                "2. Or send `/editthumbnail FILE_ID` alone → then send photo\n\n"
                "Only works for documents, videos, and audio files.\n"
                "To remove thumbnail: `/editthumbnail FILE_ID -clear`"
            )

        file_uid  = message.command[1]
        files     = load_db(FILES_DB)
        file_data = files.get(file_uid)

        if not file_data:
            return await message.reply("❌ File not found!")

        bi = get_bot_info(bot_id)
        can_edit = (uid == MAIN_ADMIN or is_admin(uid) or
                    (bi and bi.get('owner_id') == uid) or
                    file_data.get('user_id') == uid)
        if not can_edit:
            return await message.reply("❌ You can only edit your own files!")

        mt = file_data.get('media_type', 'document')
        if mt not in ('document', 'video', 'audio'):
            return await message.reply(
                f"❌ Thumbnails only work for documents, videos, and audio.\n"
                f"This file is a **{mt}** — thumbnail not applicable."
            )

        # -clear
        if len(message.command) >= 3 and message.command[2].lower() == "-clear":
            files[file_uid]['custom_thumbnail'] = None
            save_db(FILES_DB, files)
            return await message.reply(
                "✅ Thumbnail removed!",
                reply_markup=get_file_edit_keyboard(file_uid)
            )

        # Reply to a photo → set immediately
        if message.reply_to_message and message.reply_to_message.photo:
            thumb_file_id = message.reply_to_message.photo.file_id
            files[file_uid]['custom_thumbnail'] = thumb_file_id
            save_db(FILES_DB, files)
            return await message.reply(
                "✅ **Thumbnail Updated!**\n\nThe custom thumbnail has been saved.",
                reply_markup=get_file_edit_keyboard(file_uid)
            )

        # Put user in thumbnail-edit mode (FSM)
        TEMP_EDIT_DATA[uid] = {"mode": "thumbnail", "uid": file_uid}
        await message.reply(
            f"🖼 **Send New Thumbnail**\n\n"
            f"File: `{file_data.get('file_name', file_uid)}`\n\n"
            f"Send a **photo** as the new thumbnail.\n"
            f"Send /cancel to abort.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_edit")]
            ])
        )

    # ── EDIT FSM RESPONDER ───────────────────────────────────────
    # Handles the "waiting for caption text" and "waiting for thumbnail photo" states

    @app.on_message(filters.private & ~filters.command([
        "start","admin","supreme","clone","batch","done","cancel","setfs",
        "mybots","stats","help","broadcast","ban","unban","setmsg","botinfo",
        "settimer","setwelcomeimg","search","points","refer","premium",
        "shortener","buy_premium","setlog","restart","ping","listfiles",
        "editfile","editcaption","editthumbnail","delfile","addpoints",
        "gban","ungban","setpremium","info","setglobal","addadmin","deladmin",
    ]), group=2)
    async def fsm_responder(client, message):
        uid = message.from_user.id
        if uid not in TEMP_EDIT_DATA:
            return   # Not in an edit session

        session   = TEMP_EDIT_DATA[uid]
        mode      = session["mode"]
        file_uid  = session["uid"]
        files     = load_db(FILES_DB)

        if file_uid not in files:
            del TEMP_EDIT_DATA[uid]
            return await message.reply("❌ File no longer exists.")

        if mode == "caption":
            if not message.text:
                return await message.reply("❌ Please send **text** for the caption.")
            txt = message.text.strip()
            files[file_uid]['caption'] = None if txt == "-clear" else txt
            save_db(FILES_DB, files)
            del TEMP_EDIT_DATA[uid]
            await message.reply(
                f"✅ **Caption Updated!**\n\n"
                f"New: `{txt if txt != '-clear' else '(removed)'}`",
                reply_markup=get_file_edit_keyboard(file_uid)
            )

        elif mode == "thumbnail":
            if not message.photo:
                return await message.reply("❌ Please send a **photo** as thumbnail.")
            thumb_id = message.photo.file_id
            files[file_uid]['custom_thumbnail'] = thumb_id
            save_db(FILES_DB, files)
            del TEMP_EDIT_DATA[uid]
            await message.reply(
                "✅ **Thumbnail Updated!**\n\nCustom thumbnail has been saved.",
                reply_markup=get_file_edit_keyboard(file_uid)
            )

    # ── /listfiles ───────────────────────────────────────────────
    @app.on_message(filters.command("listfiles") & filters.private, group=1)
    async def list_files_handler(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        files  = load_db(FILES_DB)
        bi     = get_bot_info(bot_id)
        is_super = (uid == MAIN_ADMIN or is_admin(uid) or (bi and bi.get('owner_id') == uid))

        if is_super:
            user_files = [(k, f) for k, f in files.items() if f.get('bot_id') == bot_id]
        else:
            user_files = [(k, f) for k, f in files.items()
                         if f.get('bot_id') == bot_id and f.get('user_id') == uid]

        if not user_files:
            return await message.reply("📭 No files found!")

        recent = sorted(user_files, key=lambda x: x[1].get('upload_date', ''), reverse=True)[:10]
        label  = "All Files" if is_super else "Your Files"
        text   = f"📋 **{label}** ({len(user_files)} total, showing last {len(recent)})\n\n"

        for k, f in recent:
            icon  = get_file_type_icon(f.get('file_name', ''))
            name  = (f.get('file_name') or 'Unknown')[:35]
            thumb = "🖼" if f.get('custom_thumbnail') else ""
            cap   = "💬" if f.get('caption') else ""
            text += (
                f"{icon} **{name}** {thumb}{cap}\n"
                f"   📊 {format_size(f.get('file_size', 0))} | "
                f"👁 {f.get('access_count', 0)} views | "
                f"`{k}`\n\n"
            )

        # Show edit/share buttons for first 5 files
        buttons = []
        for k, f in recent[:5]:
            icon = get_file_type_icon(f.get('file_name', ''))
            name = (f.get('file_name') or 'Unknown')[:20]
            buttons.append([
                InlineKeyboardButton(
                    f"{icon} {name}",
                    url=f"https://t.me/{client.me.username}?start=f_{k}"
                ),
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_file_{k}"),
            ])

        await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)

    # ── /delfile ─────────────────────────────────────────────────
    @app.on_message(filters.command("delfile") & filters.private, group=1)
    async def del_file_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        if len(message.command) < 2:
            return await message.reply("Usage: `/delfile FILE_ID`")
        file_uid  = message.command[1]
        files     = load_db(FILES_DB)
        file_data = files.get(file_uid)
        if not file_data:
            return await message.reply("❌ File not found!")
        bi = get_bot_info(bot_id)
        can_del = (uid == MAIN_ADMIN or is_admin(uid) or
                   (bi and bi.get('owner_id') == uid) or
                   file_data.get('user_id') == uid)
        if not can_del:
            return await message.reply("❌ You can only delete your own files!")
        del files[file_uid]
        save_db(FILES_DB, files)
        await message.reply(
            f"🗑 **File Deleted**\n\n"
            f"📁 `{file_data.get('file_name', 'Unknown')}`\n"
            f"🆔 `{file_uid}`"
        )

    # ── /addpoints ───────────────────────────────────────────────
    @app.on_message(filters.command("addpoints") & filters.private, group=1)
    async def addpoints_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        if not (uid == MAIN_ADMIN or is_admin(uid) or (bi and bi.get('owner_id') == uid)):
            return
        if len(message.command) < 3:
            return await message.reply("Usage: `/addpoints USER_ID AMOUNT`")
        try:
            target, amount = int(message.command[1]), int(message.command[2])
        except ValueError:
            return await message.reply("❌ Invalid values!")
        update_user_stats(target, bot_id, "points", amount)
        await message.reply(f"✅ Added `{amount}` points to `{target}`!")

    # ── /mybots ──────────────────────────────────────────────────
    @app.on_message(filters.command("mybots") & filters.private, group=1)
    async def my_bots_cmd(client, message):
        uid  = message.from_user.id
        ubts = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == uid]
        if not ubts:
            return await message.reply(
                "🤖 **No Bots Yet!**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 BotFather", url="https://t.me/BotFather")]
                ])
            )
        text = f"🤖 **Your Bots ({len(ubts)})**\n\n"
        for i, b in enumerate(ubts[:10], 1):
            st = "🟢" if b['bot_id'] in ACTIVE_CLIENTS else "🔴"
            text += f"{i}. {st} @{b['bot_username']}\n"
        await message.reply(text)

    # ── /ban /unban /info /setpremium /gban /ungban ──────────────
    @app.on_message(
        filters.command(["ban","unban","info","setpremium","gban","ungban"]) & filters.private,
        group=1
    )
    async def admin_utils(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        if not (uid == MAIN_ADMIN or is_admin(uid) or (bi and bi.get('owner_id') == uid)):
            return
        if len(message.command) < 2:
            return await message.reply(f"Usage: `/{message.command[0]} USER_ID`")
        try:
            target = int(message.command[1])
        except ValueError:
            return await message.reply("❌ Invalid User ID!")
        cmd = message.command[0]
        if cmd == "ban":
            await message.reply(f"🚫 `{target}` banned." if ban_user(target, bot_id) else "❌ User not found.")
        elif cmd == "unban":
            await message.reply(f"✅ `{target}` unbanned." if unban_user(target, bot_id) else "❌ User not found.")
        elif cmd == "setpremium":
            users = load_db(USERS_DB)
            k = f"{bot_id}_{target}"
            if k in users:
                users[k]["is_premium"] = True
                save_db(USERS_DB, users)
                await message.reply(f"💎 `{target}` is now Premium!")
            else:
                await message.reply("❌ User not found.")
        elif cmd == "gban":
            if uid != MAIN_ADMIN: return
            cfg = get_global_config()
            gb  = cfg.get("global_bans", [])
            if target not in gb:
                gb.append(target)
                update_global_config("global_bans", gb)
                await message.reply(f"🌍 Globally banned `{target}`!")
            else:
                await message.reply("Already globally banned.")
        elif cmd == "ungban":
            if uid != MAIN_ADMIN: return
            cfg = get_global_config()
            gb  = cfg.get("global_bans", [])
            if target in gb:
                gb.remove(target)
                update_global_config("global_bans", gb)
                await message.reply(f"✅ Globally unbanned `{target}`!")
            else:
                await message.reply("Not in global ban list.")
        elif cmd == "info":
            user = get_user(target, bot_id)
            if not user:
                return await message.reply("❌ User not found.")
            await message.reply(
                f"👤 **User Info**\n\n"
                f"🆔 `{user['user_id']}`\n"
                f"🏷 {user.get('name','Unknown')}\n"
                f"🔗 @{user.get('username') or 'None'}\n"
                f"📅 {user.get('join_date','N/A')}\n"
                f"🚫 Banned: {'Yes' if user.get('is_banned') else 'No'}\n"
                f"💎 Premium: {'Yes' if user.get('is_premium') else 'No'}\n"
                f"💰 Points: `{user.get('points',0)}`\n"
                f"📤 Uploaded: `{user.get('files_uploaded',0)}`\n"
                f"📦 Batches: `{user.get('batches_created',0)}`\n"
                f"👥 Referrals: `{user.get('referrals',0)}`"
            )

    # ── /setmsg ──────────────────────────────────────────────────
    @app.on_message(filters.command("setmsg") & filters.private, group=1)
    async def set_msg_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        if not bi or (bi.get('owner_id') != uid and uid != MAIN_ADMIN):
            return await message.reply("❌ Only bot owner!")
        if not message.reply_to_message or not message.reply_to_message.text:
            return await message.reply("Reply to a text message with `/setmsg`.")
        update_bot_info(bot_id, 'custom_welcome', message.reply_to_message.text)
        await message.reply("✅ Welcome message updated!")

    # ── /settimer ────────────────────────────────────────────────
    @app.on_message(filters.command("settimer") & filters.private, group=1)
    async def set_timer_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        if not bi or (bi.get('owner_id') != uid and uid != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")
        if len(message.command) < 2:
            curr = bi.get('auto_delete_time', 600)
            return await message.reply(f"⏱ Current: `{curr}s` ({curr//60}min)\nUsage: `/settimer SECONDS`")
        try:
            secs = int(message.command[1])
            if secs < 60:
                return await message.reply("❌ Minimum 60 seconds!")
            update_bot_info(bot_id, 'auto_delete_time', secs)
            await message.reply(f"✅ Auto-delete set to `{secs}s` ({secs//60}min).")
        except ValueError:
            await message.reply("❌ Invalid number!")

    # ── /shortener ───────────────────────────────────────────────
    @app.on_message(filters.command("shortener") & filters.private, group=1)
    async def shortener_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        if not bi or (bi.get('owner_id') != uid and uid != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")
        if len(message.command) < 2:
            status = "✅ Enabled" if bi.get("is_shortener_enabled") else "❌ Disabled"
            return await message.reply(
                f"🔗 **Shortener**\n\nStatus: {status}\n"
                f"URL: `{bi.get('shortener_url') or 'Not set'}`\n\n"
                f"Commands: `on`, `off`, `set URL APIKEY`"
            )
        cmd = message.command[1].lower()
        if cmd == "on":
            if not bi.get("shortener_url") or not bi.get("shortener_api"):
                return await message.reply("❌ Set URL+API first: `/shortener set URL APIKEY`")
            update_bot_info(bot_id, "is_shortener_enabled", True)
            await message.reply("✅ Shortener enabled!")
        elif cmd == "off":
            update_bot_info(bot_id, "is_shortener_enabled", False)
            await message.reply("✅ Shortener disabled!")
        elif cmd == "set":
            if len(message.command) < 4:
                return await message.reply("Usage: `/shortener set URL APIKEY`")
            update_bot_info(bot_id, "shortener_url", message.command[2])
            update_bot_info(bot_id, "shortener_api", message.command[3])
            await message.reply(f"✅ Configured: `{message.command[2]}`")

    # ── /setlog ──────────────────────────────────────────────────
    @app.on_message(filters.command("setlog") & filters.private, group=1)
    async def setlog_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        if not bi or (bi.get('owner_id') != uid and uid != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")
        if len(message.command) < 2:
            return await message.reply(f"📝 Log Channel: `{bi.get('log_channel') or 'Not Set'}`\nUsage: `/setlog CHANNEL_ID` or `/setlog off`")
        if message.command[1].lower() == "off":
            update_bot_info(bot_id, 'log_channel', None)
            return await message.reply("✅ Log channel disabled!")
        try:
            cid = int(message.command[1])
            update_bot_info(bot_id, 'log_channel', cid)
            await message.reply(f"✅ Log channel set to `{cid}`.")
        except ValueError:
            await message.reply("❌ Invalid Channel ID!")

    # ── /setwelcomeimg ───────────────────────────────────────────
    @app.on_message(filters.command("setwelcomeimg") & filters.private, group=1)
    async def set_welcome_img_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        if not bi or (bi.get('owner_id') != uid and uid != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("🖼 Reply to a **photo** with `/setwelcomeimg`!")
        update_bot_info(bot_id, 'welcome_image', message.reply_to_message.photo.file_id)
        await message.reply("✅ Welcome image updated!")

    # ── /help ────────────────────────────────────────────────────
    @app.on_message(filters.command("help") & filters.private, group=1)
    async def help_cmd(client, message):
        await message.reply(
            "🚀 **FileStore Bot — Complete Help**\n\n"
            "**📂 File Sharing:**\n"
            " └ Send any file → get a secure link\n\n"
            "**📦 Batch Mode:**\n"
            " 1. `/batch` → start | 2. Send files | 3. `/done` → get link\n\n"
            "**✏️ Caption & Thumbnail Editor:**\n"
            " • `/editfile FILE_ID` — Open edit panel\n"
            " • `/editcaption FILE_ID New caption` — Edit caption\n"
            " • `/editcaption FILE_ID -clear` — Remove caption\n"
            " • `/editthumbnail FILE_ID` — Set custom thumbnail\n"
            " • Reply to photo with `/editthumbnail FILE_ID`\n"
            " • `/editthumbnail FILE_ID -clear` — Remove thumbnail\n\n"
            "**🤖 Bot Cloning:**\n"
            " 1. @BotFather → /newbot → copy token\n"
            " 2. `/clone YOUR_TOKEN`\n\n"
            "**🔒 Force Subscribe (NEW):**\n"
            " Users with pending join requests also get access!\n\n"
            "**⚙️ Admin Commands:**\n"
            " • `/setfs add -100xxx` — Add force sub\n"
            " • `/settimer 600` — Auto-delete timer\n"
            " • `/ban` `/unban` `/info` — User management\n\n"
            "**📊 Stats:** `/stats` | **📋 Files:** `/listfiles`"
        )

    # ── /setglobal ───────────────────────────────────────────────
    @app.on_message(filters.command("setglobal") & filters.private, group=1)
    async def set_global_cmd(client, message):
        if message.from_user.id != MAIN_ADMIN: return
        if len(message.command) < 2:
            return await message.reply("Usage: `/setglobal MESSAGE` or `/setglobal off`")
        txt = message.text.split(None, 1)[1]
        update_global_config("global_msg", "" if txt.lower() == "off" else txt)
        await message.reply(f"✅ Global message {'cleared' if txt.lower() == 'off' else 'set'}!")

    # ── /addadmin /deladmin ──────────────────────────────────────
    @app.on_message(filters.command(["addadmin","deladmin"]) & filters.private, group=1)
    async def manage_admin_cmd(client, message):
        if message.from_user.id != MAIN_ADMIN: return
        if len(message.command) < 2:
            return await message.reply(f"Usage: `/{message.command[0]} USER_ID`")
        target  = message.command[1]
        admins  = load_db(ADMINS_DB)
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

    # ── /refer & /points & /premium & /buy_premium ───────────────
    @app.on_message(filters.command("refer") & filters.private, group=1)
    async def refer_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        ud     = get_user(uid, bot_id)
        link   = f"https://t.me/{client.me.username}?start=ref_{uid}"
        await message.reply(
            f"🔗 **Referral Program**\n\n"
            f"💰 Points: `{ud.get('points',0) if ud else 0}`\n"
            f"👥 Referrals: `{ud.get('referrals',0) if ud else 0}`\n\n"
            f"🎁 Earn **10 points** per referral!\n500 points = Premium 🌟\n\n"
            f"Your Link:\n`{link}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Link",
                    url=f"https://t.me/share/url?url={link}&text=Join+this+amazing+bot!")]
            ])
        )

    @app.on_message(filters.command("points") & filters.private, group=1)
    async def points_cmd(client, message):
        ud = get_user(message.from_user.id, client.me.id)
        pts = ud.get('points', 0) if ud else 0
        await message.reply(f"💰 **Your Points: `{pts}`**\n\n500 points = Premium. `/refer` to earn more.")

    @app.on_message(filters.command("premium") & filters.private, group=1)
    async def premium_cmd(client, message):
        ud = get_user(message.from_user.id, client.me.id)
        is_p = ud.get("is_premium", False) if ud else False
        await message.reply(
            f"🌟 **Premium Membership**\n\nStatus: {'✅ Active' if is_p else '❌ Inactive'}\n\n"
            f"Benefits:\n ├ 🚀 No auto-delete\n ├ 🎯 Priority delivery\n └ 📂 Unlimited batch\n\n"
            f"Cost: 500 points → `/buy_premium`\nOr contact @{get_main_bot_username()}"
        )

    @app.on_message(filters.command("buy_premium") & filters.private, group=1)
    async def buy_premium_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        ud     = get_user(uid, bot_id)
        if not ud:
            return await message.reply("❌ Please /start the bot first.")
        if ud.get("is_premium"):
            return await message.reply("✅ You already have Premium!")
        if ud.get("points", 0) < 500:
            need = 500 - ud.get("points", 0)
            return await message.reply(f"❌ Need `{need}` more points. Use `/refer` to earn!")
        users = load_db(USERS_DB)
        k = f"{bot_id}_{uid}"
        users[k]["points"] -= 500
        users[k]["is_premium"] = True
        save_db(USERS_DB, users)
        await message.reply("🎉 **You are now Premium!**\n\nAuto-delete disabled. Enjoy!")

    # ── /botinfo ─────────────────────────────────────────────────
    @app.on_message(filters.command("botinfo") & filters.private, group=1)
    async def botinfo_cmd(client, message):
        bot_id = client.me.id
        bi = get_bot_info(bot_id)
        if not bi:
            return await message.reply("ℹ️ Bot info not in DB.")
        children = len(get_child_bots(bot_id))
        await message.reply(
            f"ℹ️ **Bot Info**\n\n"
            f"🤖 @{client.me.username}\n"
            f"👤 Owner: {bi.get('owner_name','Unknown')}\n"
            f"🌳 Child Bots: `{children}`\n"
            f"📢 Force Sub: `{len(bi.get('force_subs',[]))}` channels\n"
            f"⏱ Auto-Delete: `{bi.get('auto_delete_time',600)}s`\n"
            f"🔗 Shortener: `{'ON' if bi.get('is_shortener_enabled') else 'OFF'}`\n"
            f"✅ Auto-Approve: `{'ON' if bi.get('auto_approve') else 'OFF'}`"
        )

    # ── /clone ───────────────────────────────────────────────────
    @app.on_message(filters.command("clone") & filters.private, group=1)
    async def clone_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        if is_user_banned(uid, bot_id):
            return await message.reply("🚫 Banned!")
        ubts = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == uid]
        if len(message.command) < 2:
            return await message.reply(
                f"🤖 **Clone Bot**\n\nYour bots: `{len(ubts)}`\n\n"
                f"1. @BotFather → /newbot\n2. Copy token\n3. `/clone TOKEN`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 Open BotFather", url="https://t.me/BotFather")]
                ])
            )
        token = message.command[1]
        for b in get_all_bots().values():
            if isinstance(b, dict) and b.get("token") == token:
                return await message.reply("❌ Token already registered!")
        msg = await message.reply("🔄 Cloning...")
        try:
            new_app = await start_bot(token, parent_bot_id=bot_id)
            if new_app:
                me = await new_app.get_me()
                save_bot_info(token, me.id, me.username, uid, message.from_user.first_name, bot_id)
                await msg.edit(
                    f"✅ **Cloned!**\n\n🤖 @{me.username}\n🆔 `{me.id}`",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🚀 Open Bot", url=f"https://t.me/{me.username}")]
                    ])
                )
            else:
                await msg.edit("❌ Failed! Invalid token.")
        except Exception as e:
            await msg.edit(f"❌ Error: `{e}`")

    # ── /setfs ───────────────────────────────────────────────────
    @app.on_message(filters.command("setfs") & filters.private, group=1)
    async def setfs_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        if not bi or (bi.get('owner_id') != uid and uid != MAIN_ADMIN):
            return await message.reply("❌ Only bot owner!")
        fs = bi.get("force_subs", [])
        if len(message.command) < 2:
            text = f"⚙️ **Force Subscribe** ({len(fs)}/{MAX_FORCE_SUB_CHANNELS})\n\n"
            if not fs:
                text += "None configured.\n"
            else:
                for i, f in enumerate(fs, 1):
                    cid  = f['channel_id'] if isinstance(f, dict) else f
                    lnk  = (f.get('invite_link') if isinstance(f, dict) else None) or 'Auto'
                    text += f"{i}. `{cid}` — {lnk}\n"
            text += "\nCommands: `add -100xxx [link]`, `del -100xxx`, `clear`\n⚠️ Bot must be Admin!"
            return await message.reply(text)
        cmd = message.command[1].lower()
        if cmd in ("clear","off"):
            update_bot_info(bot_id, 'force_subs', [])
            n = cascade_force_subs(bot_id, [])
            return await message.reply(f"✅ Cleared! ({n} child bots updated)")
        if cmd == "add":
            if len(fs) >= MAX_FORCE_SUB_CHANNELS:
                return await message.reply(f"❌ Max {MAX_FORCE_SUB_CHANNELS} channels!")
            if len(message.command) < 3:
                return await message.reply("Usage: `/setfs add -100xxx [invite_link]`")
            try:
                cid  = int(message.command[2])
                lnk  = message.command[3] if len(message.command) > 3 else None
            except ValueError:
                return await message.reply("❌ Invalid Channel ID!")
            try:
                await client.get_chat_member(cid, client.me.id)
            except Exception:
                return await message.reply("❌ I'm not admin/member in that channel!")
            fs.append({"channel_id": cid, "invite_link": lnk})
            update_bot_info(bot_id, 'force_subs', fs)
            n = cascade_force_subs(bot_id, fs)
            return await message.reply(f"✅ Added `{cid}`! ({n} child bots updated)")
        if cmd == "del":
            if len(message.command) < 3:
                return await message.reply("Usage: `/setfs del -100xxx`")
            try:
                cid = int(message.command[2])
            except ValueError:
                return await message.reply("❌ Invalid Channel ID!")
            new_fs = [f for f in fs if (f['channel_id'] if isinstance(f, dict) else f) != cid]
            if len(new_fs) == len(fs):
                return await message.reply("❌ Channel not in list!")
            update_bot_info(bot_id, 'force_subs', new_fs)
            n = cascade_force_subs(bot_id, new_fs)
            return await message.reply(f"✅ Removed `{cid}`! ({n} child bots updated)")
        await message.reply("❌ Unknown: use `add`, `del`, `clear`")

    # ── /broadcast ───────────────────────────────────────────────
    @app.on_message(filters.command("broadcast") & filters.private, group=1)
    async def broadcast_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        can_bc = False
        target_bots = []
        if uid == MAIN_ADMIN:
            can_bc = True
            target_bots = list(ACTIVE_CLIENTS.keys())
        elif bi and bi.get('owner_id') == uid:
            can_bc = True
            target_bots = [bot_id] + [d['bot_id'] for d in get_all_descendant_bots(bot_id) if d['bot_id'] in ACTIVE_CLIENTS]
        if not can_bc:
            return await message.reply("❌ No permission!")
        if not message.reply_to_message:
            total = sum(len(get_all_users(bid)) for bid in target_bots)
            return await message.reply(
                f"📢 **Broadcast**\n\n🤖 Bots: `{len(target_bots)}`\n👥 Users: `{total}`\n\nReply to a message with `/broadcast`."
            )
        TEMP_BROADCAST_DATA[uid] = {"message": message.reply_to_message, "bot_ids": target_bots}
        await message.reply(
            f"⚠️ **Confirm Broadcast?**\n\n🤖 `{len(target_bots)}` bots\n\nThis will message ALL users.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Send", callback_data="confirm_broadcast"),
                 InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
            ])
        )

    # ── /batch /done /cancel ─────────────────────────────────────
    @app.on_message(filters.command("batch") & filters.private, group=1)
    async def batch_start_cmd(client, message):
        uid = message.from_user.id
        if is_user_banned(uid, client.me.id):
            return await message.reply("🚫 Banned!")
        TEMP_BATCH_DATA[uid] = []
        await message.reply("📦 **Batch Mode ON!**\n\nSend files now. `/done` to finish. `/cancel` to abort.")

    @app.on_message(filters.command("done") & filters.private, group=1)
    async def batch_done_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        bi     = get_bot_info(bot_id)
        if uid not in TEMP_BATCH_DATA or not TEMP_BATCH_DATA[uid]:
            return await message.reply("❌ No files in batch! Start with `/batch`.")
        file_ids  = TEMP_BATCH_DATA.pop(uid)
        batch_id  = get_unique_id()
        batches   = load_db(BATCH_DB)
        batches[batch_id] = {"files": file_ids, "created_by": uid, "bot_id": bot_id, "date": str(datetime.now())}
        save_db(BATCH_DB, batches)
        update_user_stats(uid, bot_id, "batches_created")
        link       = f"https://t.me/{client.me.username}?start=b_{batch_id}"
        short_link = await get_short_link(bi, link)
        await message.reply(
            f"✅ **Batch Created!**\n\n📦 Files: `{len(file_ids)}`\n\n🔗 `{short_link}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Batch", url=f"https://t.me/share/url?url={short_link}")]
            ])
        )

    @app.on_message(filters.command("cancel") & filters.private, group=1)
    async def cancel_cmd(client, message):
        uid = message.from_user.id
        popped_batch = TEMP_BATCH_DATA.pop(uid, None)
        popped_edit  = TEMP_EDIT_DATA.pop(uid, None)
        if popped_batch is not None or popped_edit is not None:
            await message.reply("❌ Operation cancelled!")
        else:
            await message.reply("Nothing to cancel.")

    # ── INLINE SEARCH ────────────────────────────────────────────
    @app.on_inline_query()
    async def inline_search(client, query):
        q = query.query.strip().lower()
        if not q:
            return await query.answer([], cache_time=1)
        bot_id  = client.me.id
        files   = load_db(FILES_DB)
        results = []
        for uid, f in files.items():
            if f.get('bot_id') == bot_id and q in f.get('file_name', '').lower():
                icon = get_file_type_icon(f.get('file_name', ''))
                link = f"https://t.me/{client.me.username}?start=f_{uid}"
                thumb_icon = "🖼 " if f.get('custom_thumbnail') else ""
                results.append(InlineQueryResultArticle(
                    title=f"{icon} {f.get('file_name', 'Unknown')}",
                    description=f"{thumb_icon}📊 {format_size(f.get('file_size',0))} | 👁 {f.get('access_count',0)} views",
                    input_message_content=InputTextMessageContent(
                        f"{icon} **{f.get('file_name')}**\n"
                        f"📊 `{format_size(f.get('file_size',0))}`\n🔗 {link}"
                    ),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Get File", url=link)]])
                ))
            if len(results) >= 20: break
        await query.answer(results, cache_time=1)

    # ── /search ──────────────────────────────────────────────────
    @app.on_message(filters.command("search") & filters.private, group=1)
    async def search_cmd(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id
        if is_user_banned(uid, bot_id):
            return await message.reply("🚫 Banned!")
        if len(message.command) < 2:
            return await message.reply("🔍 Usage: `/search FILENAME`")
        q = message.text.split(None, 1)[1].lower()
        files = load_db(FILES_DB)
        results = [(k, f) for k, f in files.items()
                   if f.get('bot_id') == bot_id and q in f.get('file_name', '').lower()][:10]
        if not results:
            return await message.reply(f"❌ No files found for: `{q}`")
        text    = f"🔍 **Results for** `{q}` ({len(results)} found)\n\n"
        buttons = []
        for k, f in results:
            icon = get_file_type_icon(f.get('file_name', ''))
            name = f.get('file_name', 'Unknown')
            link = f"https://t.me/{client.me.username}?start=f_{k}"
            text += f"{icon} `{name[:40]}`\n   📊 {format_size(f.get('file_size',0))}\n\n"
            buttons.append([InlineKeyboardButton(f"{icon} {name[:30]}", url=link)])
        await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))

    # ── FILE HANDLER ─────────────────────────────────────────────
    @app.on_message(
        (filters.document | filters.video | filters.audio | filters.photo) & filters.private,
        group=1
    )
    async def file_handler(client, message):
        uid    = message.from_user.id
        bot_id = client.me.id

        if is_user_banned(uid, bot_id):
            return await message.reply("🚫 Banned!")

        # If waiting for a thumbnail photo in edit mode
        if uid in TEMP_EDIT_DATA and TEMP_EDIT_DATA[uid].get("mode") == "thumbnail":
            if message.photo:
                return  # Let fsm_responder handle it (group=2 runs after group=1)

        try:
            db_msg = await message.forward(DB_CHANNEL)
        except Exception as e:
            logger.error(f"DB Channel forward failed: {e}")
            return await message.reply("❌ **DB Channel Error!** Contact admin.")

        original_caption = message.caption

        if db_msg.photo:
            file_id    = db_msg.photo.file_id
            file_name  = f"photo_{db_msg.photo.file_unique_id}.jpg"
            file_size  = db_msg.photo.file_size or 0
            media_type = "photo"
        elif db_msg.video:
            file_id    = db_msg.video.file_id
            file_name  = db_msg.video.file_name or f"video_{db_msg.video.file_unique_id}.mp4"
            file_size  = db_msg.video.file_size or 0
            media_type = "video"
        elif db_msg.audio:
            file_id    = db_msg.audio.file_id
            file_name  = db_msg.audio.file_name or f"audio_{db_msg.audio.file_unique_id}.mp3"
            file_size  = db_msg.audio.file_size or 0
            media_type = "audio"
        elif db_msg.document:
            file_id    = db_msg.document.file_id
            file_name  = db_msg.document.file_name or f"file_{db_msg.document.file_unique_id}"
            file_size  = db_msg.document.file_size or 0
            media_type = "document"
        else:
            return

        unique_id = get_unique_id()
        files     = load_db(FILES_DB)
        files[unique_id] = {
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "caption": original_caption,
            "user_id": uid,
            "bot_id": bot_id,
            "upload_date": str(datetime.now()),
            "db_msg_id": db_msg.id,
            "access_count": 0,
            "media_type": media_type,          # NEW: stored for thumbnail delivery
            "custom_thumbnail": None            # NEW: initially no custom thumb
        }
        save_db(FILES_DB, files)
        add_to_cache(file_id, db_msg.id, DB_CHANNEL, bot_id, original_caption)
        update_user_stats(uid, bot_id, "files_uploaded")

        # Log channel
        bi = get_bot_info(bot_id)
        if bi and bi.get("log_channel"):
            try:
                icon = get_file_type_icon(file_name)
                await client.copy_message(
                    bi["log_channel"], message.chat.id, message.id,
                    caption=(
                        f"📤 **New Upload**\n\n"
                        f"{icon} `{file_name}`\n"
                        f"📊 {format_size(file_size)}\n"
                        f"👤 `{uid}`\n🆔 `{unique_id}`"
                    )
                )
            except Exception:
                pass

        # Batch mode
        if uid in TEMP_BATCH_DATA:
            TEMP_BATCH_DATA[uid].append(unique_id)
            icon = get_file_type_icon(file_name)
            await message.reply(
                f"✅ **Added to Batch!**\n\n{icon} `{file_name}`\n"
                f"📦 Total: `{len(TEMP_BATCH_DATA[uid])}`",
                quote=True
            )
        else:
            link       = f"https://t.me/{client.me.username}?start=f_{unique_id}"
            short_link = await get_short_link(bi, link)
            icon       = get_file_type_icon(file_name)
            await message.reply(
                f"✅ **File Saved!**\n\n"
                f"{icon} `{file_name}`\n"
                f"📊 {format_size(file_size)}\n"
                f"🆔 `{unique_id}`\n\n"
                f"🔗 **Link:**\n`{short_link}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={short_link}"),
                     InlineKeyboardButton("✏️ Edit File", callback_data=f"edit_file_{unique_id}")]
                ])
            )

    # ═══════════════════════════════════════════════════════════
    # 🖱 CALLBACK QUERY HANDLER
    # ═══════════════════════════════════════════════════════════

    @app.on_callback_query(group=1)
    async def callback_handler(client, callback):
        uid    = callback.from_user.id
        data   = callback.data
        bot_id = client.me.id

        if is_user_banned(uid, bot_id):
            return await callback.answer("🚫 Banned!", show_alert=True)

        # ── Edit File Panel ──────────────────────────────────────
        if data.startswith("edit_file_"):
            file_uid  = data[len("edit_file_"):]
            files     = load_db(FILES_DB)
            file_data = files.get(file_uid)
            if not file_data:
                return await callback.answer("❌ File not found!", show_alert=True)
            bi = get_bot_info(bot_id)
            can = (uid == MAIN_ADMIN or is_admin(uid) or
                   (bi and bi.get('owner_id') == uid) or
                   file_data.get('user_id') == uid)
            if not can:
                return await callback.answer("❌ Not your file!", show_alert=True)
            icon    = get_file_type_icon(file_data.get('file_name', ''))
            caption = file_data.get('caption') or '_(none)_'
            thumb   = '✅ Set' if file_data.get('custom_thumbnail') else '❌ None'
            await callback.message.edit(
                f"✏️ **File Editor**\n\n"
                f"{icon} **{file_data.get('file_name','Unknown')}**\n"
                f"🆔 `{file_uid}`\n"
                f"📊 {format_size(file_data.get('file_size',0))}\n"
                f"🎭 Type: `{file_data.get('media_type','document')}`\n"
                f"💬 Caption: {caption}\n"
                f"🖼 Thumbnail: {thumb}\n"
                f"👁 Views: `{file_data.get('access_count',0)}`",
                reply_markup=get_file_edit_keyboard(file_uid)
            )
            await callback.answer()

        elif data.startswith("edit_caption_"):
            file_uid = data[len("edit_caption_"):]
            files    = load_db(FILES_DB)
            if file_uid not in files:
                return await callback.answer("❌ File not found!", show_alert=True)
            TEMP_EDIT_DATA[uid] = {"mode": "caption", "uid": file_uid}
            await callback.message.edit(
                f"✏️ **Edit Caption**\n\n"
                f"File: `{files[file_uid].get('file_name','Unknown')}`\n\n"
                f"Send the **new caption** text.\n"
                f"Send `-clear` to remove caption.\n"
                f"Send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_edit")]
                ])
            )
            await callback.answer("✏️ Send new caption now")

        elif data.startswith("edit_thumb_"):
            file_uid  = data[len("edit_thumb_"):]
            files     = load_db(FILES_DB)
            file_data = files.get(file_uid)
            if not file_data:
                return await callback.answer("❌ File not found!", show_alert=True)
            mt = file_data.get('media_type', 'document')
            if mt not in ('document', 'video', 'audio'):
                return await callback.answer(
                    f"❌ Thumbnails only for docs/videos/audio (this is {mt})",
                    show_alert=True
                )
            TEMP_EDIT_DATA[uid] = {"mode": "thumbnail", "uid": file_uid}
            await callback.message.edit(
                f"🖼 **Edit Thumbnail**\n\n"
                f"File: `{file_data.get('file_name','Unknown')}`\n\n"
                f"Send a **photo** as the new thumbnail.\n"
                f"Send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗑 Remove Thumbnail", callback_data=f"remove_thumb_{file_uid}")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_edit")]
                ])
            )
            await callback.answer("🖼 Send a photo as thumbnail")

        elif data.startswith("remove_thumb_"):
            file_uid = data[len("remove_thumb_"):]
            files    = load_db(FILES_DB)
            if file_uid in files:
                files[file_uid]['custom_thumbnail'] = None
                save_db(FILES_DB, files)
                TEMP_EDIT_DATA.pop(uid, None)
                await callback.answer("✅ Thumbnail removed!", show_alert=True)
                await callback.message.edit(
                    "✅ Thumbnail removed!",
                    reply_markup=get_file_edit_keyboard(file_uid)
                )
            else:
                await callback.answer("❌ File not found!", show_alert=True)

        elif data.startswith("del_file_"):
            file_uid  = data[len("del_file_"):]
            files     = load_db(FILES_DB)
            file_data = files.get(file_uid)
            if not file_data:
                return await callback.answer("❌ Already deleted!", show_alert=True)
            bi = get_bot_info(bot_id)
            can = (uid == MAIN_ADMIN or is_admin(uid) or
                   (bi and bi.get('owner_id') == uid) or
                   file_data.get('user_id') == uid)
            if not can:
                return await callback.answer("❌ Not your file!", show_alert=True)
            del files[file_uid]
            save_db(FILES_DB, files)
            await callback.answer("🗑 File deleted!", show_alert=True)
            await callback.message.edit(
                f"🗑 **File Deleted**\n\n"
                f"📁 `{file_data.get('file_name','Unknown')}`"
            )

        elif data.startswith("get_file_"):
            file_uid  = data[len("get_file_"):]
            files     = load_db(FILES_DB)
            file_data = files.get(file_uid)
            if not file_data:
                return await callback.answer("❌ File not found!", show_alert=True)
            await callback.answer("📤 Sending file...")
            try:
                sent = await deliver_file(client, callback.message.chat.id, file_data)
                bi = get_bot_info(bot_id)
                ud = get_user(uid, bot_id)
                auto_del = bi.get('auto_delete_time', 600) if bi else 600
                if not (ud and ud.get('is_premium')):
                    asyncio.create_task(_auto_delete(sent, auto_del))
            except Exception as e:
                await callback.message.reply(f"❌ Error: `{e}`")

        elif data == "cancel_edit":
            TEMP_EDIT_DATA.pop(uid, None)
            await callback.message.edit("❌ Edit cancelled.")
            await callback.answer()

        elif data == "my_files_back":
            await callback.message.edit(
                "📋 Use `/listfiles` to browse your files.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Home", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        # ── Standard menu callbacks ──────────────────────────────
        elif data == "start_batch":
            TEMP_BATCH_DATA[uid] = []
            await callback.message.edit(
                "📦 **Batch Mode Active**\n\nSend files. `/done` when finished.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_batch")]
                ])
            )
            await callback.answer("Batch started!")

        elif data == "cancel_batch":
            TEMP_BATCH_DATA.pop(uid, None)
            await callback.message.edit("❌ Batch cancelled!")
            await callback.answer()

        elif data == "clone_menu":
            ubts = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == uid]
            await callback.message.edit(
                f"🤖 **Clone Bot**\n\nYour bots: `{len(ubts)}`\n\n"
                f"1. @BotFather → /newbot\n2. Copy token\n3. `/clone TOKEN`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 BotFather", url="https://t.me/BotFather")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "user_dashboard":
            ud   = get_user(uid, bot_id)
            ubts = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == uid]
            await callback.message.edit(
                f"📊 **Dashboard**\n\n"
                f"📁 Uploaded: `{ud.get('files_uploaded',0) if ud else 0}`\n"
                f"📦 Batches: `{ud.get('batches_created',0) if ud else 0}`\n"
                f"🤖 Bots: `{len(ubts)}`\n"
                f"💰 Points: `{ud.get('points',0) if ud else 0}`\n"
                f"💎 Premium: `{'Yes ✅' if ud and ud.get('is_premium') else 'No'}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 My Bots", callback_data="my_bots_menu"),
                     InlineKeyboardButton("📋 My Files", callback_data="my_files_back")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "my_bots_menu":
            ubts = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == uid]
            text = f"🤖 **Your Bots ({len(ubts)})**\n\n"
            if ubts:
                for i, b in enumerate(ubts[:10], 1):
                    st = "🟢" if b['bot_id'] in ACTIVE_CLIENTS else "🔴"
                    text += f"{i}. {st} @{b['bot_username']}\n"
            else:
                text += "No bots yet!"
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Clone More", callback_data="clone_menu")],
                    [InlineKeyboardButton("🔙 Back", callback_data="user_dashboard")]
                ])
            )
            await callback.answer()

        elif data == "bot_settings":
            bi = get_bot_info(bot_id)
            if bi:
                timer = bi.get('auto_delete_time', 600)
                await callback.message.edit(
                    f"⚙️ **Settings**\n\n🤖 @{client.me.username}\n"
                    f"📢 Force Sub: `{len(bi.get('force_subs',[]))}` channels\n"
                    f"⏱ Auto-Delete: `{timer}s` ({timer//60}min)\n"
                    f"🖼 Welcome Image: `{'Set' if bi.get('welcome_image') else 'None'}`\n"
                    f"🔗 Shortener: `{'ON' if bi.get('is_shortener_enabled') else 'OFF'}`",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                    ])
                )
            await callback.answer()

        elif data == "help_menu":
            await callback.message.edit(
                "ℹ️ **Help Guide**\n\n"
                "• Send file → link | `/batch` → multi-file link\n"
                "• `/editfile ID` → caption + thumbnail editor\n"
                "• `/clone TOKEN` → create your own bot\n"
                "• Force-sub: pending join request = access ✅\n"
                "• `/refer` → earn points → premium",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "referral_menu":
            ud   = get_user(uid, bot_id)
            link = f"https://t.me/{client.me.username}?start=ref_{uid}"
            await callback.message.edit(
                f"🎁 **Referral**\n\n"
                f"👥 Referrals: `{ud.get('referrals',0) if ud else 0}`\n"
                f"💰 Points: `{ud.get('points',0) if ud else 0}`\n\n"
                f"Earn 10 pts per referral!\n\n`{link}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={link}")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "premium_menu":
            ud = get_user(uid, bot_id)
            status = "💎 Active" if ud and ud.get("is_premium") else "🆓 Free"
            await callback.message.edit(
                f"💎 **Premium**\n\nStatus: **{status}**\n\n"
                f"Benefits:\n• 🚀 No auto-delete\n• 🎯 Priority delivery\n• 📂 Unlimited batch\n\n"
                f"Cost: 500 points → `/buy_premium`\nContact @{get_main_bot_username()}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()

        elif data == "admin_panel":
            bi = get_bot_info(bot_id)
            if not (is_admin(uid) or (bi and bi.get('owner_id') == uid)):
                return await callback.answer("❌ No access!", show_alert=True)
            await callback.message.edit("⚡ **Admin Panel**", reply_markup=get_admin_panel_keyboard())
            await callback.answer()

        elif data == "broadcast_menu":
            bi = get_bot_info(bot_id)
            if not (is_admin(uid) or uid == MAIN_ADMIN or (bi and bi.get('owner_id') == uid)):
                return await callback.answer("❌ No access!", show_alert=True)
            await callback.message.edit(
                f"📢 **Broadcast**\n\n👥 Users: `{len(get_all_users(bot_id))}`\n\nReply to a message with `/broadcast`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
            await callback.answer()

        elif data == "admin_stats":
            bot_files  = [f for f in load_db(FILES_DB).values() if f.get('bot_id') == bot_id]
            total_view = sum(f.get('access_count', 0) for f in bot_files)
            thumbs_set = sum(1 for f in bot_files if f.get('custom_thumbnail'))
            await callback.message.edit(
                f"📊 **Bot Stats**\n\n"
                f"👥 Users: `{len(get_all_users(bot_id))}`\n"
                f"📁 Files: `{len(bot_files)}`\n"
                f"👁 Total Views: `{total_view}`\n"
                f"🖼 Custom Thumbs: `{thumbs_set}`\n"
                f"⏳ Uptime: `{str(datetime.now() - START_TIME).split('.')[0]}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "manage_users":
            all_u  = load_db(USERS_DB)
            banned = sum(1 for u in all_u.values() if u.get('bot_id') == bot_id and u.get('is_banned'))
            await callback.message.edit(
                f"👥 **User Management**\n\n"
                f"🟢 Active: `{len(get_all_users(bot_id))}`\n🚫 Banned: `{banned}`\n\n"
                f"• `/ban ID` `/unban ID` `/info ID`\n• `/setpremium ID` `/addpoints ID AMT`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
            await callback.answer()

        elif data == "my_bots_admin":
            ubts = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == uid]
            text = f"🤖 **Your Bots ({len(ubts)})**\n\n"
            for i, b in enumerate(ubts[:15], 1):
                st = "🟢" if b['bot_id'] in ACTIVE_CLIENTS else "🔴"
                text += f"{i}. {st} @{b['bot_username']}\n"
            if not ubts: text += "None yet!"
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Clone", callback_data="clone_menu")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "bot_settings_admin":
            bi = get_bot_info(bot_id)
            if not bi:
                return await callback.answer("Bot info not found!", show_alert=True)
            timer = bi.get('auto_delete_time', 600)
            await callback.message.edit(
                f"⚙️ **Bot Settings**\n\n"
                f"💬 Welcome: `{'Set' if bi.get('custom_welcome') else 'Default'}`\n"
                f"🖼 Welcome Img: `{'Set' if bi.get('welcome_image') else 'None'}`\n"
                f"⏱ Auto-Delete: `{timer}s` ({timer//60}min)\n"
                f"✅ Auto-Approve: `{'ON' if bi.get('auto_approve') else 'OFF'}`\n"
                f"📝 Log Channel: `{bi.get('log_channel') or 'None'}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 Welcome Msg", callback_data="set_welcome_msg"),
                     InlineKeyboardButton("⏱ Timer", callback_data="set_delete_timer")],
                    [InlineKeyboardButton("📝 Log Channel", callback_data="set_log_info")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()

        elif data == "set_welcome_msg":
            await callback.message.edit(
                "💬 Reply to text with `/setmsg`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bot_settings_admin")]])
            )
            await callback.answer()

        elif data == "set_log_info":
            await callback.message.edit(
                "📝 `/setlog CHANNEL_ID` or `/setlog off`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bot_settings_admin")]])
            )
            await callback.answer()

        elif data == "set_delete_timer":
            bi = get_bot_info(bot_id)
            curr = bi.get('auto_delete_time', 600) if bi else 600
            await callback.message.edit(
                f"⏱ Current: `{curr}s` ({curr//60}min)\n\n`/settimer SECONDS`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bot_settings_admin")]])
            )
            await callback.answer()

        elif data == "forcesub_admin":
            bi = get_bot_info(bot_id)
            if not bi:
                return await callback.answer("Bot info not found!", show_alert=True)
            fs   = bi.get("force_subs", [])
            text = f"🔒 **Force Subscribe** ({len(fs)}/{MAX_FORCE_SUB_CHANNELS})\n\n"
            if not fs:
                text += "None configured.\n"
            else:
                for i, f in enumerate(fs, 1):
                    cid  = f['channel_id'] if isinstance(f, dict) else f
                    lnk  = (f.get('invite_link') if isinstance(f, dict) else None) or 'Auto'
                    text += f"{i}. `{cid}` — {lnk}\n"
            text += "\n🆕 **Pending requests also get access!**\nManage via `/setfs`."
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
            await callback.answer()

        elif data == "toggle_auto_approve":
            bi = get_bot_info(bot_id)
            if not bi:
                return await callback.answer("Bot info not found!", show_alert=True)
            curr = bi.get("auto_approve", False)
            update_bot_info(bot_id, "auto_approve", not curr)
            await callback.answer(
                f"Auto-Approve: {'ENABLED ✅' if not curr else 'DISABLED ❌'}",
                show_alert=True
            )
            await callback.message.edit("⚡ **Admin Panel**", reply_markup=get_admin_panel_keyboard())

        elif data == "edit_timer":
            bi   = get_bot_info(bot_id)
            curr = bi.get('auto_delete_time', 600) if bi else 600
            await callback.message.edit(
                f"⏱ Auto-Delete Timer: `{curr}s` ({curr//60}min)\n\n`/settimer SECONDS` (min 60)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
            await callback.answer()

        elif data == "set_welcome_img":
            await callback.message.edit(
                "🖼 Reply to a photo with `/setwelcomeimg`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
            await callback.answer()

        elif data == "shortener_admin":
            bi = get_bot_info(bot_id)
            if not bi:
                return await callback.answer("Bot info not found!", show_alert=True)
            status = "✅ Enabled" if bi.get("is_shortener_enabled") else "❌ Disabled"
            await callback.message.edit(
                f"🔗 **Shortener**\n\nStatus: {status}\nURL: `{bi.get('shortener_url') or 'Not set'}`\n\n`/shortener` to manage.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
            await callback.answer()

        elif data == "supreme_panel":
            if uid != MAIN_ADMIN:
                return await callback.answer("❌ Supreme only!", show_alert=True)
            await callback.message.edit("👑 **Supreme Panel**", reply_markup=get_supreme_panel_keyboard())
            await callback.answer()

        elif data == "global_broadcast":
            if uid != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            await callback.message.edit(
                f"🌍 **Global Broadcast**\n\n👥 `{len(get_all_users())}`\n🤖 `{len(ACTIVE_CLIENTS)}`\n\nReply to message with `/broadcast`.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]])
            )
            await callback.answer()

        elif data == "system_stats":
            if uid != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            total, used, free = shutil.disk_usage("/")
            pending_total = sum(len(u) for u in PENDING_JOIN_REQUESTS.values())
            await callback.message.edit(
                f"🖥 **System Status**\n━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 Total Bots: `{len(get_all_bots())}`\n"
                f"🟢 Online: `{len(ACTIVE_CLIENTS)}`\n"
                f"👥 Users: `{len(load_db(USERS_DB))}`\n"
                f"📁 Files: `{len(load_db(FILES_DB))}`\n"
                f"⏳ Pending Join Req: `{pending_total}`\n"
                f"💾 Disk: `{used//(2**30)}GB / {total//(2**30)}GB`\n"
                f"🆓 Free: `{free//(2**30)}GB`\n"
                f"⏱ Uptime: `{str(datetime.now() - START_TIME).split('.')[0]}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n✅ All Systems OK",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="system_stats")],
                    [InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]
                ])
            )
            await callback.answer()

        elif data == "all_bots_list":
            if uid != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            ab   = get_all_bots()
            text = f"🤖 **All Bots ({len(ab)})**\n\n"
            for i, (k, b) in enumerate(list(ab.items())[:20], 1):
                if isinstance(b, dict):
                    st = "🟢" if int(k) in ACTIVE_CLIENTS else "🔴"
                    text += f"{i}. {st} @{b['bot_username']} — {b.get('owner_name','?')}\n"
            if len(ab) > 20:
                text += f"\n...and {len(ab)-20} more"
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]])
            )
            await callback.answer()

        elif data == "manage_admins":
            if uid != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            admins = load_db(ADMINS_DB)
            text   = f"👑 **Admin Management**\n\n🌟 Main: `{MAIN_ADMIN}`\n👥 Secondary ({len(admins)}):\n"
            for aid in admins.keys():
                text += f"  • `{aid}`\n"
            text += "\n`/addadmin ID` `/deladmin ID`"
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]])
            )
            await callback.answer()

        elif data == "toggle_maintenance":
            if uid != MAIN_ADMIN:
                return await callback.answer("❌ Access denied!", show_alert=True)
            curr = get_global_config().get("maintenance", False)
            update_global_config("maintenance", not curr)
            await callback.answer(f"Maintenance: {'ON ⚠️' if not curr else 'OFF ✅'}", show_alert=True)
            await callback.message.edit("👑 **Supreme Panel**", reply_markup=get_supreme_panel_keyboard())

        elif data == "global_msg_set":
            if uid != MAIN_ADMIN: return await callback.answer()
            await callback.message.edit(
                "📢 Use `/setglobal MESSAGE` or `/setglobal off`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]])
            )
            await callback.answer()

        elif data == "manual_backup":
            if uid != MAIN_ADMIN: return await callback.answer()
            await callback.answer("⏳ Backing up...", show_alert=True)
            await backup_db_to_telegram()
            await callback.answer("✅ Backup sent!", show_alert=True)

        elif data == "manual_clean_cache":
            if uid != MAIN_ADMIN: return await callback.answer()
            count = clean_expired_cache()
            await callback.answer(f"🧹 Cleaned {count} entries!", show_alert=True)

        elif data == "restart_all_bots":
            if uid != MAIN_ADMIN: return await callback.answer()
            await callback.answer("🔄 Restarting...", show_alert=True)
            os.execl(sys.executable, sys.executable, *sys.argv)

        elif data == "confirm_broadcast":
            bd = TEMP_BROADCAST_DATA.get(uid)
            if not bd:
                return await callback.answer("❌ Session expired!", show_alert=True)
            sm = await callback.message.edit("📢 Broadcasting...")
            s, f = await broadcast_message(bd["message"], bd["bot_ids"], status_msg=sm)
            TEMP_BROADCAST_DATA.pop(uid, None)
            await sm.edit(f"✅ **Done!**\n\n✅ `{s}` ❌ `{f}` 🤖 `{len(bd['bot_ids'])}`")

        elif data == "cancel_broadcast":
            TEMP_BROADCAST_DATA.pop(uid, None)
            await callback.message.edit("❌ Broadcast cancelled!")
            await callback.answer()

        elif data == "back_to_start":
            bi   = get_bot_info(bot_id)
            msg  = (bi.get('custom_welcome') if bi else None) or (
                f"✨ **Welcome Back!**\n🤖 @{client.me.username}"
            )
            img  = bi.get('welcome_image') if bi else None
            kbd  = get_start_keyboard(bot_id, uid)
            try:
                if img:
                    await callback.message.delete()
                    await client.send_photo(callback.message.chat.id, img, caption=msg, reply_markup=kbd)
                else:
                    await callback.message.edit(msg, reply_markup=kbd)
            except Exception:
                await callback.message.edit(f"👋 **Welcome Back!**\n🤖 @{client.me.username}", reply_markup=kbd)
            await callback.answer()

        else:
            await callback.answer()


# ═══════════════════════════════════════════════════════════════
# 🔧 HELPERS
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
        await asyncio.sleep(600)
        try:
            USER_FLOOD.clear()
            count = clean_expired_cache()
            if count:
                logger.info(f"🗑 Cleaned {count} cache entries")
            await backup_db_to_telegram()
            logger.info("💾 DB backup done")
            # Also clean stale pending requests in memory
            now = datetime.now()
            for cid in list(PENDING_JOIN_REQUESTS.keys()):
                for uid in list(PENDING_JOIN_REQUESTS[cid].keys()):
                    try:
                        ts = datetime.fromisoformat(PENDING_JOIN_REQUESTS[cid][uid])
                        if (now - ts).days > PENDING_REQUEST_TTL_DAYS:
                            del PENDING_JOIN_REQUESTS[cid][uid]
                    except Exception:
                        del PENDING_JOIN_REQUESTS[cid][uid]
                if not PENDING_JOIN_REQUESTS[cid]:
                    del PENDING_JOIN_REQUESTS[cid]
        except Exception as e:
            logger.error(f"Background task error: {e}")

# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║  🚀 ULTRA FILESTORE BOT v3.0 — COMPLETE & ADVANCED  ║")
    print("╚══════════════════════════════════════════════════════╝")

    if DB_CHANNEL == -1000000000000:
        logger.error("❌ DB_CHANNEL not configured!")
        return

    # Load persisted pending requests into memory
    _load_pending_requests()
    logger.info(f"📋 Loaded pending join requests for {len(PENDING_JOIN_REQUESTS)} channels")

    # Start main bot
    logger.info("🔥 Starting Main Bot...")
    main_app = await start_bot(MAIN_BOT_TOKEN)
    if not main_app:
        logger.error("❌ Main bot failed! Check token.")
        return

    # Start clone bots
    all_bots = get_all_bots()
    if all_bots:
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
    print("║          ✅ ALL SYSTEMS OPERATIONAL v3.0 ✅          ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"👑 Admin  : {MAIN_ADMIN}")
    print(f"🤖 Bots   : {len(ACTIVE_CLIENTS)}")
    print(f"📅 Started: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("⏳ Running... Ctrl+C to stop.")

    asyncio.create_task(background_tasks())
    await idle()

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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    except Exception as e:
        logger.error(f"❌ Fatal: {e}")
        raise
