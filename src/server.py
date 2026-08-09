from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import pandas as pd
from symplex import Symplex
import os
import time
from enum import Enum
from timeout_decorator import timeout, TimeoutError

gender_index = {
    'М': 0,
    'Ж': 1,
}


activity_values = {
    'неактивный': 1.2,
    'активный': 1.55,
    'спортивный': 1.9,
}

class Gender(Enum):
    MALE = 'М'
    FEMALE = 'Ж'

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

COUNTRIES = [
    "Российская Федерация", "Беларусь", "Казахстан", 
    "Норвегия", "Канада", "Финляндия", "Исландия", "США",
    "Эквадор", "Кения", "Колумбия", "Индонезия", "Сомали",
    "Австралия", "ЮАР", "Чили", "Аргентина", "Новая Зеландия"
]

VITAMIN_D_FACTORS = {
    "Россия": 1.8,
    "Беларусь": 1.7,
    "Казахстан": 1.6,
    "Норвегия": 1.9,
    "Канада": 1.8,
    "Финляндия": 1.9,
    "Исландия": 1.9,
    "США": 1.6,
    "Эквадор": 1.1,
    "Кения": 1.0,
    "Колумбия": 1.1,
    "Индонезия": 1.0,
    "Сомали": 1.0,
    "Австралия": 1.2,
    "ЮАР": 1.2,
    "Чили": 1.3,
    "Аргентина": 1.3,
    "Новая Зеландия": 1.4,
}

ALLERGENS = ['Абрикосы', 'Авокадо', 'Айва', 'Ананас', 'Апельсин', 'Арбуз', 'Бананы', 'Брусника', 'Виноград', 'Вишня', 'Черника', 'Гранат', 'Грейпфрут', 'Груша', 'Ежевика', 'Инжир', 'Киви', 'Клубника', 'Клюква', 'Крыжовник', 'Курага', 'Лимон', 'Мандарин', 'Малина', 'Морошка', 'Облепиха', 'Персики', 'Слива', 'Смородина черная', 'Смородина красная', 'Смородина белая', 'Финики', 'Хурма', 'Черешня', 'Шиповник сухой', 'Яблоки', 'Базилик', 'Баклажаны', 'Горошек зеленый', 'Кабачки', 'Капуста белокочанная', 'Капуста цветная', 'Капуста брокколи', 'Картофель', 'Лук зеленый перьевой', 'Лук репчатый', 'Морковь', 'Огурец', 'Перец болгарский', 'Петрушка', 'Редис', 'Редька зелёная', 'Репа', 'Салат листовой', 'Шпинат', 'Свекла', 'Томаты', 'Тыква', 'Чеснок', 'Грибы белые', 'Горох цельный', 'Фасоль', 'Яйцо куриное', 'Чечевица', 'Морская капуста', 'Яйцо перепелиное', 'Горбуша', 'Икра красная', 'Кальмар', 'Карась', 'Карп', 'Креветка', 'Лещ', 'Семга', 'Минтай', 'Окунь речной', 'Осетр', 'Палтус', 'Скумбрия', 'Судак', 'Треска', 'Тунец', 'Щука', 'Форель свежая', 'Лосось', 'Баранина', 'Говядина', 'Говяжья печень', 'Говяжий язык', 'Индейка', 'Кролик', 'Гусь', 'Курица (грудка)', 'Куриная печень', 'Куриные сердечки', 'Свинина (вырезка)', 'Сердце свиное', 'Утка', 'Язык свиной', 'Брынза', 'Йогурт греческий', 'Кефир 3.2%', 'Молоко 3.2%', 'Сыр российский (50%)', 'Творог 5%', 'Булгур', 'Гречневая крупа', 'Овсянка', 'Миндаль', 'Шоколад горький 77%', 'Молоко сгущеное с сахаром', 'Ряженка 2.5%', 'Сливки 10%', 'Сливки 20%', 'Сметана 20%', 'Сыр плавленый', 'Сыр фета', 'Кукурузная крупа', 'Кус-кус', 'Манная крупа', 'Мука пшеничная', 'Перловая крупа', 'Рис', 'Хлеб пшеничный', 'Арахис', 'Грецкий орех', 'Кедровый орех', 'Кешью', 'Семя подсолнечника', 'Масло сливочное', 'Шоколад молочный', 'Сыр творожный', 'Ячневая крупа', 'Хлеб ржаной', 'Фисташки', 'Фундук', 'Горчица', 'Майонез', 'Кетчуп', 'Масло растительное', 'Масло оливковое']

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "countries": COUNTRIES, "allergens": ALLERGENS})

