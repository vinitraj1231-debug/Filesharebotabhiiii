"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 ULTRA ADVANCED MULTI-LEVEL FILESTORE BOT - COMPLETE & FIXED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL FEATURES WORKING
✅ VIDEO CAPTION PRESERVED
✅ CLONE SYSTEM & BATCHING
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
import aiohttp
from datetime import datetime, timedelta
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired
from pyrogram.enums import ChatMemberStatus, ParseMode

# ═══════════════════════════════════════════════════════════════
# 🔧 CONFIGURATION (अपनी डिटेल्स यहाँ डालें)
# ═══════════════════════════════════════════════════════════════

API_ID = 23790796  # अपना API ID यहाँ डालें
API_HASH = "626eb31c9057007df4c2851b3074f27f"  # अपना API HASH यहाँ डालें
MAIN_BOT_TOKEN = "8607033631:AAEEHymSzeLeP8wpH1TR4vnZSyai3kI1DTE"  # अपना Main Bot Token यहाँ डालें
MAIN_ADMIN = 8756786934  # अपनी Telegram User ID यहाँ डालें (e.g., 12345678)
DB_CHANNEL = -1003982754680  # अपना Database Channel ID यहाँ डालें (Must be Admin)

FILE_CACHE_DURATION = 60 * 60  # 60 minutes cache

# Database Paths
DB_FOLDER = "database"
FILES_DB = f"{DB_FOLDER}/files.json"
BATCH_DB = f"{DB_FOLDER}/batches.json"
BOTS_DB = f"{DB_FOLDER}/bots.json"
USERS_DB = f"{DB_FOLDER}/users.json"
ADMINS_DB = f"{DB_FOLDER}/admins.json"
FILE_CACHE_DB = f"{DB_FOLDER}/file_cache.json"
CONFIG_DB = f"{DB_FOLDER}/config.json"

GLOBAL_CONFIG_CACHE = {}

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
]

# ═══════════════════════════════════════════════════════════════
# 📝 LOGGING
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FileStore")

# ═══════════════════════════════════════════════════════════════
# 💾 DATABASE FUNCTIONS (WITH CACHING)
# ═══════════════════════════════════════════════════════════════

os.makedirs(DB_FOLDER, exist_ok=True)
DB_CACHE = {}

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
    except:
        return {}

def save_db(filename, data):
    DB_CACHE[filename] = data
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

async def backup_db_to_telegram():
    """Backs up all JSON database files to the DB_CHANNEL."""
    # Find main bot client
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
                    caption=f"📂 **Database Backup**\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n📄 File: `{file}`"
                )
    except Exception as e:
        logger.error(f"Backup failed: {e}")

def add_user(user_id, bot_id, username=None, name=None, referred_by=None):
    users = load_db(USERS_DB)
    user_key = f"{bot_id}_{user_id}"
    if user_key not in users:
        users[user_key] = {
            "user_id": user_id, "bot_id": bot_id, "username": username, "name": name,
            "join_date": str(datetime.now()), "is_banned": False,
            "files_uploaded": 0, "batches_created": 0, "bots_cloned": 0,
 advanced-filestore-bot-upgrade-16475289135707005334
            "referred_by": referred_by, "referrals": 0, "is_premium": False
        }
        save_db(USERS_DB, users)
        if referred_by:
            update_user_stats(referred_by, bot_id, "referrals")

            "referred_by": referred_by, "referrals": 0, "points": 0, "is_premium": False
        }
        save_db(USERS_DB, users)
        if referred_by:
            ref_key = f"{bot_id}_{referred_by}"
            if ref_key in users:
                users[ref_key]["referrals"] = users[ref_key].get("referrals", 0) + 1
                users[ref_key]["points"] = users[ref_key].get("points", 0) + 10 # 10 points per referral
                save_db(USERS_DB, users)
 main
    return users[user_key]

def get_user(user_id, bot_id):
    users = load_db(USERS_DB)
    return users.get(f"{bot_id}_{user_id}")

def update_user_stats(user_id, bot_id, field):
    users = load_db(USERS_DB)
    user_key = f"{bot_id}_{user_id}"
    if user_key in users:
        users[user_key][field] = users[user_key].get(field, 0) + 1
        save_db(USERS_DB, users)

def is_user_banned(user_id, bot_id):
    # Global Ban Check
    config = get_global_config()
    global_bans = config.get("global_bans", [])
    if user_id in global_bans:
        return True

    user = get_user(user_id, bot_id)
    return user.get("is_banned", False) if user else False

def ban_user(user_id, bot_id):
    users = load_db(USERS_DB)
    user_key = f"{bot_id}_{user_id}"
    if user_key in users:
        users[user_key]["is_banned"] = True
        save_db(USERS_DB, users)
        return True
    return False

def unban_user(user_id, bot_id):
    users = load_db(USERS_DB)
    user_key = f"{bot_id}_{user_id}"
    if user_key in users:
        users[user_key]["is_banned"] = False
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

