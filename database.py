import aiosqlite

DB_NAME = "bot_data.db"

# --- Asosiy baza yaratish ---
async def init_db():
    print("📂 Baza tayyorlanmoqda...")
    async with aiosqlite.connect(DB_NAME) as db:
        # Users jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                almaz INTEGER DEFAULT 0,
                ref_by INTEGER
            )
        """)
        
        # Adminlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT
            )
        """)
        # Guruhlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER UNIQUE,
                title TEXT
            )
        """)
        # To‘lovlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                status TEXT
            )
        """)
               # --- Akkount bozoriga oid jadvallar ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS listings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          seller_id INTEGER,
          title TEXT,
          description TEXT,
          price_almaz INTEGER,
          status TEXT DEFAULT 'pending',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS listing_images (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          listing_id INTEGER,
          file_id TEXT,
          seq INTEGER
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS listing_meta (
          listing_id INTEGER PRIMARY KEY,
          linked_accounts TEXT,
          reserve_gmail INTEGER DEFAULT 0,
          has_issues INTEGER DEFAULT 0,
          issue_description TEXT
        )
        """)

        await db.commit()
    print("✅ Baza tayyor bo‘ldi (users, admins, groups, payments)")

# --- Foydalanuvchilar bilan ishlash ---
async def add_user(user_id: int, username: str, ref_by: int = None):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO users (user_id, username, ref_by) VALUES (?, ?, ?)",
                (user_id, username, ref_by)
            )
            await db.commit()
            print(f"👤 Foydalanuvchi qo‘shildi: {user_id}")

            if ref_by:
                await db.execute("UPDATE users SET almaz = almaz + 10 WHERE user_id = ?", (ref_by,))
                await db.commit()
        except aiosqlite.IntegrityError:
            pass

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

async def add_almaz(user_id: int, amount: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET almaz = almaz + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()
        print(f"💎 {user_id} foydalanuvchisiga {amount} Almaz qo‘shildi")

async def get_leaderboard(limit: int = 10):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT username, almaz FROM users ORDER BY almaz DESC LIMIT ?", (limit,))
        return await cursor.fetchall()

# --- Adminlar bilan ishlash ---
async def add_admin(user_id: int, username: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute("INSERT INTO admins (user_id, username) VALUES (?, ?)", (user_id, username))
            await db.commit()
            print(f"👑 Admin qo‘shildi: {user_id}")
            return True
        except aiosqlite.IntegrityError:
            return False

async def remove_admin(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.commit()
        return cursor.rowcount > 0

async def list_admins():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id, username FROM admins")
        return await cursor.fetchall()

async def is_admin(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return await cursor.fetchone() is not None

# --- Guruhlar bilan ishlash ---
async def add_group(group_id: int, title: str):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute("INSERT INTO groups (group_id, title) VALUES (?, ?)", (group_id, title))
            await db.commit()
            print(f"👥 Guruh qo‘shildi: {title}")
        except aiosqlite.IntegrityError:
            pass

async def list_groups():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT group_id, title FROM groups")
        return await cursor.fetchall()

# --- To‘lov tizimi ---
async def add_payment(user_id: int, amount: int, status: str = "pending"):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO payments (user_id, amount, status)
            VALUES (?, ?, ?)
        """, (user_id, amount, status))
        await db.commit()
        print(f"💰 To‘lov so‘rovi: {user_id} — {amount} so‘m")

async def get_pending_payments():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, user_id, amount FROM payments WHERE status = 'pending'")
        return await cursor.fetchall()

async def confirm_payment(payment_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE payments SET status = 'approved' WHERE id = ?", (payment_id,))
        await db.commit()
        print(f"✅ To‘lov #{payment_id} tasdiqlandi")

# =============================
#  AKKAUNT BOZORI FUNKSIYALARI
# =============================

# 🔹 Yangi listing (sotiladigan akkount) yaratish
async def create_listing(seller_id, title, description, price):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO listings (seller_id, title, description, price_almaz) VALUES (?, ?, ?, ?)",
            (seller_id, title, description, price)
        )
        await db.commit()
        return cursor.lastrowid


# 🔹 Akkount rasmlarini qo‘shish (max 10 ta)
async def add_listing_image(listing_id, file_id, seq):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO listing_images (listing_id, file_id, seq) VALUES (?, ?, ?)",
            (listing_id, file_id, seq)
        )
        await db.commit()


# 🔹 Akkountga qo‘shimcha ma’lumotlar (meta) yozish
async def set_listing_meta(listing_id, linked_accounts, reserve_gmail, has_issues, issue_description):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO listing_meta (listing_id, linked_accounts, reserve_gmail, has_issues, issue_description)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(listing_id) DO UPDATE SET
              linked_accounts=excluded.linked_accounts,
              reserve_gmail=excluded.reserve_gmail,
              has_issues=excluded.has_issues,
              issue_description=excluded.issue_description
        """, (listing_id, linked_accounts, reserve_gmail, has_issues, issue_description))
        await db.commit()


# 🔹 Admin tasdiqlamagan (pending) listinglarni olish
async def get_pending_listings():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, seller_id, title, price_almaz FROM listings WHERE status='pending'")
        return await cursor.fetchall()


# 🔹 Admin tasdiqlagandan keyin listingni “published” qilish
async def publish_listing(listing_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE listings SET status = 'published' WHERE id = ?", (listing_id,))
        await db.commit()


# 🔹 Bitta listingni olish (id orqali)
async def get_listing(listing_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        return await cursor.fetchone()


# 🔹 Listingga tegishli barcha rasm file_idlarini olish
async def get_listing_images(listing_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT file_id FROM listing_images WHERE listing_id = ? ORDER BY seq", (listing_id,))
        return [r[0] for r in await cursor.fetchall()]
