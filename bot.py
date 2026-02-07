import json
from telegram import (
    Update,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from rto import fetch_rto_details

# ================= CONFIG =================
BOT_TOKEN = "8313512551:AAENVRPjbo4ny--baGTfaf3u9thRKtvuQEc"
ADMIN_IDS = [1609002531]   # your Telegram ID
DB_FILE = "users.json"

BROADCAST_MODE = set()

# ================= HELPERS =================
def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def uname(u):
    return f"@{u.username}" if u.username else "NoUsername"

def is_admin(uid):
    return uid in ADMIN_IDS

# ================= /START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    db = load_db()

    if uid in db["banned"]:
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    if uid not in db["approved"]:
        if uid not in db["pending"]:
            db["pending"][uid] = {
                "name": user.full_name,
                "username": uname(user),
            }
            save_db(db)

            for admin in ADMIN_IDS:
                await context.bot.send_message(
                    admin,
                    f"🆕 New Approval Request\n\n"
                    f"Name: {user.full_name}\n"
                    f"Username: {uname(user)}\n"
                    f"User ID: {uid}\n\n"
                    f"/approve {uid}"
                )

        await update.message.reply_text(
            "🤖 Bot Status: ONLINE 🟢\n"
            "⚡ Service: Active\n\n"
            "⏳ Awaiting for approval from owner...\n"
            "🕒 Please wait, you will be notified once approved."
        )
        return

    await update.message.reply_text(
        "🤖 Bot Status: ONLINE 🟢\n"
        "⚡ Service: Active\n\n"
        "📱 Please Send Vehicle No.\n\n"
        "[ Note : Only Indian Vehicle Allowed ]"
    )

# ================= /RTO =================
async def rto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()

    if uid not in db["approved"]:
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /rto KA05P 5175")
        return

    data = fetch_rto_details(context.args[0].upper(), context.args[1])
    if not data:
        await update.message.reply_text("Failed to fetch data.")
        return

    await update.message.reply_text(json.dumps(data))

# ================= ADMIN =================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    uid = context.args[0]
    db = load_db()

    if uid in db["pending"]:
        db["approved"][uid] = db["pending"].pop(uid)
        save_db(db)

        await context.bot.send_message(
            uid,
            "✅ Owner approved you!\n"
            "🎉 Now you can use this bot.\n"
            "📱 Send /start to begin."
        )
        await update.message.reply_text("✅ User approved.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    uid = context.args[0]
    db = load_db()

    db["approved"].pop(uid, None)
    db["pending"].pop(uid, None)
    db["banned"][uid] = True
    save_db(db)

    await update.message.reply_text("🚫 User banned.")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    BROADCAST_MODE.add(update.effective_user.id)
    await update.message.reply_text(
        "📢 Broadcast Mode Enabled\n"
        "Send ONE message now."
    )

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in BROADCAST_MODE:
        return

    BROADCAST_MODE.remove(uid)
    db = load_db()

    for user_id in db["approved"].keys():
        try:
            await context.bot.send_message(user_id, update.message.text)
        except:
            pass

    await update.message.reply_text("✅ Broadcast sent.")

async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    db = load_db()
    buttons = []

    for group in ["approved", "pending", "banned"]:
        for uid, info in db[group].items():
            name = info["name"] if isinstance(info, dict) else uid
            buttons.append([
                InlineKeyboardButton(
                    f"Delete {name}",
                    callback_data=f"DEL:{uid}"
                )
            ])

    if not buttons:
        await update.message.reply_text("No users found.")
        return

    await update.message.reply_text(
        "🗑 Select user to delete:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    uid = query.data.split(":")[1]
    db = load_db()

    db["approved"].pop(uid, None)
    db["pending"].pop(uid, None)
    db["banned"].pop(uid, None)
    save_db(db)

    await query.edit_message_text(
        f"✅ User {uid} deleted.\n"
        "Next /start → approval required again."
    )

# ================= INIT =================
async def set_commands(app):
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Start Bot"),
            BotCommand("rto", "Vehicle Lookup"),
        ],
        scope=BotCommandScopeDefault(),
    )

    for admin in ADMIN_IDS:
        await app.bot.set_my_commands(
            [
                BotCommand("approve", "Approve User"),
                BotCommand("ban", "Ban User"),
                BotCommand("admin", "Broadcast"),
                BotCommand("delete", "Delete User"),
            ],
            scope=BotCommandScopeChat(admin),
        )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rto", rto_cmd))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("admin", admin_broadcast))
    app.add_handler(CommandHandler("delete", delete_cmd))
    app.add_handler(CallbackQueryHandler(delete_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast))

    app.post_init = set_commands
    app.run_polling()

if __name__ == "__main__":
    main()