def save_bot_info(token, bot_id, bot_username, owner_id, owner_name, parent_bot_id=None):
    bots = load_db(BOTS_DB)
    bots[str(bot_id)] = {
        "token": token, "bot_id": bot_id, "bot_username": bot_username,
        "owner_id": owner_id, "owner_name": owner_name, "parent_bot_id": parent_bot_id,
 advanced-filestore-bot-upgrade-16475289135707005334
        "created_on": str(datetime.now()), "force_subs": [], "is_active": True,
        "custom_welcome": None, "auto_delete_timer": 600

        "created_on": str(datetime.now()), "force_sub": None, "fs_link": None, "is_active": True,
        "custom_welcome": None,
        "welcome_image": None,
        "auto_delete_time": 600,
        "auto_approve": False,
        "force_subs": [], # Support for multiple channels
        "shortener_api": None,
        "shortener_url": None,
        "is_shortener_enabled": False,
        "log_channel": None
 main
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
    all_descendants = []
    def recurse(bot_id):
        for child in get_child_bots(bot_id):
            all_descendants.append(child)
            recurse(child['bot_id'])
    recurse(parent_bot_id)
    return all_descendants

 advanced-filestore-bot-upgrade-16475289135707005334
def cascade_force_subs(parent_bot_id, force_subs):

def cascade_force_sub(parent_bot_id, force_subs):
 main
    descendants = get_all_descendant_bots(parent_bot_id)
    bots = load_db(BOTS_DB)
    count = 0
    for bot in descendants:
 advanced-filestore-bot-upgrade-16475289135707005334
        if str(bot['bot_id']) in bots:
            bots[str(bot['bot_id'])]['force_subs'] = force_subs

        bot_id_str = str(bot['bot_id'])
        if bot_id_str in bots:
            bots[bot_id_str]['force_subs'] = force_subs
 main
            count += 1
    save_db(BOTS_DB, bots)
    return count

def add_to_cache(file_id, message_id, chat_id, bot_id, caption=None):
    cache = load_db(FILE_CACHE_DB)
    cache[file_id] = {
        "message_id": message_id, "chat_id": chat_id, "bot_id": bot_id,
        "caption": caption, "cached_at": datetime.now().isoformat(),
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
    except:
        return None

def clean_expired_cache():
    cache = load_db(FILE_CACHE_DB)
    expired = [k for k, v in cache.items() if datetime.now() > datetime.fromisoformat(v.get('expires_at', '2000-01-01'))]
    for k in expired:
        del cache[k]
    if expired:
        save_db(FILE_CACHE_DB, cache)
    return len(expired)

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

async def get_short_link(bot_info, link):
    if not bot_info.get("is_shortener_enabled") or not bot_info.get("shortener_api") or not bot_info.get("shortener_url"):
        return link

    api_url = f"https://{bot_info['shortener_url']}/api?api={bot_info['shortener_api']}&url={link}"
    try:
        session = await get_http_session()
        async with session.get(api_url) as response:
            data = await response.json()
            if data.get("status") == "success":
                return data.get("shortenedUrl")
    except Exception as e:
        logger.error(f"Shortener error: {e}")

    return link

def get_unique_id():
    return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:12]

# ═══════════════════════════════════════════════════════════════
# 🤖 BOT MANAGEMENT
# ═══════════════════════════════════════════════════════════════

START_TIME = datetime.now()
ACTIVE_CLIENTS = {}
TEMP_BATCH_DATA = {}
TEMP_BROADCAST_DATA = {}
USER_FLOOD = {}
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
        logger.error(f"Commands error for {app.name}: {e}")

async def start_bot(token, parent_bot_id=None):
    try:
        # Client Setup
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
        
        ACTIVE_CLIENTS[me.id] = {
            "app": app, "username": me.username, "is_main": token == MAIN_BOT_TOKEN,
            "token": token, "parent_bot_id": parent_bot_id, "started_at": datetime.now()
        }
        
        register_handlers(app)
        logger.info(f"✅ {'MAIN' if token == MAIN_BOT_TOKEN else 'CHILD'}: @{me.username}")
        return app
    except Exception as e:
        logger.error(f"Bot start failed for token {token[:10]}... : {e}")
        return None

async def check_force_sub(client, user_id):
    bot_info = get_bot_info(client.me.id)
 advanced-filestore-bot-upgrade-16475289135707005334
    if not bot_info or not bot_info.get("force_subs"):
        return True, []
    
    must_join = []
    for channel_id in bot_info["force_subs"]:
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                must_join.append(channel_id)
        except UserNotParticipant:
            must_join.append(channel_id)
        except Exception:
            # Skip if bot is not admin in that channel
            continue

    if not must_join:
        return True, []

    links = []
    for c_id in must_join:
        try:
            chat = await client.get_chat(c_id)
            link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
            if link:
                links.append({"title": chat.title, "link": link})
        except:
            continue

    return (False, links) if links else (True, [])

    if not bot_info:
        return True, None
    
    # New Multi-FS logic
    force_subs = bot_info.get("force_subs", [])

    # Backward compatibility
    if not force_subs and bot_info.get("force_sub"):
        force_subs = [{"channel_id": bot_info["force_sub"], "invite_link": bot_info.get("fs_link")}]

    if not force_subs:
        return True, None

    must_join = []
    for fs in force_subs:
        channel_id = fs["channel_id"]
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                must_join.append(fs)
        except UserNotParticipant:
            must_join.append(fs)
        except Exception:
            continue

    if not must_join:
        return True, None

    # Return the first channel they need to join
    fs = must_join[0]
    link = fs.get("invite_link")
    if not link:
        try:
            chat = await client.get_chat(fs["channel_id"])
            link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
        except:
            link = None

    return False, link
 main

async def broadcast_message(original_msg, bot_ids=None, status_msg=None):
    if bot_ids is None:
        bot_ids = list(ACTIVE_CLIENTS.keys())
    
    total_bots = len(bot_ids)
    success, failed = 0, 0
 advanced-filestore-bot-upgrade-16475289135707005334
    total_bots = len(bot_ids)

    for b_idx, bot_id in enumerate(bot_ids, 1):
        if bot_id not in ACTIVE_CLIENTS:
            continue

        client_data = ACTIVE_CLIENTS[bot_id]
        app = client_data["app"]
        users = get_all_users(bot_id)
        total_users = len(users)

        for u_idx, user in enumerate(users, 1):
            try:
                # Advanced Copy logic (handles all media types + buttons)

    start_time = datetime.now()

    for i, bot_id in enumerate(bot_ids, 1):
        if bot_id not in ACTIVE_CLIENTS:
            continue
        app = ACTIVE_CLIENTS[bot_id]["app"]
        users = get_all_users(bot_id)

        for j, user in enumerate(users, 1):
            try:
 main
                await original_msg.copy(user['user_id'])
                success += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await original_msg.copy(user['user_id'])
                success += 1
 advanced-filestore-bot-upgrade-16475289135707005334
            except:
                failed += 1

            # Real-time progress tracking
            if status_msg and (success + failed) % 10 == 0:
                try:
                    progress = f"📢 **Broadcast Progress**\n\n" \
                               f"🤖 Bot: {b_idx}/{total_bots} (@{client_data['username']})\n" \
                               f"👥 Users: {u_idx}/{total_users}\n" \
                               f"━━━━━━━━━━━━━━━━━━━━\n" \
                               f"✅ Success: `{success}`\n" \
                               f"❌ Failed: `{failed}`\n" \
                               f"📊 Total: `{success + failed}`"
                    await status_msg.edit(progress)
                except:
                    pass
            await asyncio.sleep(0.05) # Flood prevention

            except Exception:
                failed += 1

            # Update status occasionally
            if (success + failed) % 20 == 0 and status_msg:
                try:
                    elapsed = (datetime.now() - start_time).seconds
                    await status_msg.edit(
                        f"📢 **Broadcast Progress**\n\n"
                        f"🤖 Bot: {i}/{total_bots} (@{ACTIVE_CLIENTS[bot_id]['username']})\n"
                        f"👥 Users: {j}/{len(users)}\n\n"
                        f"✅ Success: `{success}`\n"
                        f"❌ Failed: `{failed}`\n"
                        f"⏳ Time: `{elapsed}s`"
                    )
                except:
                    pass
            await asyncio.sleep(0.05)
 main

    return success, failed

# ═══════════════════════════════════════════════════════════════
# 🎨 UI KEYBOARDS
# ═══════════════════════════════════════════════════════════════

def get_start_keyboard(bot_id, user_id):
    buttons = []
    bot_info = get_bot_info(bot_id)
    is_owner = bot_info and bot_info['owner_id'] == user_id
    
    if user_id == MAIN_ADMIN:
        buttons.append([InlineKeyboardButton("👑 SUPREME PANEL 👑", callback_data="supreme_panel")])
    if is_admin(user_id) or is_owner:
        buttons.append([InlineKeyboardButton("⚡ ADMIN PANEL ⚡", callback_data="admin_panel")])
    
    buttons.extend([
 advanced-filestore-bot-upgrade-16475289135707005334
        [InlineKeyboardButton("📦 Batch", callback_data="start_batch"), InlineKeyboardButton("🤖 Clone", callback_data="clone_menu")],
        [InlineKeyboardButton("📊 Dashboard", callback_data="user_dashboard"), InlineKeyboardButton("🎁 Referral", callback_data="referral_menu")],
        [InlineKeyboardButton("🎯 My Bots", callback_data="my_bots_menu"), InlineKeyboardButton("⚙️ Settings", callback_data="bot_settings")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium_menu"), InlineKeyboardButton("ℹ️ Help", callback_data="help_menu")]

        [InlineKeyboardButton("📦 CREATE BATCH", callback_data="start_batch"), InlineKeyboardButton("🤖 CLONE BOT", callback_data="clone_menu")],
        [InlineKeyboardButton("📊 DASHBOARD", callback_data="user_dashboard"), InlineKeyboardButton("🎯 MY BOTS", callback_data="my_bots_menu")],
        [InlineKeyboardButton("⚙️ SETTINGS", callback_data="bot_settings"), InlineKeyboardButton("ℹ️ HELP & INFO", callback_data="help_menu")]
 main
    ])
    return InlineKeyboardMarkup(buttons)

def get_admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 BROADCAST", callback_data="broadcast_menu"), InlineKeyboardButton("📊 BOT STATS", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 MANAGE USERS", callback_data="manage_users"), InlineKeyboardButton("🤖 CLONED BOTS", callback_data="my_bots_admin")],
        [InlineKeyboardButton("⚙️ BOT SETTINGS", callback_data="bot_settings_admin"), InlineKeyboardButton("🔒 FORCE SUB", callback_data="forcesub_admin")],
        [InlineKeyboardButton("🔗 SHORTENER", callback_data="shortener_admin"), InlineKeyboardButton("⏱ DELETE TIMER", callback_data="edit_timer")],
        [InlineKeyboardButton("🖼 WELCOME IMG", callback_data="set_welcome_img"), InlineKeyboardButton("✅ AUTO APPROVE", callback_data="toggle_auto_approve")],
        [InlineKeyboardButton("🔙 BACK TO HOME", callback_data="back_to_start")]
    ])

def get_supreme_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 GLOBAL BROADCAST", callback_data="global_broadcast"), InlineKeyboardButton("📊 SYSTEM STATS", callback_data="system_stats")],
        [InlineKeyboardButton("🤖 MANAGE ALL BOTS", callback_data="all_bots_list"), InlineKeyboardButton("👑 MANAGE ADMINS", callback_data="manage_admins")],
        [InlineKeyboardButton("🛠 MAINTENANCE", callback_data="toggle_maintenance"), InlineKeyboardButton("📢 GLOBAL MSG", callback_data="global_msg_set")],
        [InlineKeyboardButton("💾 BACKUP DB", callback_data="manual_backup"), InlineKeyboardButton("🧹 CLEAN CACHE", callback_data="manual_clean_cache")],
        [InlineKeyboardButton("🔄 RESTART ALL BOTS", callback_data="restart_all_bots")],
        [InlineKeyboardButton("🔙 BACK TO HOME", callback_data="back_to_start")]
    ])

# ═══════════════════════════════════════════════════════════════
# 📝 HANDLERS
# ═══════════════════════════════════════════════════════════════

