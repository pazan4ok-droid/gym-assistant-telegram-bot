import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ЖЕЛЕЗНО ВШИТЫЕ ТВОИ ЛИЧНЫЕ ДАННЫЕ
TOKEN = "8992868971:AAGkBctaG3j3V9CYdwChdAngITwAnd6yEnM"
MY_CLOUDFLARE_URL = "https://nameless-frog-31c6.pazan4ok.workers.dev"

my_private_server = TelegramAPIServer.from_base(MY_CLOUDFLARE_URL)
session = AiohttpSession(api=my_private_server)

bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

# Имя файла для нашей локальной базы данных
DB_FILE = "users_db.json"

# Функции для работы с базой данных (JSON)
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_data(user_id, weight, height, bmi):
    db = load_db()
    db[str(user_id)] = {
        "weight": weight,
        "height": height,
        "bmi": bmi
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

exercises = {
    "грудь": "1. Жим лежа на горизонтальной скамье\n2. Тренажер Бабочка (Пек-дек)\n3. Сведения в кроссовере",
    "спина": "1. Тяга вертикального блока к груди\n2. Тяга горизонтального блока к поясу\n3. Гиперэкстензия (для поясницы)",
    "ноги": "1. Жим ногами в платформе\n2. Разгибание ног сидя\n3. Сгибание ног лежа"
}

class FitnessStates(StatesGroup):
    waiting_for_warmup_weight = State() 
    waiting_for_bmi_weight = State()    
    waiting_for_bmi_height = State()    

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💪 Тренажеры"), KeyboardButton(text="🔥 Разминка")],
        [KeyboardButton(text="📊 Посчитать ИМТ"), KeyboardButton(text="👤 Мой Профиль")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие..."
)

muscles_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Грудь"), KeyboardButton(text="Спина")],
        [KeyboardButton(text="Ноги"), KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear() 
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n"
        "Я твой умный фитнес-ассистент с собственной базой данных. Выбирай нужную функцию! 👇",
        reply_markup=main_keyboard
    )

@dp.message(lambda msg: msg.text == "🔙 Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Возвращаемся в главное меню:", reply_markup=main_keyboard)

@dp.message(lambda msg: msg.text == "💪 Тренажеры")
async def show_muscles_menu(message: types.Message):
    await message.answer("Выбери группу мышц:", reply_markup=muscles_keyboard)

@dp.message(lambda msg: msg.text == "👤 Мой Профиль")
async def show_profile(message: types.Message):
    db = load_db()
    user_id = str(message.from_user.id)
    
    if user_id in db:
        data = db[user_id]
        await message.answer(
            f"👤 *Твой постоянный фитнес-профиль:*\n\n"
            f"⚖️ Вес: {data['weight']} кг\n"
            f"📏 Рост: {data['height']} см\n"
            f"📊 Последний ИМТ: {data['bmi']}\n\n"
            "Данные успешно подгружены из локальной базы!",
            parse_mode="Markdown"
        )
    else:
        await message.answer("🤔 Твоего профиля еще нет в базе данных. Нажми кнопку '📊 Посчитать ИМТ', чтобы создать его!")

@dp.message(lambda msg: msg.text == "🔥 Разминка")
async def warmup_start(message: types.Message, state: FSMContext):
    await state.set_state(FitnessStates.waiting_for_warmup_weight)
    await message.answer(
        "🏋️‍♂️ Давай рассчитaем разминочные подходы!\n\n"
        "Введи свой **максимальный рабочий вес штанги или гантелей** "
        "для того упражнения, которое собираешься делать (просто число в кг, например `40`):",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True),
        parse_mode="Markdown"
    )

@dp.message(FitnessStates.waiting_for_warmup_weight)
async def process_warmup(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.strip())
        w50 = round(weight * 0.5, 1)
        w70 = round(weight * 0.7, 1)
        w90 = round(weight * 0.9, 1)
        
        await message.answer(
            f"🏋️‍♂️ Твой план разминки для веса {weight} кг:\n\n"
            f"1️⃣ Подход: {w50} кг на 10 повторений (50%)\n"
            f"⏳ Отдых 1.5 минуты\n"
            f"2️⃣ Подход: {w70} кг на 6 повторений (70%)\n"
            f"⏳ Отдых 2 минуты\n"
            f"3️⃣ Подход: {w90} кг на 2 повторения (90%)\n"
            f"⏳ Отдых 2.5 минуты\n\n"
            f"🚀 После этого ты полностью готов к рабочим подходам!",
            reply_markup=main_keyboard
        )
        await state.clear() 
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введи только число! Например: 40 или 52.5")

@dp.message(lambda msg: msg.text == "📊 Посчитать ИМТ")
async def bmi_start(message: types.Message, state: FSMContext):
    await state.set_state(FitnessStates.waiting_for_bmi_weight)
    await message.answer(
        "Давай посчитаем Индекс массы тела. Введи свой текущий вес в кг (например `65`):",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True)
    )

@dp.message(FitnessStates.waiting_for_bmi_weight)
async def process_bmi_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.strip())
        await state.update_data(user_weight=weight) 
        await state.set_state(FitnessStates.waiting_for_bmi_height)
        await message.answer("Отлично! А теперь введи свой рост в сантиметрах (например `175`):")
    except ValueError:
        await message.answer("⚠️ Введи корректный вес числом!")

@dp.message(FitnessStates.waiting_for_bmi_height)
async def process_bmi_height(message: types.Message, state: FSMContext):
    try:
        height_cm = float(message.text.strip())
        height_m = height_cm / 100.0 
        
        user_data = await state.get_data()
        weight = user_data.get("user_weight")
        
        bmi = round(weight / (height_m ** 2), 1)
        
        # СОХРАНЯЕМ В НАШУ ЛОКАЛЬНУЮ БАЗУ JSON
        save_user_data(message.from_user.id, weight, height_cm, bmi)
        
        result_text = f"📊 Твой Индекс Массы Тела (ИМТ): *{bmi}*\n\n"
        if bmi < 18.5:
            result_text += "⚠️ У тебя дефицит массы. Чтобы качаться в зале, нужно плотно и правильно питаться, добирая калории! 🥩"
        elif 18.5 <= bmi < 25:
            result_text += "✅ Идеальный вес! Отличная база для построения качественных мышц в зале. Жми на максимум! 💪"
        else:
            result_text += "⚠️ Масса тела повышенная. Зал поможет перегнать лишнее в крутые рельефные мышцы! Налегай на фулл-бади. 🏃‍♂️"
            
        result_text += "\n\n💾 Твой профиль успешно обновлен в базе данных бота!"
        await message.answer(result_text, reply_markup=main_keyboard, parse_mode="Markdown")
        await state.clear()
    except ValueError:
        await message.answer("⚠️ Введи рост целым числом в сантиметрах!")

@dp.message()
async def handle_muscles(message: types.Message):
    user_choice = message.text.lower().strip()
    if user_choice in exercises:
        await message.answer(f"💪 Список тренажеров:\n\n{exercises[user_choice]}")
    else:
        await message.answer("🤔 Не понял команду. Пожалуйста, используй кнопки меню!")

async def main():
    print("Финальный бот с локальной базой данных запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
