import json
import re
from telegram import (
    Update,
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
ADMIN_IDS = ["1609002531"]   # keep as STRING
DB_FILE = "users.json"

BROADCAST_MODE = set()

# ================= HELPERS =================
def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def uname(u):
    return f"@{u.username}" if u.username else "NoUsername"

def is_admin(uid):
    return uid in ADMIN_IDS

# ================= /START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    db = load_db()

    # 🚫 banned
    if uid in db["banned"]:
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    # ✅ auto-approve admin
    if is_admin(uid):
        if uid not in db["approved"]:
            db["approved"][uid] = {
                "name": user.full_name,
                "username": uname(user),
            }
            db["pending"].pop(uid, None)
            save_db(db)

        await update.message.reply_text(
            "🤖 Bot Status: ONLINE 🟢\n"
            "⚡ Service: Active\n\n"
            "📱 Please Send Vehicle No.\n\n"
            "[ Note : Only Indian Vehicle Allowed ]"
        )
        return

    # ⏳ normal user approval flow
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

    # approved user
    await update.message.reply_text(
        "🤖 Bot Status: ONLINE 🟢\n"
        "⚡ Service: Active\n\n"
        "📱 Please Send Vehicle No.\n\n"
        "[ Note : Only Indian Vehicle Allowed ]"
    )

# ================= VEHICLE NUMBER HANDLER =================
async def vehicle_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()

    if uid not in db["approved"]:
        return

    text = update.message.text.strip().upper()

    # Match: DL9SCG2660 / KA05P5175 etc
    m = re.match(r"^([A-Z]{2}\d{1,2}[A-Z]{0,3})(\d{4})$", text)
    if not m:
        return

    reg1 = m.group(1)
    reg2 = m.group(2)

    await update.message.reply_text("🔍 Fetching vehicle details...")

    data = fetch_rto_details(reg1, reg2)
    if not data:
        await update.message.reply_text("❌ No data found or server blocked.")
        return

    await update.message.reply_text(json.dumps(data))

# ================= ADMIN COMMANDS =================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_admin(uid):
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    target = context.args[0]
    db = load_db()

    if target in db["pending"]:
        db["approved"][target] = db["pending"].pop(target)
        save_db(db)

        await context.bot.send_message(
            target,
            "✅ Owner approved you!\n"
            "🎉 Now you can use this bot.\n"
            "📱 Send /start to begin."
        )
        await update.message.reply_text("✅ User approved.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_admin(uid):
        return

    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return

    target = context.args[0]
    db = load_db()

    db["approved"].pop(target, None)
    db["pending"].pop(target, None)
    db["banned"][target] = True
    save_db(db)

    await update.message.reply_text("🚫 User banned.")

# ================= BROADCAST =================
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_admin(uid):
        return

    BROADCAST_MODE.add(uid)
    await update.message.reply_text("📢 Send ONE message to broadcast.")

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in BROADCAST_MODE:
        return

    BROADCAST_MODE.remove(uid)
    db = load_db()

    sent = 0
    for user_id in db["approved"]:
        try:
            await context.bot.send_message(user_id, update.message.text)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users.")

# ================= DELETE =================
async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_admin(uid):
        return

    db = load_db()
    buttons = []

    for group in ["approved", "pending", "banned"]:
        for u, info in db[group].items():
            name = info["name"] if isinstance(info, dict) else u
            buttons.append([
                InlineKeyboardButton(
                    f"Delete {name}",
                    callback_data=f"DEL:{u}"
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
    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)
    if not is_admin(uid):
        return

    target = q.data.split(":")[1]
    db = load_db()

    db["approved"].pop(target, None)
    db["pending"].pop(target, None)
    db["banned"].pop(target, None)
    save_db(db)

    await q.edit_message_text(
        "✅ User deleted.\n"
        "Next /start → approval required again."
    )

# ================= MAIN =================
def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("admin", admin_broadcast))
    app.add_handler(CommandHandler("delete", delete_cmd))

    # order matters
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, vehicle_text_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast))

    app.add_handler(CallbackQueryHandler(delete_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