def register_handlers(app: Client):

    @app.on_chat_join_request()
    async def join_request_handler(client, request):
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        if bot_info and bot_info.get("auto_approve"):
            try:
                await client.approve_chat_join_request(request.chat.id, request.from_user.id)
                logger.info(f"✅ Approved {request.from_user.id} in {request.chat.id}")
            except Exception as e:
                logger.error(f"Failed to approve join request: {e}")
    
    @app.on_message(filters.private)
    async def flood_control_handler(client, message):
        user_id = message.from_user.id
        now = datetime.now()

        if user_id not in USER_FLOOD:
            USER_FLOOD[user_id] = [now]
        else:
            USER_FLOOD[user_id].append(now)
            # Keep only last 5 messages within last 5 seconds
            USER_FLOOD[user_id] = [t for t in USER_FLOOD[user_id] if (now - t).total_seconds() < 5]

            if len(USER_FLOOD[user_id]) > 5:
                await message.reply("⚠️ **Anti-Flood Triggered!** Please slow down.")
                message.stop_propagation()

    @app.on_message(filters.command("start") & filters.private)
    async def start_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        
        # Check Maintenance
        config = get_global_config()
        if config.get("maintenance") and user_id != MAIN_ADMIN:
            return await message.reply("🚧 **Bot is under maintenance!**\n\nPlease try again later.")

        if is_user_banned(user_id, bot_id):
            return await message.reply("🚫 You are banned!")
        
 advanced-filestore-bot-upgrade-16475289135707005334

        # Handle referral
 main
        referred_by = None
        if len(message.command) > 1 and message.command[1].startswith("ref_"):
            try:
                referred_by = int(message.command[1][4:])
 advanced-filestore-bot-upgrade-16475289135707005334
                if referred_by == user_id: referred_by = None

                if referred_by == user_id: referred_by = None # Can't refer self
 main
            except:
                pass

        add_user(user_id, bot_id, message.from_user.username, message.from_user.first_name, referred_by)
        
        is_subbed, sub_links = await check_force_sub(client, user_id)
        if not is_subbed:
            buttons = []
            for item in sub_links:
                buttons.append([InlineKeyboardButton(f"📢 Join {item['title']}", url=item['link'])])

            buttons.append([InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{client.me.username}?start={message.command[1] if len(message.command)>1 else ''}")])

            return await message.reply(
                "⚠️ **Membership Required!**\n\nYou must join the following channels to use this bot:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        
        # Handle deep links
        bot_info = get_bot_info(bot_id)
        auto_delete_time = bot_info.get("auto_delete_time", 600) if bot_info else 600

        if len(message.command) > 1:
            code = message.command[1]
            
            if code.startswith("f_"):
                unique_id = code[2:]
                files = load_db(FILES_DB)
                file_data = files.get(unique_id)
                
                if file_data:
 advanced-filestore-bot-upgrade-16475289135707005334
                    # Auto-delete Timer logic (High Advance Feature)
                    bot_info = get_bot_info(bot_id)
                    auto_delete_time = bot_info.get("auto_delete_timer", 600)


 main
                    # 1. Try copying from DB Channel (Most Reliable)
                    try:
                        sent_msg = await client.copy_message(
                            chat_id=message.chat.id,
                            from_chat_id=DB_CHANNEL,
                            message_id=file_data['db_msg_id'],
                            caption=file_data.get('caption')
                        )

 advanced-filestore-bot-upgrade-16475289135707005334
                        # Auto-delete task (Premium bypass)
                        user_data = get_user(user_id, bot_id)
                        if user_data and user_data.get("is_premium"):
                            await message.reply("💎 **Premium User Detected!** Auto-delete disabled for you.")
                        else:

                        # Auto-delete task (Skip for premium users)
                        user_data = get_user(user_id, bot_id)
                        if not user_data or not user_data.get("is_premium"):
 main
                            async def delete_after(msg, delay):
                                await asyncio.sleep(delay)
                                try:
                                    await msg.delete()
                                except:
                                    pass

                            asyncio.create_task(delete_after(sent_msg, auto_delete_time))
 advanced-filestore-bot-upgrade-16475289135707005334
                            await message.reply(f"⏳ This file will be deleted automatically in {auto_delete_time//60} minutes for security reasons.")

                            await message.reply(f"⏳ **Security Alert:** This file will be automatically deleted in `{auto_delete_time//60}` minutes. Please save it if needed!")
                        else:
                            await message.reply("🌟 **Premium Feature:** Auto-delete is disabled for you. Enjoy your files permanently!")
 main
                        return
                    except Exception as e:
                        logger.error(f"Copy from DB Channel failed: {e}")

                    # 2. Check Cache
                    cached = get_from_cache(file_data['file_id'])
                    if cached and cached['bot_id'] in ACTIVE_CLIENTS:
                        try:
                            cached_app = ACTIVE_CLIENTS[cached['bot_id']]['app']
                            await cached_app.copy_message(message.chat.id, cached['chat_id'], cached['message_id'], caption=file_data.get('caption'))
                            return
                        except Exception:
                            pass
                    
                    # 3. Last Resort: Reply Cached Media
                    try:
                        sent_msg = await message.reply_cached_media(
                            file_data['file_id'],
                            caption=file_data.get('caption') or f"📁 {file_data['file_name']}"
                        )
                        add_to_cache(file_data['file_id'], sent_msg.id, message.chat.id, bot_id, file_data.get('caption'))
                    except Exception as e:
                        await message.reply(f"❌ File missing or revoked! {e}")
                else:
                    await message.reply("❌ File not found in database.")
                return
            
            elif code.startswith("b_"):
                batch_id = code[2:]
                batches = load_db(BATCH_DB)
                batch_data = batches.get(batch_id)
                
                if batch_data:
                    status = await message.reply(f"📦 Processing batch ({len(batch_data['files'])} files)...")
                    files = load_db(FILES_DB)
                    sent = 0
                    
                    for fid in batch_data['files']:
                        f_data = files.get(fid)
                        if f_data:
                            try:
                                # Try DB Channel first
                                await client.copy_message(
                                    chat_id=message.chat.id,
                                    from_chat_id=DB_CHANNEL,
                                    message_id=f_data['db_msg_id'],
                                    caption=f_data.get('caption')
                                )
                                sent += 1
                            except:
                                # Fallback to cached media
                                try:
                                    sent_msg = await message.reply_cached_media(
                                        f_data['file_id'],
                                        caption=f_data.get('caption') or f"📁 {f_data['file_name']}"
                                    )
                                    sent += 1
                                except:
                                    pass
                            await asyncio.sleep(0.5)
                    
                    await status.delete()
                    await message.reply(f"✅ Delivered {sent}/{len(batch_data['files'])} files!")
                else:
                    await message.reply("❌ Batch not found.")
                return
        
        # Standard Welcome
 advanced-filestore-bot-upgrade-16475289135707005334
        bot_info = get_bot_info(bot_id)
        config = get_global_config()

      
  config = load_db(CONFIG_DB)
 main
        global_msg = config.get("global_msg", "")
        welcome = bot_info.get('custom_welcome') if bot_info else None
        welcome_image = bot_info.get('welcome_image') if bot_info else None
        
        if global_msg:
            await message.reply(f"📢 **SYSTEM ANNOUNCEMENT**\n\n{global_msg}\n\n━━━━━━━━━━━━━━━━━━━━")

        if not welcome:
            greetings = ["Hello", "Hey", "Welcome", "Namaste", "Greetings"]
            welcome = (
                f"✨ **{random.choice(greetings)} {message.from_user.first_name}!**\n\n"
                f"Welcome to the most **Advanced & Secure FileStore System**.\n\n"
                f"🛠 **Premium Features:**\n"
                f" ├ 📂 **Cloud Storage:** Unlimited & Permanent\n"
                f" ├ 📦 **Batch Mode:** Multiple files in one link\n"
                f" ├ 🤖 **Bot Cloning:** Create your copy in seconds\n"
                f" ├ 🔐 **Auto-Destruct:** Files delete for privacy\n"
                f" └ ⚡ **Nitro Speed:** Instant file delivery\n\n"
                f"✨ *Powered by High-End Human-Like Technology*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
        
        if welcome_image:
            try:
                await message.reply_photo(welcome_image, caption=welcome, reply_markup=get_start_keyboard(bot_id, user_id))
            except:
                await message.reply(welcome, reply_markup=get_start_keyboard(bot_id, user_id))
        else:
            await message.reply(welcome, reply_markup=get_start_keyboard(bot_id, user_id))

    @app.on_message(filters.command("admin") & filters.private)
    async def admin_panel_cmd(client, message):
        user_id = message.from_user.id
        bot_info = get_bot_info(client.me.id)
        if not is_admin(user_id) and (not bot_info or bot_info['owner_id'] != user_id):
            return
        await message.reply("⚡ **Admin Panel**", reply_markup=get_admin_panel_keyboard())

    @app.on_message(filters.command("supreme") & filters.private)
    async def supreme_panel_cmd(client, message):
        if message.from_user.id != MAIN_ADMIN:
            return

        # Check if DB_CHANNEL is valid (placeholder check)
        db_status = "🟢 Connected" if DB_CHANNEL != -1000000000000 else "🔴 Not Configured"

        text = (
            f"👑 **Supreme Admin Panel**\n\n"
            f"📊 **Status:** {db_status}\n"
            f"🤖 **Active Bots:** {len(ACTIVE_CLIENTS)}\n"
            f"👥 **Total Users:** {len(load_db(USERS_DB))}\n"
        )
        await message.reply(text, reply_markup=get_supreme_panel_keyboard())

    @app.on_message(filters.command("stats") & filters.private)
    async def stats_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        
        if user_id == MAIN_ADMIN:
            all_bots = get_all_bots()
            users = load_db(USERS_DB)
            files = load_db(FILES_DB)
            stats_text = (
                "🌐 **Global System Analytics**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 **Total Bots:** `{len(all_bots)}` bots\n"
                f"🟢 **Online Now:** `{len(ACTIVE_CLIENTS)}` bots\n"
                f"👥 **Total Users:** `{len(users)}` users\n"
                f"📁 **Total Files:** `{len(files)}` files\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "✨ *Performance: Optimized*"
            )
            await message.reply(stats_text)
        else:
            user_data = get_user(user_id, bot_id)
            user_bots = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == user_id]
            stats_text = (
                "📊 **Personal Growth Dashboard**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📤 **Files Uploaded:** `{user_data.get('files_uploaded', 0) if user_data else 0}`\n"
                f"📦 **Batches Created:** `{user_data.get('batches_created', 0) if user_data else 0}`\n"
                f"🤖 **Bots Cloned:** `{len(user_bots)}` copies\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🌟 *Keep growing with us!*"
            )
            await message.reply(stats_text)

    @app.on_message(filters.command("mybots") & filters.private)
    async def my_bots_cmd(client, message):
        user_id = message.from_user.id
        user_bots = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == user_id]
        
        if not user_bots:
            return await message.reply(
                "🤖 **No Bots Yet!**\n\nUse `/clone` to create!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Clone", callback_data="clone_menu")]])
            )
        
        text = f"🤖 **Your Bots ({len(user_bots)})**\n\n"
        for i, bot in enumerate(user_bots[:10], 1):
            status = "🟢" if bot['bot_id'] in ACTIVE_CLIENTS else "🔴"
            text += f"{i}. {status} @{bot['bot_username']}\n"
        
        await message.reply(text)

    @app.on_message(filters.command(["ban", "unban", "info", "setpremium", "gban", "ungban"]) & filters.private)
    async def admin_utils_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        
        can_access = user_id == MAIN_ADMIN or (bot_info and bot_info['owner_id'] == user_id) or is_admin(user_id)
        if not can_access:
            return
        
        if len(message.command) < 2:
            return await message.reply(f"Usage: `/{message.command[0]} USER_ID`")
        
        try:
            target = int(message.command[1])
            cmd = message.command[0]

            if cmd == "ban":
                if ban_user(target, bot_id):
                    await message.reply(f"🚫 User `{target}` has been banned.")
                else:
                    await message.reply("❌ User not found.")
            elif cmd == "unban":
                if unban_user(target, bot_id):
                    await message.reply(f"✅ User `{target}` has been unbanned.")
                else:
                    await message.reply("❌ User not found.")
            elif cmd == "setpremium":
                users = load_db(USERS_DB)
                user_key = f"{bot_id}_{target}"
                if user_key in users:
                    users[user_key]["is_premium"] = True
                    save_db(USERS_DB, users)
                    await message.reply(f"💎 User `{target}` is now a **Premium** user!")
                else:
                    await message.reply("❌ User not found.")
            elif cmd == "gban":
                if user_id != MAIN_ADMIN: return
                config = get_global_config()
                gbans = config.get("global_bans", [])
                if target not in gbans:
                    gbans.append(target)
                    update_global_config("global_bans", gbans)
                    await message.reply(f"🌍 **Globally Banned** `{target}`!")
                else:
                    await message.reply("❌ User already globally banned.")
            elif cmd == "ungban":
                if user_id != MAIN_ADMIN: return
                config = get_global_config()
                gbans = config.get("global_bans", [])
                if target in gbans:
                    gbans.remove(target)
                    update_global_config("global_bans", gbans)
                    await message.reply(f"✅ **Globally Unbanned** `{target}`!")
                else:
                    await message.reply("❌ User not in global ban list.")
            elif cmd == "info":
                user = get_user(target, bot_id)
                if not user:
                    return await message.reply("❌ User info not found in database.")

                info = (
                    f"👤 **User Info**\n\n"
                    f"🆔 ID: `{user['user_id']}`\n"
                    f"🏷 Name: {user.get('name', 'Unknown')}\n"
                    f"🔗 Username: @{user.get('username', 'None')}\n"
                    f"📅 Joined: {user.get('join_date', 'N/A')}\n"
                    f"🚫 Banned: {'Yes' if user.get('is_banned') else 'No'}\n"
                    f"💎 Premium: {'Yes' if user.get('is_premium') else 'No'}\n\n"
                    f"📊 **Stats:**\n"
                    f"📤 Uploaded: {user.get('files_uploaded', 0)}\n"
                    f"📦 Batches: {user.get('batches_created', 0)}\n"
                    f"🤖 Clones: {user.get('bots_cloned', 0)}\n"
                    f"🎁 Referrals: {user.get('referrals', 0)}"
                )
                await message.reply(info)
        except ValueError:
            await message.reply("❌ Invalid User ID!")

    @app.on_message(filters.command("settimer") & filters.private)
    async def set_timer_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if not bot_info or (bot_info['owner_id'] != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ No permission!")

        if len(message.command) < 2:
            return await message.reply("Usage: `/settimer SECONDS`")

        try:
            seconds = int(message.command[1])
            if seconds < 0: raise ValueError
            update_bot_info(bot_id, 'auto_delete_timer', seconds)
            await message.reply(f"✅ Auto-delete timer set to `{seconds}` seconds.")
        except:
            await message.reply("❌ Invalid seconds!")

    @app.on_message(filters.command("setmsg") & filters.private)
    async def set_msg_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        
        if not bot_info or (bot_info['owner_id'] != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Only owner!")
        
        if not message.reply_to_message or not message.reply_to_message.text:
            return await message.reply("💬 Reply to message with `/setmsg` to set welcome text.")
        
        update_bot_info(bot_id, 'custom_welcome', message.reply_to_message.text)
        await message.reply("✅ Welcome message updated!")

    @app.on_message(filters.command("settimer") & filters.private)
    async def set_timer_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if not bot_info or (bot_info['owner_id'] != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")

        if len(message.command) < 2:
            return await message.reply("⏱ Usage: `/settimer SECONDS` (e.g., `/settimer 600` for 10 mins)")

        try:
            seconds = int(message.command[1])
            update_bot_info(bot_id, 'auto_delete_time', seconds)
            await message.reply(f"✅ Auto-delete timer set to `{seconds}` seconds.")
        except ValueError:
            await message.reply("❌ Invalid time format!")

    @app.on_message(filters.command("shortener") & filters.private)
    async def set_shortener_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if not bot_info or (bot_info['owner_id'] != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")

        if len(message.command) < 2:
            status = "✅ Enabled" if bot_info.get("is_shortener_enabled") else "❌ Disabled"
            return await message.reply(
                f"🔗 **URL Shortener Settings**\n\n"
                f"Status: {status}\n"
                f"URL: `{bot_info.get('shortener_url', 'Not set')}`\n"
                f"API: `{bot_info.get('shortener_api', 'Not set')}`\n\n"
                f"**Commands:**\n"
                f"• `/shortener on` - Enable\n"
                f"• `/shortener off` - Disable\n"
                f"• `/shortener set URL API` - Set Shortener\n"
                f"Example: `/shortener set shareus.io 1234567890abcdef`"
            )

        cmd = message.command[1].lower()
        if cmd == "on":
            update_bot_info(bot_id, "is_shortener_enabled", True)
            await message.reply("✅ Shortener enabled!")
        elif cmd == "off":
            update_bot_info(bot_id, "is_shortener_enabled", False)
            await message.reply("✅ Shortener disabled!")
        elif cmd == "set":
            if len(message.command) < 4:
                return await message.reply("❌ Usage: `/shortener set URL API`")
            url = message.command[2]
            api = message.command[3]
            update_bot_info(bot_id, "shortener_url", url)
            update_bot_info(bot_id, "shortener_api", api)
            await message.reply(f"✅ Shortener set to `{url}` with API key `{api}`.")

    @app.on_inline_query()
    async def inline_search_handler(client, query):
        bot_id = client.me.id
        q = query.query.lower()
        if not q: return

        files = load_db(FILES_DB)
        results = []

        for uid, f in files.items():
            if f.get('bot_id') == bot_id and q in f.get('file_name', '').lower():
                link = f"https://t.me/{client.me.username}?start=f_{uid}"
                results.append(
                    InlineQueryResultArticle(
                        title=f.get('file_name'),
                        description=f"Size: {format_size(f.get('file_size', 0))}",
                        input_message_content=InputTextMessageContent(
                            f"📁 **File:** `{f.get('file_name')}`\n"
                            f"📊 **Size:** `{format_size(f.get('file_size', 0))}`\n\n"
                            f"🔗 **Link:** {link}"
                        ),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Get File", url=link)]])
                    )
                )
            if len(results) >= 20: break

        await query.answer(results, cache_time=1)

    @app.on_message(filters.command("search") & filters.private)
    async def search_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id

        if is_user_banned(user_id, bot_id):
            return await message.reply("🚫 Banned!")

        if len(message.command) < 2:
            return await message.reply("🔍 Usage: `/search QUERY`")

        query = message.text.split(None, 1)[1].lower()
        files = load_db(FILES_DB)

        results = []
        for uid, f in files.items():
            if f.get('bot_id') == bot_id and query in f.get('file_name', '').lower():
                results.append((uid, f.get('file_name')))

            if len(results) >= 10: break # Limit results

        if not results:
            return await message.reply("❌ No files found!")

        text = "🔍 **Search Results:**\n\n"
        buttons = []
        for uid, name in results:
            link = f"https://t.me/{client.me.username}?start=f_{uid}"
            text += f"• `{name}`\n"
            buttons.append([InlineKeyboardButton(f"📁 {name[:25]}...", url=link)])

        await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))

    @app.on_message(filters.command("setlog") & filters.private)
    async def set_log_channel_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if not bot_info or (bot_info['owner_id'] != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")

        if len(message.command) < 2:
            current = bot_info.get('log_channel', 'Not Set')
            return await message.reply(
                f"📝 **Log Channel Settings**\n\n"
                f"Current Channel: `{current}`\n\n"
                f"Usage: `/setlog CHANNEL_ID` or `/setlog off`"
            )

        if message.command[1].lower() == "off":
            update_bot_info(bot_id, 'log_channel', None)
            return await message.reply("✅ Log channel disabled!")

        try:
            channel_id = int(message.command[1])
            update_bot_info(bot_id, 'log_channel', channel_id)
            await message.reply(f"✅ Log channel set to `{channel_id}`.")
        except ValueError:
            await message.reply("❌ Invalid Channel ID!")

    @app.on_message(filters.command("setwelcomeimg") & filters.private)
    async def set_welcome_img_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if not bot_info or (bot_info['owner_id'] != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Access Denied!")

        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("🖼 Reply to a photo with `/setwelcomeimg` to set it as welcome image.")

        update_bot_info(bot_id, 'welcome_image', message.reply_to_message.photo.file_id)
        await message.reply("✅ Welcome image updated successfully!")

    @app.on_message(filters.command("help") & filters.private)
    async def help_cmd(client, message):
        help_text = (
            "🚀 **Ultimate FileStore Help Guide**\n\n"
            "📂 **File Management:**\n"
            " └ Simply send any file to get a secure, sharable link.\n\n"
            "📦 **Batch Creation:**\n"
            " 1️⃣ Send `/batch` to start.\n"
            " 2️⃣ Upload all files you want to group.\n"
            " 3️⃣ Send `/done` to generate a single master link.\n\n"
            "🤖 **Bot Cloning (Self-Service):**\n"
            " 1️⃣ Create a new bot at @BotFather.\n"
            " 2️⃣ Copy the API Token.\n"
            " 3️⃣ Use `/clone <TOKEN>` here to create your own copy!\n\n"
            "⚙️ **Admin Features:**\n"
            " • `/setfs <ID>` - Setup Force Subscribe.\n"
            " • `/settimer <SEC>` - Set auto-delete timer.\n"
            " • `/setwelcomeimg` - Set a custom welcome photo.\n"
            " • `/setmsg` - Set a custom welcome text.\n\n"
            "📊 **Statistics:**\n"
            " • Use `/stats` to view your growth and usage."
        )
        await message.reply(help_text)

    @app.on_message(filters.command("setglobal") & filters.private)
    async def set_global_msg(client, message):
        if message.from_user.id != MAIN_ADMIN: return
        if len(message.command) < 2:
            return await message.reply("Usage: `/setglobal YOUR_MESSAGE`")

        msg = message.text.split(None, 1)[1]
        update_global_config("global_msg", msg)
        await message.reply("✅ Global message set successfully!")

    @app.on_message(filters.command("addadmin") & filters.private)
    async def add_admin_handler(client, message):
        if message.from_user.id != MAIN_ADMIN: return
        if len(message.command) < 2:
            return await message.reply("Usage: `/addadmin USER_ID`")

        try:
            target = int(message.command[1])
            admins = load_db(ADMINS_DB)
            admins[str(target)] = str(datetime.now())
            save_db(ADMINS_DB, admins)
            await message.reply(f"✅ User `{target}` is now a Global Admin.")
        except ValueError:
            await message.reply("❌ Invalid ID!")

    @app.on_message(filters.command("deladmin") & filters.private)
    async def del_admin_handler(client, message):
        if message.from_user.id != MAIN_ADMIN: return
        if len(message.command) < 2:
            return await message.reply("Usage: `/deladmin USER_ID`")

        target = message.command[1]
        admins = load_db(ADMINS_DB)
        if target in admins:
            del admins[target]
            save_db(ADMINS_DB, admins)
            await message.reply(f"✅ Admin `{target}` removed.")
        else:
            await message.reply("❌ Not an admin!")

    @app.on_message(filters.command("refer") & filters.private)
    async def refer_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        user_data = get_user(user_id, bot_id)

        link = f"https://t.me/{client.me.username}?start=ref_{user_id}"
        text = (
            "🔗 **Referral Program**\n\n"
            "Invite your friends and earn points! points can be used to get **Premium Features**.\n\n"
            f"💰 **Your Points:** `{user_data.get('points', 0)}` pts\n"
            f"👥 **Your Referrals:** `{user_data.get('referrals', 0)}` users\n\n"
            f"🚀 **Your Link:** `{link}`\n\n"
            "🎁 *Reward: 10 points per successful referral!*"
        )
        await message.reply(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share Link", url=f"https://t.me/share/url?url={link}")]]))

    @app.on_message(filters.command("points") & filters.private)
    async def points_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        user_data = get_user(user_id, bot_id)
        await message.reply(f"💰 **You have:** `{user_data.get('points', 0)}` points.")

    @app.on_message(filters.command("premium") & filters.private)
    async def premium_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        user_data = get_user(user_id, bot_id)

        is_premium = user_data.get("is_premium", False)
        status = "✅ Active" if is_premium else "❌ Inactive"

        text = (
            "🌟 **Premium Membership**\n\n"
            f"Status: {status}\n\n"
            "✨ **Benefits:**\n"
            " ├ 🚀 No Auto-Delete for your files\n"
            " ├ 🎯 Priority File Delivery\n"
            " ├ 📂 Unlimited Batch Size\n"
            " └ 🛡️ Ad-Free Experience\n\n"
            "💰 **Cost:** 500 points or Contact Admin.\n\n"
            "To buy with points, use `/buy_premium`"
        )
        await message.reply(text)

    @app.on_message(filters.command("buy_premium") & filters.private)
    async def buy_premium_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        users = load_db(USERS_DB)
        user_key = f"{bot_id}_{user_id}"

        if users[user_key].get("is_premium"):
            return await message.reply("✅ You are already a Premium user!")

        if users[user_key].get("points", 0) < 500:
            return await message.reply("❌ You need at least 500 points to buy Premium! Refer more friends.")

        users[user_key]["points"] -= 500
        users[user_key]["is_premium"] = True
        save_db(USERS_DB, users)
        await message.reply("🎉 **Congratulations!** You are now a Premium user.")

    @app.on_message(filters.command("botinfo") & filters.private)
    async def bot_info_cmd(client, message):
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        
        if bot_info:
            children = len(get_child_bots(bot_id))
            await message.reply(
                f"ℹ️ **Bot Info**\n\n"
                f"🤖 @{client.me.username}\n"
                f"👤 Owner: {bot_info['owner_name']}\n"
                f"🌳 Cloned Bots: {children}\n"
                f"📢 Force Sub: {len(bot_info.get('force_subs', []))} Channels"
            )

    @app.on_message(filters.command("clone") & filters.private)
    async def clone_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        
        if is_user_banned(user_id, bot_id):
            return await message.reply("🚫 Banned!")
        
        if len(message.command) < 2:
            user_bots = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == user_id]
            return await message.reply(
                f"🤖 **Clone Bot**\n\n"
                f"Your Bots: {len(user_bots)}\n\n"
                f"**Steps:**\n"
                f"1. Go to @BotFather -> /newbot\n"
                f"2. Copy the API Token\n"
                f"3. Send: `/clone YOUR_TOKEN` here.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🤖 BotFather", url="https://t.me/BotFather")]])
            )
        
        token = message.command[1]
        msg = await message.reply("🔄 Cloning bot, please wait...")
        
        try:
            # Check if token already exists
            all_bots = get_all_bots()
            for b in all_bots.values():
                if isinstance(b, dict) and b.get("token") == token:
                    return await msg.edit("❌ This token is already registered!")

            new_app = await start_bot(token, parent_bot_id=bot_id)
            if new_app:
                bot_info_res = await new_app.get_me()
                save_bot_info(token, bot_info_res.id, bot_info_res.username, user_id, message.from_user.first_name, bot_id)
                await msg.edit(
                    f"✅ **Bot Cloned Successfully!**\n\n"
                    f"🤖 @{bot_info_res.username}\n"
                    f"🆔 `{bot_info_res.id}`\n\n"
                    f"All features are active! Make sure to Add your clone to channels as Admin for Force Sub.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Start Bot", url=f"https://t.me/{bot_info_res.username}")]])
                )
            else:
                await msg.edit("❌ Failed! Invalid token or Bot API error.")
        except Exception as e:
            await msg.edit(f"❌ Error: {str(e)}")

    @app.on_message(filters.command("setfs") & filters.private)
    async def set_fs_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        
        if not bot_info or (bot_info['owner_id'] != user_id and user_id != MAIN_ADMIN):
            return await message.reply("❌ Only owner can set force subscribe!")
        
 advanced-filestore-bot-upgrade-16475289135707005334
        force_subs = bot_info.get('force_subs', [])

        if len(message.command) < 2:
            text = "⚙️ **Force Subscribe Settings (Up to 6)**\n\n"
            if force_subs:
                for i, c_id in enumerate(force_subs, 1):
                    text += f"{i}. `{c_id}`\n"
            else:
                text += "❌ No channels set."

            text += (
                f"\n**Add:** `/setfs -100xxxxxxxx`\n"
                f"**Remove:** `/setfs off -100xxxx`\n"
                f"**Clear All:** `/setfs clear`\n\n"
                f"⚠️ Note: Bot must be Admin in the channel!"
            )
            return await message.reply(text)

        cmd = message.command[1].lower()
        
        if cmd == "clear":
            update_bot_info(bot_id, 'force_subs', [])
            cascade_force_subs(bot_id, [])
            return await message.reply("✅ All Force Sub channels cleared!")

        if cmd == "off":
            if len(message.command) < 3:
                return await message.reply("Usage: `/setfs off -100xxxxxx` to remove specific channel.")
            try:
                target_id = int(message.command[2])
                if target_id in force_subs:
                    force_subs.remove(target_id)
                    update_bot_info(bot_id, 'force_subs', force_subs)
                    cascade_force_subs(bot_id, force_subs)
                    return await message.reply(f"✅ Removed `{target_id}` from Force Sub.")
                else:
                    return await message.reply("❌ Channel not found in list.")
            except:
                return await message.reply("❌ Invalid Channel ID.")

        try:
            channel_id = int(message.command[1])
            if channel_id in force_subs:
                return await message.reply("❌ Channel already added.")

            if len(force_subs) >= 6:
                return await message.reply("❌ Maximum 6 channels allowed!")

            # Check admin rights
            try:
                chat_member = await client.get_chat_member(channel_id, client.me.id)
                if chat_member.status != ChatMemberStatus.ADMINISTRATOR:
                    return await message.reply("❌ I am not Admin in that channel!")
            except Exception:
                 return await message.reply("❌ Cannot access channel! Make sure I am Admin and ID is correct.")

            chat = await client.get_chat(channel_id)
            force_subs.append(channel_id)
            update_bot_info(bot_id, 'force_subs', force_subs)
            
            count = cascade_force_subs(bot_id, force_subs) if bot_info['owner_id'] == user_id else 0
            await message.reply(f"✅ **Channel Added!**\n\n📢 {chat.title}\n🆔 `{channel_id}`\n\nApplied to {count} child bots automatically.")
        except ValueError:
            await message.reply("❌ Invalid Channel ID!")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

        force_subs = bot_info.get("force_subs", [])

        if len(message.command) < 2:
            text = "⚙️ **Force Subscribe Settings (Up to 3 Channels)**\n\n"
            if not force_subs:
                text += "No channels configured.\n"
            else:
                for i, fs in enumerate(force_subs, 1):
                    text += f"{i}. 🆔 `{fs['channel_id']}`\n   🔗 Link: {fs.get('invite_link') or 'Auto'}\n"

            text += (
                "\n**Commands:**\n"
                "• `/setfs add -100xxx link` - Add channel\n"
                "• `/setfs del -100xxx` - Remove channel\n"
                "• `/setfs clear` - Clear all\n"
                "• `/setfs off` - Disable FS\n\n"
                "⚠️ *Bot must be Admin in channels!*"
            )
            return await message.reply(text)
        
        cmd = message.command[1].lower()
        
        if cmd == "clear" or cmd == "off":
            update_bot_info(bot_id, 'force_subs', [])
            update_bot_info(bot_id, 'force_sub', None)
            count = cascade_force_sub(bot_id, []) if bot_info['owner_id'] == user_id or user_id == MAIN_ADMIN else 0
            return await message.reply(f"✅ All Force Sub channels cleared! (Applied to {count} child bots)")

        if cmd == "add":
            if len(force_subs) >= 3:
                return await message.reply("❌ Maximum 3 channels allowed!")

            if len(message.command) < 3:
                return await message.reply("Usage: `/setfs add -100xxxxxxxx [invite_link]`")

            try:
                channel_id = int(message.command[2])
                invite_link = message.command[3] if len(message.command) > 3 else None

                # Check admin
                try:
                    await client.get_chat_member(channel_id, client.me.id)
                except Exception:
                    return await message.reply("❌ I am not Admin or cannot access channel!")

                force_subs.append({"channel_id": channel_id, "invite_link": invite_link})
                update_bot_info(bot_id, 'force_subs', force_subs)
                count = cascade_force_sub(bot_id, force_subs) if bot_info['owner_id'] == user_id or user_id == MAIN_ADMIN else 0
                return await message.reply(f"✅ Channel added to Force Subscribe! (Applied to {count} child bots)")
            except ValueError:
                return await message.reply("❌ Invalid Channel ID!")

        if cmd == "del":
            if len(message.command) < 3:
                return await message.reply("Usage: `/setfs del -100xxxxxxxx`")
            
            try:
                channel_id = int(message.command[2])
                new_fs = [fs for fs in force_subs if fs['channel_id'] != channel_id]
                if len(new_fs) == len(force_subs):
                    return await message.reply("❌ Channel not found in list!")

                update_bot_info(bot_id, 'force_subs', new_fs)
                count = cascade_force_sub(bot_id, new_fs) if bot_info['owner_id'] == user_id or user_id == MAIN_ADMIN else 0
                return await message.reply(f"✅ Channel removed from Force Subscribe! (Applied to {count} child bots)")
            except ValueError:
                return await message.reply("❌ Invalid Channel ID!")
 main

    @app.on_message(filters.command("broadcast") & filters.private)
    async def broadcast_cmd(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)
        
        can_broadcast = False
        bot_ids_to_broadcast = []
        
        # Determine scope
        if user_id == MAIN_ADMIN:
            can_broadcast = True
            bot_ids_to_broadcast = list(ACTIVE_CLIENTS.keys()) # All bots
        elif bot_info and bot_info['owner_id'] == user_id:
            can_broadcast = True
            bot_ids_to_broadcast = [bot_id] # Own bot
            # Add child bots
            for desc in get_all_descendant_bots(bot_id):
                if desc['bot_id'] in ACTIVE_CLIENTS:
                    bot_ids_to_broadcast.append(desc['bot_id'])
        
        if not can_broadcast:
            return await message.reply("❌ No permission!")
        
        if not message.reply_to_message:
            total_users = sum(len(get_all_users(bid)) for bid in bot_ids_to_broadcast if bid in ACTIVE_CLIENTS)
            return await message.reply(
                f"📢 **Broadcast Module**\n\n"
                f"👥 Targeted Users: {total_users}\n"
                f"🤖 Targeted Bots: {len(bot_ids_to_broadcast)}\n\n"
                f"Usage: Reply to any message/photo/video with `/broadcast` to send."
            )
        
        TEMP_BROADCAST_DATA[user_id] = {
            "message": message.reply_to_message,
            "bot_ids": bot_ids_to_broadcast
        }
        
        await message.reply(
            "⚠️ **Confirm Broadcast?**\n\nThis will send the message to all users.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, Send", callback_data="confirm_broadcast"), InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
            ])
        )

    @app.on_message(filters.command("batch") & filters.private)
    async def batch_start(client, message):
        user_id = message.from_user.id
        if is_user_banned(user_id, client.me.id):
            return await message.reply("🚫 Banned!")
        TEMP_BATCH_DATA[user_id] = []
        await message.reply("📦 **Batch Mode ON!**\n\nSend files now. They will be added to the list.\nWhen finished, type `/done`.")

    @app.on_message(filters.command("done") & filters.private)
    async def batch_done(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        bot_info = get_bot_info(bot_id)

        if user_id not in TEMP_BATCH_DATA or not TEMP_BATCH_DATA[user_id]:
            return await message.reply("❌ No files in batch! Start with `/batch`.")
        
        file_ids = TEMP_BATCH_DATA[user_id]
        batch_id = get_unique_id()
        
        batches = load_db(BATCH_DB)
        batches[batch_id] = {
            "files": file_ids, "created_by": user_id, "bot_id": bot_id, "date": str(datetime.now())
        }
        save_db(BATCH_DB, batches)
        del TEMP_BATCH_DATA[user_id]
        update_user_stats(user_id, bot_id, "batches_created")
        
        link = f"https://t.me/{client.me.username}?start=b_{batch_id}"
        short_link = await get_short_link(bot_info, link)

        await message.reply(
            f"✅ **Batch Created!**\n\n📦 Files: {len(file_ids)}\n🔗 `{short_link}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share Batch", url=f"https://t.me/share/url?url={short_link}")]])
        )

    @app.on_message(filters.command("cancel") & filters.private)
    async def batch_cancel(client, message):
        user_id = message.from_user.id
        if user_id in TEMP_BATCH_DATA:
            del TEMP_BATCH_DATA[user_id]
            await message.reply("❌ Batch cancelled!")
        else:
            await message.reply("No active batch operation.")

    @app.on_callback_query()
    async def callback_handler(client, callback):
        user_id = callback.from_user.id
        data = callback.data
        bot_id = client.me.id
        
        if is_user_banned(user_id, bot_id):
            await callback.answer("🚫 Banned!", show_alert=True)
            return
        
        if data == "start_batch":
            TEMP_BATCH_DATA[user_id] = []
            await callback.message.edit("📦 **Batch Mode Active**\n\nSend files now...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_batch")]]))
            await callback.answer()
        
        elif data == "cancel_batch":
            if user_id in TEMP_BATCH_DATA:
                del TEMP_BATCH_DATA[user_id]
            await callback.message.edit("❌ Batch Cancelled!")
            await callback.answer()
        
        elif data == "clone_menu":
            user_bots = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == user_id]
            await callback.message.edit(
                f"🤖 **Clone Bot**\n\nYour Bots: {len(user_bots)}\n\n1. @BotFather → /newbot\n2. Copy token\n3. `/clone TOKEN`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 BotFather", url="https://t.me/BotFather")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            await callback.answer()
        
        elif data == "user_dashboard":
            user_data = get_user(user_id, bot_id)
            user_bots = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == user_id]
            await callback.message.edit(
                f"📊 **Dashboard**\n\n"
                f"📁 Files: {user_data.get('files_uploaded', 0) if user_data else 0}\n"
                f"📦 Batches: {user_data.get('batches_created', 0) if user_data else 0}\n"
                f"🤖 Bots: {len(user_bots)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
            )
            await callback.answer()
        
        elif data == "my_bots_menu":
            user_bots = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == user_id]
            if not user_bots:
                text = "🤖 No Bots!\n\nCreate your first bot!"
                buttons = [[InlineKeyboardButton("➕ Clone", callback_data="clone_menu")]]
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
                fs_count = len(bot_info.get('force_subs', []))
                msg = "✅" if bot_info.get('custom_welcome') else "❌"
                await callback.message.edit(
                    f"⚙️ **Settings**\n\n🤖 @{client.me.username}\n📢 Force Sub: {fs_count} Channels\n💬 Welcome: {msg}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
                )
            await callback.answer()
        
        elif data == "help_menu":
            await callback.message.edit(
                "ℹ️ **Advanced Help Guide**\n\n"
                "• **Files:** Send any file to get a secure link.\n"
                "• **Batch:** Use `/batch`, send multiple files, then `/done`.\n"
                "• **Clone:** Use `/clone` with your Bot Token.\n"
                "• **Referral:** Invite friends to earn rewards.\n"
                "• **Timer:** Files are deleted automatically after a set time.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
            )
            await callback.answer()

        elif data == "referral_menu":
            user_data = get_user(user_id, bot_id)
            ref_link = f"https://t.me/{client.me.username}?start=ref_{user_id}"
            text = (
                f"🎁 **Referral Program**\n\n"
                f"Invite your friends and earn premium benefits!\n\n"
                f"👥 Your Referrals: `{user_data.get('referrals', 0)}`\n"
                f"🔗 Your Link:\n`{ref_link}`"
            )
            await callback.message.edit(text, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Share Link", url=f"https://t.me/share/url?url={ref_link}")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
            ]))
            await callback.answer()

        elif data == "premium_menu":
            user_data = get_user(user_id, bot_id)
            status = "💎 Premium" if user_data.get("is_premium") else "🆓 Free"
            text = (
                f"💎 **Premium Subscription**\n\n"
                f"Status: **{status}**\n\n"
                f"**Benefits:**\n"
                f"• No auto-delete on your files\n"
                f"• Higher file size limits\n"
                f"• Priority support\n\n"
                f"Contact @{ACTIVE_CLIENTS[MAIN_ADMIN]['username'] if MAIN_ADMIN in ACTIVE_CLIENTS else 'Admin'} to upgrade!"
            )
            await callback.message.edit(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))
            await callback.answer()
        
        elif data == "admin_panel":
            bot_info = get_bot_info(bot_id)
            is_owner = bot_info and bot_info['owner_id'] == user_id
            if not is_admin(user_id) and not is_owner:
                await callback.answer("❌ No access!", show_alert=True)
                return
            await callback.message.edit("⚡ **Admin Panel**", reply_markup=get_admin_panel_keyboard())
            await callback.answer()
        
        elif data == "broadcast_menu":
            bot_info = get_bot_info(bot_id)
            is_owner = bot_info and bot_info['owner_id'] == user_id
            if not is_admin(user_id) and not is_owner and user_id != MAIN_ADMIN:
                await callback.answer("❌ No access!", show_alert=True)
                return
            user_count = len(get_all_users(bot_id))
            await callback.message.edit(
                f"📢 **Broadcast**\n\n👥 Users: {user_count}\n\nReply to message with `/broadcast`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
            await callback.answer()
        
        elif data == "admin_stats":
            bot_users = len(get_all_users(bot_id))
            files = load_db(FILES_DB)
            bot_files = [f for f in files.values() if f.get('bot_id') == bot_id]
            await callback.message.edit(
                f"📊 **Stats**\n\n👥 Users: {bot_users}\n📁 Files: {len(bot_files)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()
        
        elif data == "manage_users":
            bot_users = get_all_users(bot_id)
            banned = sum(1 for u in load_db(USERS_DB).values() if u.get('bot_id') == bot_id and u.get('is_banned'))
            await callback.message.edit(
                f"👥 **User Management**\n\n🟢 Active: {len(bot_users)}\n🚫 Banned: {banned}\n\n**Commands:**\n• `/ban USER_ID` - Ban user\n• `/unban USER_ID` - Unban user\n• `/info USER_ID` - User Details",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
            await callback.answer()
        
        elif data == "my_bots_admin":
            user_bots = [b for b in get_all_bots().values() if isinstance(b, dict) and b.get('owner_id') == user_id]
            text = f"🤖 **Your Bots ({len(user_bots)})**\n\n"
            if user_bots:
                for i, bot in enumerate(user_bots[:10], 1):
                    status = "🟢" if bot['bot_id'] in ACTIVE_CLIENTS else "🔴"
                    text += f"{i}. {status} @{bot['bot_username']}\n"
            else:
                text += "No bots yet!"
            await callback.message.edit(
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Clone", callback_data="clone_menu")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
                ])
            )
            await callback.answer()
        
        elif data == "supreme_panel":
            if user_id != MAIN_ADMIN:
                await callback.answer("❌ Supreme access only!", show_alert=True)
                return
            await callback.message.edit("👑 **Supreme Panel**", reply_markup=get_supreme_panel_keyboard())
            await callback.answer()
        
        elif data == "global_broadcast":
            if user_id != MAIN_ADMIN:
                await callback.answer("❌ Access denied!", show_alert=True)
                return
            total_users = len(get_all_users())
            await callback.message.edit(
                f"🌍 **Global Broadcast**\n\n👥 Users: {total_users}\n🤖 Bots: {len(ACTIVE_CLIENTS)}\n\nReply to message with `/broadcast`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]])
            )
            await callback.answer()

        elif data == "set_welcome_msg":
            await callback.message.edit(
                "💬 **Set Custom Welcome**\n\nTo set a custom welcome message for this bot, reply to any message with `/setmsg` command.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bot_settings_admin")]])
            )
            await callback.answer()
        
        elif data == "system_stats":
            if user_id != MAIN_ADMIN:
                await callback.answer("❌ Access denied!", show_alert=True)
                return
            all_bots = get_all_bots()
            users = load_db(USERS_DB)
            files = load_db(FILES_DB)

            # Get disk usage
            total, used, free = shutil.disk_usage("/")
            disk_stats = f"{used // (2**30)}GB / {total // (2**30)}GB"

            stats_text = (
                "🖥 **System Status Report**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 **Total Bots:** `{len(all_bots)}` bots\n"
                f"🟢 **Online Now:** `{len(ACTIVE_CLIENTS)}` bots\n"
                f"👥 **Total Users:** `{len(users)}` users\n"
                f"📁 **Total Files:** `{len(files)}` files\n"
                f"💾 **Disk Usage:** `{disk_stats}`\n"
                f"⏳ **Uptime:** `{str(datetime.now() - START_TIME).split('.')[0]}`\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "✨ *Status: All Systems Normal*"
            )
            await callback.message.edit(
                stats_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 REFRESH", callback_data="system_stats")],
                    [InlineKeyboardButton("🔙 BACK", callback_data="supreme_panel")]
                ])
            )
            await callback.answer()
        
        elif data == "all_bots_list":
            if user_id != MAIN_ADMIN:
                await callback.answer("❌ Access denied!", show_alert=True)
                return
            all_bots = get_all_bots()
            text = f"🤖 **All Bots ({len(all_bots)})**\n\n"
            count = 0
            for bot_id_key, bot in all_bots.items():
                if isinstance(bot, dict) and count < 20:
                    status = "🟢" if int(bot_id_key) in ACTIVE_CLIENTS else "🔴"
                    text += f"{count+1}. {status} @{bot['bot_username']}\n"
                    count += 1
            if len(all_bots) > 20:
                text += f"\n... and {len(all_bots) - 20} more"
            await callback.message.edit(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]]))
            await callback.answer()
        
        elif data == "manage_admins":
            if user_id != MAIN_ADMIN:
                await callback.answer("❌ Access denied!", show_alert=True)
                return
            admins = load_db(ADMINS_DB)
            text = (
                f"👑 **Admin Management**\n\n"
                f"🌟 **Main Owner:** `{MAIN_ADMIN}`\n\n"
                f"👥 **Secondary Admins ({len(admins)}):**\n"
            )
            for admin_id in admins.keys():
                text += f" • `{admin_id}`\n"

            text += "\n**Commands:**\n• `/addadmin ID` - Add new admin\n• `/deladmin ID` - Remove admin"
            await callback.message.edit(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="supreme_panel")]]))
            await callback.answer()

        elif data == "toggle_maintenance":
            if user_id != MAIN_ADMIN:
                await callback.answer("❌ Access denied!", show_alert=True)
                return
            config = get_global_config()
            curr = config.get("maintenance", False)
            update_global_config("maintenance", not curr)
            await callback.answer(f"Maintenance: {'ON' if not curr else 'OFF'}", show_alert=True)
            await callback.message.edit("👑 **Supreme Panel**", reply_markup=get_supreme_panel_keyboard())

        elif data == "bot_settings_admin":
            bot_info = get_bot_info(bot_id)
            if not bot_info: return
            text = (
                f"⚙️ **Bot Settings**\n\n"
                f"🤖 Bot: @{bot_info['bot_username']}\n"
                f"👋 Custom Welcome: {'Enabled' if bot_info.get('custom_welcome') else 'Disabled'}\n"
 advanced-filestore-bot-upgrade-16475289135707005334
                f"⏱ Auto Delete: {bot_info.get('auto_delete_timer', 600)//60} Mins"
            )
            buttons = [
                [InlineKeyboardButton("💬 Set Welcome", callback_data="set_welcome_msg")],
                [InlineKeyboardButton("⏱ Set Timer", callback_data="set_delete_timer")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]

                f"⏱ Auto Delete: `{bot_info.get('auto_delete_time', 600)}` seconds\n"
                f"✅ Auto Approve: {'ON' if bot_info.get('auto_approve') else 'OFF'}"
            )
            buttons = [
                [InlineKeyboardButton("💬 SET WELCOME MSG", callback_data="set_welcome_msg")],
                [InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]
 main
            ]
            await callback.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))
            await callback.answer()

 advanced-filestore-bot-upgrade-16475289135707005334
        elif data == "set_delete_timer":
            await callback.message.edit(
                "⏱ **Set Auto-Delete Timer**\n\nSend command: `/settimer SECONDS` (e.g., `/settimer 600` for 10 mins).",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bot_settings_admin")]])
            )
            await callback.answer()

        elif data == "forcesub_admin":
            bot_info = get_bot_info(bot_id)
            if not bot_info: return
            curr_fs = bot_info.get('force_subs', [])
            text = f"🔒 **Force Subscribe Settings**\n\nChannels: {len(curr_fs)}/6\n\n"
            for i, cid in enumerate(curr_fs, 1):
                text += f"{i}. `{cid}`\n"

            text += "\nTo manage, use command:\n`/setfs`"

        elif data == "toggle_auto_approve":
            bot_info = get_bot_info(bot_id)
            if not bot_info: return
            curr = bot_info.get("auto_approve", False)
            update_bot_info(bot_id, "auto_approve", not curr)
            await callback.answer(f"Auto-Approve: {'ENABLED' if not curr else 'DISABLED'}", show_alert=True)
            await callback.message.edit("⚡ **Admin Panel**", reply_markup=get_admin_panel_keyboard())

        elif data == "edit_timer":
            await callback.message.edit(
                "⏱ **Edit Auto-Delete Timer**\n\nUse command: `/settimer SECONDS`\nExample: `/settimer 300` for 5 minutes.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]])
            )
            await callback.answer()

        elif data == "set_welcome_img":
            await callback.message.edit(
                "🖼 **Set Welcome Image**\n\nReply to any photo with command: `/setwelcomeimg`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]])
            )
            await callback.answer()

        elif data == "manual_backup":
            if user_id != MAIN_ADMIN: return
            await backup_db_to_telegram()
            await callback.answer("✅ Backup sent to DB Channel!", show_alert=True)

        elif data == "manual_clean_cache":
            if user_id != MAIN_ADMIN: return
            count = clean_expired_cache()
            await callback.answer(f"🧹 Cleaned {count} expired cache entries!", show_alert=True)

        elif data == "restart_all_bots":
            if user_id != MAIN_ADMIN: return
            await callback.answer("🔄 Restarting System... Please wait.", show_alert=True)
            logger.info("Restarting process...")
            os.execl(sys.executable, sys.executable, *sys.argv)

        elif data == "forcesub_admin":
            bot_info = get_bot_info(bot_id)
            if not bot_info: return
            force_subs = bot_info.get("force_subs", [])
            text = "🔒 **Force Subscribe Settings (Up to 3 Channels)**\n\n"
            if not force_subs:
                text += "No channels configured.\n"
            else:
                for i, fs in enumerate(force_subs, 1):
                    text += f"{i}. 🆔 `{fs['channel_id']}`\n"

            text += "\nTo manage, use command:\n`/setfs`"
            await callback.message.edit(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]))
            await callback.answer()

        elif data == "shortener_admin":
            bot_info = get_bot_info(bot_id)
            if not bot_info: return
            status = "✅ Enabled" if bot_info.get("is_shortener_enabled") else "❌ Disabled"
            text = (
                f"🔗 **URL Shortener Settings**\n\n"
                f"Status: {status}\n"
                f"URL: `{bot_info.get('shortener_url', 'Not set')}`\n\n"
                f"To change, use command:\n`/shortener`"
            )
 main
            await callback.message.edit(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]))
            await callback.answer()

        elif data == "global_msg_set":
            if user_id != MAIN_ADMIN: return
            await callback.message.edit(
                "📢 **Global Message**\n\nThis feature allows setting a message that appears for ALL users on all bots.\n\nUse command:\n`/setglobal MESSAGE`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="supreme_panel")]])
            )
            await callback.answer()
        
        elif data == "confirm_broadcast":
            if user_id not in TEMP_BROADCAST_DATA:
                await callback.answer("❌ Expired!", show_alert=True)
                return
            
            broadcast_data = TEMP_BROADCAST_DATA[user_id]
            msg = broadcast_data["message"]
            bot_ids = broadcast_data["bot_ids"]
            
 advanced-filestore-bot-upgrade-16475289135707005334
            status_msg = await callback.message.edit("📢 **Broadcasting Started...**")
            
            success, failed = await broadcast_message(msg, bot_ids, status_msg)
            
            del TEMP_BROADCAST_DATA[user_id]
            await status_msg.edit(
                f"✅ **Broadcast Completed!**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ Success: `{success}`\n"
                f"❌ Failed: `{failed}`\n"
                f"🤖 Bots: `{len(bot_ids)}`"
            )

            status_msg = await callback.message.edit("📢 **Broadcasting in progress...**")
            
            success, failed = await broadcast_message(msg, bot_ids, status_msg=status_msg)
            
            del TEMP_BROADCAST_DATA[user_id]
            await status_msg.edit(f"✅ **Broadcast Completed!**\n\n📈 **Results:**\n ├ Success: `{success}`\n ├ Failed: `{failed}`\n └ Total Bots: `{len(bot_ids)}`")
 main
        
        elif data == "cancel_broadcast":
            if user_id in TEMP_BROADCAST_DATA:
                del TEMP_BROADCAST_DATA[user_id]
            await callback.message.edit("❌ Broadcast Cancelled!")
            await callback.answer()
        
        elif data == "back_to_start":
            await callback.message.edit(
                f"👋 **Welcome Back!**\n\n🤖 @{client.me.username}\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n✨ Ultra Advanced FileStore Bot",
                reply_markup=get_start_keyboard(bot_id, user_id)
            )
            await callback.answer()

    @app.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private)
    async def file_handler(client, message):
        user_id = message.from_user.id
        bot_id = client.me.id
        
        if is_user_banned(user_id, bot_id):
            return await message.reply("🚫 Banned!")

        # 1. Forward to DB Channel first (High Advance Feature: Centralized Storage)
        try:
            db_msg = await message.forward(DB_CHANNEL)
        except Exception as e:
            logger.error(f"Forward to DB Channel failed: {e}")
            return await message.reply("❌ Error: DB Channel not accessible. Contact Admin.")

        # Capture Original Caption
        original_caption = message.caption

        # Determine Media Type and details from DB message
        if db_msg.photo:
            file_id = db_msg.photo.file_id
            file_name = f"photo_{db_msg.photo.file_unique_id}.jpg"
            file_size = db_msg.photo.file_size
        elif db_msg.video:
            file_id = db_msg.video.file_id
            file_name = db_msg.video.file_name or "video.mp4"
            file_size = db_msg.video.file_size
        elif db_msg.audio:
            file_id = db_msg.audio.file_id
            file_name = db_msg.audio.file_name or "audio.mp3"
            file_size = db_msg.audio.file_size
        elif db_msg.document:
            file_id = db_msg.document.file_id
            file_name = db_msg.document.file_name
            file_size = db_msg.document.file_size
        else:
            return # Unknown media type

        unique_id = get_unique_id()
        
        # Save to DB
        files = load_db(FILES_DB)
        files[unique_id] = {
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "caption": original_caption,
            "user_id": user_id,
            "bot_id": bot_id,
            "upload_date": str(datetime.now()),
            "db_msg_id": db_msg.id # Store DB message ID
        }
        save_db(FILES_DB, files)
        
        # Add to Cache immediately (so we can forward it right back if needed)
        add_to_cache(file_id, db_msg.id, DB_CHANNEL, bot_id, original_caption)
        update_user_stats(user_id, bot_id, "files_uploaded")
        
        # Log to Log Channel
        bot_info = get_bot_info(bot_id)
        if bot_info and bot_info.get("log_channel"):
            try:
                await client.copy_message(bot_info["log_channel"], message.chat.id, message.id, caption=f"📤 **File Uploaded**\n👤 User: `{user_id}`\n🏷 Name: `{file_name}`")
            except:
                pass

        # Check Batch Mode
        if user_id in TEMP_BATCH_DATA:
            TEMP_BATCH_DATA[user_id].append(unique_id)
            await message.reply(
                f"✅ **Added to Batch!**\n\n📂 {file_name}\n🔢 Files in batch: {len(TEMP_BATCH_DATA[user_id])}",
                quote=True
            )
        else:
            # Single File Link
            bot_info = get_bot_info(bot_id)
            link = f"https://t.me/{client.me.username}?start=f_{unique_id}"
            short_link = await get_short_link(bot_info, link)

            await message.reply(
                f"✅ **File Saved!**\n\n📁 `{file_name}`\n📊 {format_size(file_size)}\n\n🔗 **Link:**\n`{short_link}`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share Link", url=f"https://t.me/share/url?url={short_link}")]])
            )

