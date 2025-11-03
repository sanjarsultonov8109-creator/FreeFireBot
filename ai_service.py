# ai_service.py
from openai import OpenAI
import os
from dotenv import load_dotenv

# .env faylni yuklaymiz
load_dotenv()

# OpenAI mijozini yaratamiz
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def ask_ai(prompt: str) -> str:
    """Foydalanuvchi so‘roviga sun’iy intellektdan javob olish"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # bu tezkor va arzon model
            messages=[
                {"role": "system", "content": "Sen Free Fire bo‘yicha yordamchi botsan. O‘zbek tilida foydali, qisqa va do‘stona javob ber."},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print("AI bilan bog‘lanishda xato:", e)
        return "Kechirasiz, AI server bilan aloqa vaqtincha uzildi 🤖"