@app.post("/submit")
async def submit_form(
    request: Request,
    age: int = Form(...),
    height: int = Form(...),
    weight: int = Form(...),
    gender: str = Form(...),
    country: str = Form(...),
    lifestyle: str = Form(...),
    alcohol: bool = Form(False),
    tobacco: bool = Form(False),
    allergens: str = Form(""),
    budget: Optional[int] = Form(0)
):
    response = RedirectResponse(url="/submit", status_code=303)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    allergens_list = allergens.split(',') if allergens else []
    budget = budget if budget and budget > 0 else 0

    try:
        @timeout(90)
        def calculate_diet():
            data_c = pd.read_csv('Nutrienty8.csv', encoding='UTF-8', sep=';', decimal='.').values.tolist()
            data_p = pd.read_csv('Produkty8.csv', encoding='UTF-8', sep=';', decimal='.').values.tolist()

            if allergens_list:
                products_exclusion = set(allergens_list)
                data_p = [sublist for sublist in data_p if sublist[0] not in products_exclusion]

            if gender in gender_index:
                data_c = data_c[gender_index[gender]]

            activity_value = activity_values[lifestyle]
            if gender == Gender.FEMALE:
                kcal=round((10*weight+6.25*height-5*age-161)*activity_value, 2)
                water=weight*35*activity_value
            else:
                kcal=round((10*weight+6.25*height-5*age+5)*activity_value, 2)
                water=weight*31*activity_value

            if tobacco:
                data_c[8] += 35 # Витамин C

            if alcohol:
                data_c[1] *= 1.2 # Витамин B1
                data_c[4] *= 1.2 # Витамин B6
                data_c[14] *= 1.1 # Магний
                data_c[-10] *= 1.1 # Цинк 

            vitamin_d_factor = VITAMIN_D_FACTORS.get(country, 1.5)
            data_c[9] *= vitamin_d_factor # Витамин D в зависимости от страны

            proteins = round(kcal*0.2/4, 2) 
            fats=round(kcal*0.3/9, 2)
            carbs=round(kcal*0.5/4, 2)

            data_c.insert(1, carbs)
            data_c.insert(1, fats)
            data_c.insert(1, proteins)
            data_c.insert(1, kcal)

            #data_c.append(budget)

            #data_c.append(water)
             
            nutrients = data_c.copy()

            for p in data_p:
                p.pop(-1)

            # Запуск симплекс-метода

            print(data_p)
            print(data_c)

            symp = Symplex(data_p, data_c, cash=budget)
            symp.start()

            return symp, nutrients 

        # Вызываем функцию с таймаутом
        symp, nutrients = calculate_diet()

        plot_cash = symp.graphics_cash()
        plot_gramms = symp.graphics_gramms()

        sorted_products = dict(sorted(
            symp.products.items(),
            key=lambda item: item[1],
            reverse=True
        ))

        # Формирование результатов
        results = {
            "products": sorted_products,
            "total_cost": symp.result,
            "nutrient_factor": symp.cash_factor,
            "plot_cash": plot_cash,
            "plot_gramms": plot_gramms,
            "nutrients": nutrients,
        }

        # Передача результатов в шаблон
        return templates.TemplateResponse("results.html", {
            "request": request,
            "diet": results
        })

    except TimeoutError:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Расчет занял слишком много времени. Возможно, введенные вами данные еще не исследованы. Попробуйте другие параметры."
        })

    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка расчета: {str(e)}"
        })