async def background_tasks():
    while True:
        await asyncio.sleep(600) # Every 10 mins
        try:
            # 1. Clean Flood data to prevent memory leak
            USER_FLOOD.clear()

            # 2. Clean Cache
            count = clean_expired_cache()
            if count > 0:
                logger.info(f"🗑 Cleaned {count} expired cache entries")

            # 2. Backup DB
            await backup_db_to_telegram()
            logger.info("💾 Database backup completed.")

        except Exception as e:
            logger.error(f"Background task error: {e}")

async def main():
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   🚀 ULTRA FILESTORE BOT - COMPLETE & FIXED         ║")
    print("╚═══════════════════════════════════════════════════════╝")
    
    if DB_CHANNEL == -1000000000000:
        logger.error("❌ DB_CHANNEL not configured! Please set it in main.py")
        return

    # 1. Start Main Bot
    logger.info("🔥 Starting Main Bot...")
    main_app = await start_bot(MAIN_BOT_TOKEN)
    
    if not main_app:
        logger.error("❌ Main Bot Failed to Start! Check Token.")
        return
    
    # 2. Start Cloned Bots
    all_bots = get_all_bots()
    if all_bots:
        logger.info(f"🔄 Loading {len(all_bots)} cloned bots...")
        tasks = []
        for bot_id, bot_data in all_bots.items():
            if not isinstance(bot_data, dict):
                continue
            token = bot_data.get("token")
            parent_id = bot_data.get("parent_bot_id")
            # Skip if it's the main bot token (already started) or invalid
            if token and token != MAIN_BOT_TOKEN:
                tasks.append(start_bot(token, parent_bot_id=parent_id))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success = sum(1 for r in results if r and not isinstance(r, Exception))
            print(f"✅ Successfully started {success} cloned bots.")
    
    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║          ✅ SYSTEM FULLY OPERATIONAL ✅              ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print(f"👑 Admin: {MAIN_ADMIN}")
    print(f"🤖 Active Bots: {len(ACTIVE_CLIENTS)}")
    print()
    print("⏳ Bot is running... Press Ctrl+C to stop.")
    
    # Start background tasks
    asyncio.create_task(background_tasks())
    
    # Keep running
    await idle()
    
    # Shutdown sequence
    logger.info("🛑 Shutting down all bots...")
    if HTTP_SESSION:
        await HTTP_SESSION.close()
    for client_data in ACTIVE_CLIENTS.values():
        try:
            await client_data["app"].stop()
        except:
            pass
    logger.info("✅ Shutdown complete!")

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"❌ Fatal Error: {e}")
