import sys
from typing import List, Tuple
import pandas as pd
import numpy as np
import csv
import matplotlib.pyplot as plt
import io
import base64

class Symplex:
    """Основной класс для реализации симплекс-метода"""

    class F_function:
        """Класс для представления целевой функции"""
        def default_init(self):
            self.free_axs: List[float] = []  # Коэффициенты при переменных в целевой функции
            self.maxmin: str = "min"  # Тип задачи (минимизация/максимизация)

        def __init__(self, free_axs=None, maxmin=None):
            if free_axs is None and maxmin is None:
                self.default_init()
            else:
                self.free_axs = free_axs
                self.maxmin = maxmin

    class Constraint:
        """Класс для представления ограничений"""
        def default_init(self):
            self.free_axs: List[float] = []  # Коэффициенты при переменных в ограничении
            self.b: float = 0  # Правая часть ограничения (bi)
            self.sign: str = "="  # Знак сравнения (<=, >=, =)

        def __init__(self, free_axs=None, sign=None, b=None):
            if free_axs is None and sign is None and b is None:
                self.default_init()
            else:
                self.free_axs = free_axs
                self.sign = sign
                self.b = b


    class Symplecs_table_row:
        """Класс для строки симплекс-таблицы"""
        def __init__(self):
            self.axs: List[float] = []  # Коэффициенты в строке таблицы
            self.b: float = 0  # Значение в столбце b
            self.xi: int = -1  # Индекс базисной переменной для этой строки

    def __init__(self, data_p, data_c, cash=None):
        """Инициализация основных переменных класса"""
        self.data_p = list(map(list, zip(*data_p)))
        self.data_c = data_c
        self.data_p_for_cash = list(map(list, zip(*data_p)))
        self.data_c_for_cash = data_c
        self.cash_factor = 1.0
        self.cash_bool = False
        self.cash = 0 if cash is None else cash
        self.constraint_list: List[Symplex.Constraint] = []  # Список ограничений
        self.constraint_count: int = len(self.data_c)-1  # Количество ограничений
        self.free_x_count: int = len(self.data_p[0])  # Количество свободных переменных
        self.Ffun_max_min: str = "min"  # Тип задачи (max/min)
        self.Ffun = self.F_function()  # Целевая функция
        self.result = 0
        self.products = {}
        self.products_cash = {}

    def print_symf(self, Ffun: F_function, constraint_list: List[Constraint]) -> None:
        """Вывод условий задачи (целевой функции и ограничений)"""
        print("---------")
        # Вывод целевой функции
        print(Ffun.free_axs)
        for ax in Ffun.free_axs:
            print(f"{ax:.2f}", end="\t")
        print(f"->\t{Ffun.maxmin}")

        # Вывод ограничений
        for con in constraint_list:
            for ax in con.free_axs:
                print(f"{ax:.2f}", end="\t")
            print(f"{con.sign}\t{con.b:.2f}")
        print("---------")

    def print_symt(self, symtable: List[Symplecs_table_row]) -> None:
        """Вывод симплекс-таблицы в удобном формате"""
        print("---------")
        ax_count = len(symtable[0].axs)
        # Заголовок таблицы
        print(" \t|\t", end="")
        for i in range(1, ax_count + 1):
            print(f"x{i}\t|\t", end="")
        print("b")

        # Разделительная линия
        print("—\t|\t", end="")
        for _ in range(ax_count):
            print("—\t|\t", end="")
        print("—")

        # Содержимое таблицы
        for symr in symtable:
            print(f"x{symr.xi+1}\t|\t", end="")
            for ax in symr.axs:
                print(f"{ax}\t|\t", end="")
            print(f"{symr.b}")
            print("---------")
        print("=======#|#|#|#=======")

    def raz_stolb_symt(self, symtable: List[Symplecs_table_row], max_min: str, symp_st_row: List[Tuple[int, int]]) -> int:
        """Нахождение разрешающего столбца в симплекс-таблице"""
        Ffun = symtable[-1]  # Берем последнюю строку (целевую функцию)
        '''
        if max_min == "max":
            raz_stolb = Ffun.axs.index(min(Ffun.axs))  # Для максимизации - минимальный элемент
        else:
            raz_stolb = Ffun.axs.index(max(Ffun.axs))  # Для минимизации - максимальный элемент
        '''
        delta_list = []
        for i in range(len(Ffun.axs)):
            delta = 0
            for j in range(len(symtable)-1):
                delta += Ffun.axs[symp_st_row[j][0]] * symtable[j].axs[i]
            delta -= Ffun.axs[i]
            delta_list.append(delta)


        if max_min == "max":
            raz_stolb = delta_list.index(min(delta_list))  # Для максимизации - минимальный элемент
        else:
            raz_stolb = delta_list.index(max(delta_list))  # Для минимизации - максимальный элемент


        #print(f"Разрешающий столбец - {raz_stolb+1}")
        return raz_stolb

    def raz_stroka_symt(self, symtable: List[Symplecs_table_row], raz_stolb: int,
                       symp_st_row: List[Tuple[int, int]], constraint_count: int) -> int:
        """Нахождение разрешающей строки в симплекс-таблице"""
        prirast = []
        for i in range(len(symtable)-1):
            if symtable[i].b >= 0 and symtable[i].axs[raz_stolb] > 0:
                raz_stroka_value = symtable[i].b / symtable[i].axs[raz_stolb]  # Вычисляем отношение
                if raz_stroka_value == 0:
                    prirast.append(float('inf'))
                else:
                    prirast.append(raz_stroka_value)
            else:
                prirast.append(float('inf'))

        raz_stroka = prirast.index(min(prirast))  # Берем минимальное отношение
        #print(f"Разрешающая строка - {raz_stroka+1}")
        symtable[raz_stroka].xi = raz_stolb
        symp_st_row.append((raz_stolb, raz_stroka))  # Запоминаем базис
        return raz_stroka

    def raz_stroka_symt_min(self, symtable: List[Symplecs_table_row]) -> int:
        """Нахождение строки с минимальным отрицательным b (для искусственного базиса)"""
        raz_stroka=0
        min_val=symtable[0].b
        for i in range(len(symtable)):
            if symtable[i].b < 0 and symtable[i].b < min_val and (
                    symtable[i].axs.count(1.0) == 1 and symtable[i].axs.count(0.0) == len(
                    symtable[i].axs) - 1) == False:
                min_val=symtable[i].b
                raz_stroka=i
        #print(f"Строка - {raz_stroka + 1} = {symtable[raz_stroka].b}")
        return raz_stroka

    def raz_stolb_symt_min(self, symtable: List[Symplecs_table_row], raz_stroka: int,
                          symp_st_row: List[Tuple[int, int]]) -> int:
        """Нахождение разрешающего столбца для строки с отрицательным b"""
        raz_stolb = 0
        cur_row = symtable[raz_stroka]
        min_val = cur_row.axs.index(max(cur_row.axs))
        for i in range(len(cur_row.axs)):
            if cur_row.axs[i] < min_val and cur_row.axs[i]!=0.0 and cur_row.axs[i]!=1.0:
                min_val = cur_row.axs[i]
                raz_stolb = i
        symtable[raz_stroka].xi = raz_stolb
        #print(f"Столбец - {raz_stolb+1} = {symtable[raz_stroka].axs[raz_stolb]}", "строк:", len(symtable))
        symp_st_row.append((raz_stolb, raz_stroka))  # Запоминаем базис
        return raz_stolb



    def gaus(self, symtable: List[Symplecs_table_row], raz_stolb: int,
            raz_stroka: int, make_last: bool) -> None:
        """Метод Гаусса для преобразования симплекс-таблицы"""

        def custom_round(num):
            if num == 0:
                return 0.0
            decimal_places=10
            rounded=round(num, decimal_places)
            while rounded == 0:
                decimal_places+=1
                rounded=round(num, decimal_places)
            return round(num, decimal_places) if rounded != 0 else 0.0

        cur_sym_el = symtable[raz_stroka]
        del_val = cur_sym_el.axs[raz_stolb]  # Разрешающий элемент

        # Нормировка разрешающей строки
        for i in range(len(cur_sym_el.axs)):
            cur_sym_el.axs[i] /= del_val
            cur_sym_el.axs[i] = custom_round(cur_sym_el.axs[i])
        cur_sym_el.b /= del_val
        cur_sym_el.b = custom_round(cur_sym_el.b)

        # Преобразование остальных строк
        symsize = len(symtable) if make_last else len(symtable)-1
        for i in range(symsize):
            if i != raz_stroka:
                cur_sym_el = symtable[i]
                del_val = -1.0 * cur_sym_el.axs[raz_stolb]
                for j in range(len(cur_sym_el.axs)):
                    cur_sym_el.axs[j] += del_val * symtable[raz_stroka].axs[j]
                    cur_sym_el.axs[j]=custom_round(cur_sym_el.axs[j])
                cur_sym_el.b += del_val * symtable[raz_stroka].b
                cur_sym_el.b=custom_round(cur_sym_el.b)

        for i in range(symsize):
            for j in range(len(cur_sym_el.axs)):
                cur_sym_el.axs[j]+=del_val * symtable[raz_stroka].axs[j]
                cur_sym_el.axs[i]=custom_round(cur_sym_el.axs[j])
            cur_sym_el.b+=del_val * symtable[raz_stroka].b
            cur_sym_el.b=custom_round(cur_sym_el.b)

    def min_Ffun_el_bigger_smaller_zero(self, FFfun: Symplecs_table_row, free_x_count: int,
                                      max_min: str, symtable: List[Symplecs_table_row],
                                      symp_st_row: List[Tuple[int, int]]) -> bool:
        """Проверка, есть ли в целевой строке отрицательные (для max) или положительные (для min) коэффициенты"""
        #deltal = []
        for i in range(len(FFfun.axs)):
            delta = 0
            for j in range(len(symtable)-1):
                delta += FFfun.axs[symp_st_row[j][0]] * symtable[j].axs[i]
            delta -= FFfun.axs[i]
            if delta > 0:
                #print(deltal)
                return True
        #print(deltal)
        return False

    def B_is_otrits(self, symtable: List[Symplecs_table_row]) -> bool:
        """Проверка, есть ли в столбце b отрицательные значения"""
        for row in symtable:
            if row.b < 0:
                if row.axs.count(1.0)==1 and row.axs.count(0.0)== len(row.axs)-1:
                    continue
                else:
                    return True
        return False

    def NOT_Have_Solution(self, symtable: List[Symplecs_table_row], Ffun_max_min: str) -> bool:
        """Проверка, что задача не имеет решения"""
        for j in range(len(symtable[-1].axs)):
            otriz_ax_count = 0
            if (Ffun_max_min == "max" and symtable[-1].axs[j] > 0) or (Ffun_max_min == "min" and symtable[-1].axs[j] < 0):
                for i in range(len(symtable)-1):
                    if symtable[i].axs[j] <= 0:
                        otriz_ax_count += 1
                if otriz_ax_count == len(symtable)-1:
                    return True
        return False

    def Result_Not_Exists(self, symtable: List[Symplecs_table_row], Ffun_max_min: str) -> None:
        """Завершение программы, если решение не существует"""
        if self.NOT_Have_Solution(symtable, Ffun_max_min):
            print("Задача не имеет решения")
            sys.exit(0)

    def Find_basis(self, symtable: List[Symplecs_table_row], symp_st_row: List[Tuple[int, int]],
                  constraint_count: int, Ffun_max_min: str) -> None:
        """Поиск начального базиса для симплекс-метода"""
        symp_st_row.clear()
        self.Result_Not_Exists(symtable, Ffun_max_min)

        # Поиск единичного базиса
        for j in range(len(symtable[-1].axs)):
            if len(symp_st_row) < constraint_count:
                stolb = []
                for i in range(len(symtable)-1):
                    stolb.append(symtable[i].axs[j])
                if stolb.count(1) == 1 and stolb.count(0) == constraint_count-1:
                    symp_st_row.append((j, stolb.index(1)))



        # Если базис не найден, строим его
        while len(symp_st_row) < constraint_count:
            self.Result_Not_Exists(symtable, Ffun_max_min)
            raz_stolb = self.raz_stolb_symt(symtable, Ffun_max_min, symp_st_row)
            raz_stroka = self.raz_stroka_symt(symtable, raz_stolb, symp_st_row, constraint_count)
            self.gaus(symtable, raz_stolb, raz_stroka, True)
            #self.print_symt(symtable)
            self.Result_Not_Exists(symtable, Ffun_max_min)


        # Сортируем базисные переменные
        symp_st_row.sort(key=lambda x: x[1])
        for i in range(len(symtable)-1):
            symtable[i].xi = symp_st_row[i][0]

    def graphics_cash(self):
        categories=[]
        values=[]
        colors=[]
        for product in self.products:
            categories.append(product)
            values.append(self.products_cash[product])
            colors.append('yellow')

        categories.append('сумма')
        values.append(self.result)
        colors.append('green')

        MAX_HEIGHT=40
        base_height=6
        dynamic_height=base_height * (1 + (max(values) / min(values)) ** 0.3)
        dynamic_height=min(dynamic_height, MAX_HEIGHT)

        fig, ax=plt.subplots(figsize=(len(categories) * 0.7, dynamic_height))

        bars=ax.bar(categories, values, color=colors)

        max_value=max(values)
        yticks=np.linspace(0, max_value, num=25)
        plt.yticks(yticks)

        plt.xticks(rotation=90, ha='right')
        plt.tight_layout()
        plt.xlabel('Продукты и итоговая сумма')
        plt.ylabel('Стоимость')

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)

        plot_data = base64.b64encode(buf.read()).decode("utf-8")
        return plot_data

    def graphics_gramms(self):
        categories = []
        values = []
        colors = []
        for product in self.products:
            categories.append(product)
            values.append(self.products[product])
            colors.append('yellow')

        MAX_HEIGHT=40  # Дюймов (не более 20)
        base_height=6
        dynamic_height=base_height * (1 + (max(values) / min(values)) ** 0.3)
        dynamic_height=min(dynamic_height, MAX_HEIGHT)  # Ограничиваем

        fig, ax=plt.subplots(figsize=(len(categories) * 0.7, dynamic_height))

        bars=ax.bar(categories, values, color=colors)

        max_value=max(values)
        yticks=np.linspace(0, max_value, num=25)
        plt.yticks(yticks)

        plt.xticks(rotation=90, ha='right')
        plt.tight_layout()
        plt.xlabel('Продукты')
        plt.ylabel('Количество в граммах')

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)

        plot_data = base64.b64encode(buf.read()).decode("utf-8")
        return plot_data

    def start(self) -> None:
        self.Ffun.free_axs=self.data_p[-1]
        for i in range(1, self.constraint_count + 1):
            con = self.Constraint(self.data_p[i], ">=", self.data_c[i])
            self.constraint_list.append(con)
        self.start2()

    def start1(self) -> None:
        self.constraint_list.clear()
        self.cash_factor = self.cash/self.result
        self.result = 0
        #print(self.cash_factor)
        #print(self.data_p_for_cash)
        self.Ffun.free_axs = self.data_p_for_cash[-1]
        for i in range(1, len(self.data_c_for_cash)):
            self.data_c_for_cash[i] *= self.cash_factor
            self.data_c_for_cash[i] = round(self.data_c_for_cash[i], 10)
        for i in range(1, self.constraint_count + 1):
            con = self.Constraint(self.data_p_for_cash[i], ">=", self.data_c_for_cash[i])
            self.constraint_list.append(con)
        self.start2()

    def start2(self):
        Ffun_ax = self.Ffun.free_axs.copy()
        # Приведение задачи к канонической форме
        basis_ax = []
        for con in self.constraint_list:
            con.free_axs.extend(basis_ax)
            if con.sign == ">=":
                con.free_axs.append(-1)  # Добавляем искусственную переменную
                con.sign = "="
                con.free_axs = [ax * -1 for ax in con.free_axs]  # Умножаем на -1
                con.b *= -1
                basis_ax.append(0)
            elif con.sign == "<=":
                con.free_axs.append(1)  # Добавляем дополнительную переменную
                con.sign = "="
                basis_ax.append(0)

        # Преобразование задачи максимизации в минимизацию
        if self.Ffun.maxmin == "max":
            self.Ffun.free_axs = [ax * -1 for ax in self.Ffun.free_axs]
            self.Ffun.maxmin = "min"

        # Добавление нулей для искусственных переменных в целевую функцию
        self.Ffun.free_axs.extend(basis_ax)
        x_count = len(self.Ffun.free_axs)
        for con in self.constraint_list:
            last_basis_ax = [0] * (x_count - len(con.free_axs))
            con.free_axs.extend(last_basis_ax)

        #self.print_symf(self.Ffun, self.constraint_list)

        # Создание симплекс-таблицы
        symp_st_row = []
        symtable = []
        for con in self.constraint_list:
            symtr = self.Symplecs_table_row()
            symtr.axs = con.free_axs
            symtr.b = con.b
            symtable.append(symtr)

        # Добавление целевой функции в таблицу
        symtr = self.Symplecs_table_row()
        symtr.axs = self.Ffun.free_axs
        symtr.b = 0
        symtr.xi = -1
        symtable.append(symtr)

        #self.print_symt(symtable)

        self.Find_basis(symtable, symp_st_row, self.constraint_count, self.Ffun_max_min)
        #Устранение отрицательных правых частей
        #print("\n=======Смотрим наличие отриц. b=====")
        while self.B_is_otrits(symtable):
            self.Result_Not_Exists(symtable, self.Ffun_max_min)
            raz_stroka = self.raz_stroka_symt_min(symtable)
            raz_stolb = self.raz_stolb_symt_min(symtable, raz_stroka, symp_st_row)
            self.gaus(symtable, raz_stolb, raz_stroka, False)
            #self.print_symt(symtable)
            self.Result_Not_Exists(symtable, self.Ffun_max_min)

        #Основное решение симплекс-метода
        #print("\n=======Решаем=====")
        while self.min_Ffun_el_bigger_smaller_zero(symtable[-1], self.free_x_count, self.Ffun_max_min, symtable, symp_st_row):
            self.Find_basis(symtable, symp_st_row, self.constraint_count, self.Ffun_max_min)
            self.Result_Not_Exists(symtable, self.Ffun_max_min)
            raz_stolb = self.raz_stolb_symt(symtable, self.Ffun_max_min, symp_st_row)
            raz_stroka = self.raz_stroka_symt(symtable, raz_stolb, symp_st_row, self.constraint_count)
            self.gaus(symtable, raz_stolb, raz_stroka, True)
            #self.print_symt(symtable)

        self.products={}
        self.products_cash={}
        # Вывод результатов
        for i in range(self.free_x_count):
            x_result = 0
            for st_row in symp_st_row:
                if i == st_row[0]:
                    self.result += symtable[st_row[1]].b * Ffun_ax[i]
                    self.products[self.data_p[0][i]]=symtable[st_row[1]].b
                    self.products_cash[self.data_p[0][i]]=symtable[st_row[1]].b * Ffun_ax[i]
                    #x_result = symtable[st_row[1]].b
                    break
            #print(f"x{i+1} = {x_result}")
        print(f"Результат: {abs(self.result)}")

        if self.result > self.cash and self.cash > 0 and self.cash_bool == False:
            #print(f"так как цена вышла больше положенной, придется немного уменьшить норму :(")
            self.cash_bool = True
            self.start1()
