import mesa
import numpy as np
from scipy.special import lambertw
from .settings import *
from math import floor

class Seller(mesa.Agent):

    def __init__(self, model):
        super().__init__(model)
        self.forecast_horizon = FORECAST_HORIZON

        self.reserve_history = [RESERVE_START]
        self.produce_history = [PRODUCE_START]
        self.produce_future = [PRODUCE_FUTURE_START for i in range(BUILD_SPEED)]
        self.sold_history = [SOLD_START]
        self.start_price_history = [PRICE_START]
        self.sold_price_history = [PRICE_START]
        self.current_prices = [PRICE_START]
        self.extra_demand_history = [EXTRA_DEMAND_START]

    def product(self, buyers_want_home=0):

        # Добавили цены
        if np.isnan(np.mean(self.current_prices)):
            self.sold_price_history.append(
                np.mean(self.sold_price_history[-1])
            )
        else:
            self.sold_price_history.append(
                np.mean(self.current_prices)
            )

        self.current_prices = []

        # Создали дом
        finished_production_amount = self.produce_future.pop(0)
        House.create_agents(
            model=self.model,
            n=finished_production_amount,
            price=FIRST_PRICE_MULT*np.mean(self.sold_price_history[-self.forecast_horizon:]))
        self.produce_history.append(finished_production_amount)
        self.reserve_history.append(finished_production_amount + self.reserve_history[-1])
        self.extra_demand_history.append(buyers_want_home)

        # Выбираем строительство через n периодов
        avg_extra_demand = np.mean(
            self.extra_demand_history[-self.forecast_horizon:])
        avg_produce = np.mean(self.produce_history[-self.forecast_horizon:])
        avg_sold = np.mean(self.sold_history[-self.forecast_horizon:])
        avg_start_price = np.mean(self.start_price_history[-self.forecast_horizon:])
        avg_sold_price = np.mean(self.sold_price_history[-self.forecast_horizon:])

        # self.produce_future.append(
        #    max(avg_extra_demand + avg_sold - avg_produce - np.mean(self.produce_future), 0)
        # )
        #self.produce_future.append(2)

        #self.produce_future.append(
        #    floor(
        #        max(
        #            (avg_extra_demand) + max(20 - avg_produce, 0),
        #            0
        #        )
        #    )
        #)
        #
        #n_buyers = len(self.model.agents_by_type[Buyer])
        #n_houses = len(self.model.agents_by_type[House])
        #surplus_speed = n_buyers // 200
        #added_surplus = int(avg_sold - self.reserve_history[-1])
        #n_new_houses = max(
        #    int(((n_buyers/n_houses) - 1) * surplus_speed) + (n_buyers // 1000)  + (added_surplus // 6) + np.random.randint(0,20),
        #    0
        #)
        #self.produce_future.append(n_new_houses)
        n_buyers = len(self.model.agents_by_type[Buyer])
        build_rate = int((15 + np.random.randint(0,5)) * (n_buyers/14600)) * 2 + int((avg_sold - self.reserve_history[-1])/14600)
        self.produce_future.append(build_rate)

        # Готовимся к продажам
        self.sold_history.append(0)

    def house_bought(self, price):
        self.reserve_history[-1] -= 1
        self.sold_history[-1] += 1
        self.current_prices.append(price)


class Buyer(mesa.Agent):

    def __init__(self, model, age=-1, n_children=-1):
        super().__init__(model)
        if n_children >= 0:
            self.n_children = n_children
        else:
            self.n_children = np.random.choice(a=[0,1,2], p=[0.7, 0.2, 0.1])
        self.kids_list = []
        self.additional_consumption = 0
        self.mortgage_monthly_payment = 0
        self.is_informed = np.random.choice(a=[False, True], p=[0.5, 0.5])
        self.wage = np.random.choice( # Данные из https://rosstat.gov.ru/folder/13397 "Распределение населения по интервальным группам среднедушевых денежных доходов"
                a=[
                    np.random.random() * 5000 + 5000,
                    np.random.random() * 4000 + 10000,
                    np.random.random() * 5000 + 14000,
                    np.random.random() * 8000 + 19000,
                    np.random.random() * 18000 + 27000,
                    np.random.random() * 15000 + 45000,
                    np.random.random() * 15000 + 60000,
                    np.random.random() * 15000 + 75000,
                    (np.random.chisquare(2) + 1) * 100000
                ],
                p=[
                    0.032,
                    0.047,
                    0.078,
                    0.138,
                    0.262,
                    0.144,
                    0.094,
                    0.091,
                    0.114
                ]
            )
        self.wealth = 0
        self.will_to_buy = 0
        self.houses = mesa.agent.AgentSet([]) # Мб данные тут удаляются. Следить пристально: https://mesa.readthedocs.io/latest/mesa.html#mesa.agent.AgentSet:~:text=The%20implementation%20uses%20a%20WeakKeyDictionary%20to%20store%20agents%2C%20which%20means%20that%20agents%20not%20referenced%20elsewhere%20in%20the%20program%20may%20be%20automatically%20removed%20from%20the%20AgentSet.
        if age == -1:
            self.age = np.random.randint(ADOLESCENCE_AGE, OLD_AGE)
        else:
            self.age = age

    def change_state(self):
        # Выход на работу и рождение детей
        if self.age > ADOLESCENCE_AGE:
            disposable_income = self.wage * (1 - INCOME_TAX)
            - AUTONOMOUS_CONSUMPTION
            - self.mortgage_monthly_payment
            self.model.agents_by_type[Government][0].taxes += self.wage * INCOME_TAX
            self.wealth += disposable_income - self.additional_consumption
            if self.age < CLIMAX_AGE:
                newborn = np.random.choice(a=[0, 1], p=[0.996, 0.004])
            else:
                newborn = 0
        else:
            newborn = 0

        # Добавляем детей
        if newborn > 0:
            self.kids_list.extend(
                list(
                    self.create_agents(
                        self.model,
                        n=newborn,
                        age=0,
                        n_children=0)))

        self.model.births += newborn
        self.n_children += newborn
        self.will_to_buy += (self.n_children + 1) / (len(self.houses) + 1)

        # Добавляем старение и смерть
        if self.age >= OLD_AGE:
            self.model.deaths += 1
            n_kids = len(self.kids_list)
            if n_kids > 0:  # Если дети есть - наследство им
                money_per_kid = self.wealth / n_kids
                houses_per_kid = len(self.houses) // n_kids
                houses_left = len(self.houses) % n_kids
                for kid in self.kids_list:
                    if houses_left > 0:
                        kid.recieve_inheritance(
                            money=money_per_kid, houses=self.houses[:houses_per_kid+1])
                    else:
                        kid.recieve_inheritance(
                            money=money_per_kid, houses=self.houses[:houses_per_kid])
                    houses_left -= 1
            else:  # Если детей нет - наследство передаётся государству
                self.model.agents_by_type[Government].do(
                    "get_lost_inheritance",
                    houses=self.houses,
                    wealth=self.wealth
                )
            self.remove()
        else:
            self.age += 1

    def generate_kids(self):
        # Генерируем детей при первичном прогоне
        self.kids_list = list(
            self.create_agents(
                self.model,
                n=self.n_children,
                age=np.random.randint(
                    0,
                    ADOLESCENCE_AGE),
                n_children=0))

    def generate_houses(self):
        # Генерируем дома при первичном прогоне
        # Работает только при STARTING_HOUSE_PER_PERSON от 0 до 1. Если нужно иначе, то придётся переписать
        vacant_houses = self.model.agents_by_type[House].select(
            lambda x: x.owner == 'developer'
        )
        if len(vacant_houses) > 0:
            self.houses.add(
                vacant_houses[0]
            )
            vacant_houses[0].owner = self.unique_id

    def generate_wealth(self):
        # Генерируем накопленное богатство при первичном прогоне
        self.wealth = np.random.random() * WEALTH_MULTIPLIER - WEALTH_DIMINISHER

    def recieve_inheritance(self, money, houses):
        # Получаем наследство
        self.wealth += money
        for house in houses:
            self.houses.add(house)
        mesa.agent.AgentSet(houses).do("change_owner", change=self.unique_id)

    def recieve_government_help(self):
        # Получаем поддержку от государства
        government = self.model.agents_by_type[Government][0]
        # Это немного случайный процесс. Кому-то повезёт, кому-то нет. Но в среднем все получат среднюю поддержку
        if (government.inheritant_income > TRANSFERT_AMOUNT) and ((self.wealth < 0) or (self.wage < 10**5)):
            self.wealth += TRANSFERT_AMOUNT
            government.inheritant_income -= TRANSFERT_AMOUNT
        if (len(government.houses) > 0) and (len(self.houses) == 0) and (self.age > ADOLESCENCE_AGE):
            self.houses.add(government.houses[0])
            government.houses.remove(government.houses[0])
        if (government.taxes > TRANSFERT_AMOUNT) and government.redistribution_mode and ((self.wealth < 0) or (self.wage < 5*10**5)):
        # Это немного случайный процесс. Кому-то повезёт, кому-то нет. Но в среднем все получат среднюю поддержку
            if self.wage < 10**5:
                self.wealth += 2*TRANSFERT_AMOUNT
                government.taxes -= 2*TRANSFERT_AMOUNT
                self.model.transfert_spending += 2*TRANSFERT_AMOUNT
            else:
                self.wealth += TRANSFERT_AMOUNT
                government.taxes -= TRANSFERT_AMOUNT
                self.model.transfert_spending += TRANSFERT_AMOUNT

    def select_desired_amount_alt(self, price):
        # TODO добавить первоначальный взнос в ипотеку
        # Функция полезности x^(кол-во детей)*y -> max
        remaining_life = OLD_AGE - self.age + 1 # +1 костыль, чтобы избегать ZeroDivisionError, когда чел умирает
        mortgage_duration = remaining_life # В будущем поменять
        disposable_income = self.wage * (1 - INCOME_TAX) - AUTONOMOUS_CONSUMPTION - self.mortgage_monthly_payment
        predicted_wealth = self.wealth + disposable_income * mortgage_duration
        mortgage_rates_list = [self.model.mortgage_rate]
        if self.age < YOUTH_AGE: # Молодёжная ипотека
            mortgage_rates_list.append(self.model.youth_mortgage_rate)
        if len(self.kids_list) >= KIDS_THRESHOLD: # Семейная ипотека
            mortgage_rates_list.append(self.model.family_mortgage_rate)
        selected_mortgage_rate = min(mortgage_rates_list)
        monthly_mortgage_rate = (1 + selected_mortgage_rate) ** (1/12) - 1
        household_size = self.n_children + 1 # Дети + один родитель
        if len(self.houses) == 0: # Если дома нет, то сильно увеличиваем его желание
            household_size += 10 
        mortgage_overpay_ratio = (
            monthly_mortgage_rate + 
            (monthly_mortgage_rate / ((1+monthly_mortgage_rate)**(mortgage_duration) - 1))
        ) * mortgage_duration
        desired_amount_cash = ( # Если покупка налом
            (self.wealth * household_size) /
            (price * lambertw(household_size*(self.wealth*np.e**(household_size))/price).real)
        ) # Аналитически вычесленная формула максимума для конкретной функции полезности
        desired_amount_mortgage = ( # Если покупка налом
            (predicted_wealth * household_size) /
            (price * (0.3 + 0.7*mortgage_overpay_ratio) * lambertw((household_size*predicted_wealth*np.e**household_size)/(price * (0.3 + 0.7*mortgage_overpay_ratio))).real)
        ) # Аналитически вычесленная формула максимума для конкретной функции полезности
        if desired_amount_cash > desired_amount_mortgage:
            desired_home_cost = np.floor(desired_amount_cash) * price
            if self.age > ADOLESCENCE_AGE: # Если человек взрослый, то он тратит на себя
                self.additional_consumption = (predicted_wealth - desired_home_cost) * MARGINAL_CONSUMPTION_RATE / OLD_AGE
            return ('cash', np.floor(desired_amount_cash), selected_mortgage_rate)
        else:
            desired_home_cost = np.floor(desired_amount_mortgage) * price * mortgage_overpay_ratio
            if self.age > ADOLESCENCE_AGE:
                self.additional_consumption = (predicted_wealth - desired_home_cost) * MARGINAL_CONSUMPTION_RATE / OLD_AGE
            return ('mortgage', np.floor(desired_amount_mortgage), selected_mortgage_rate)

    def buy(self):
        # Процесс покупки
        remaining_life = OLD_AGE - self.age + 1
        mortgage_duration = remaining_life
        government = self.model.agents_by_type[Government][0]
        if self.age < ADOLESCENCE_AGE: # Подростки не могут покупать
            return None
        if len(self.model.sorted_houses) > 0:
            if self.is_informed:
                house = self.model.sorted_houses[0]
            else:
                house = self.model.vacant_houses[0]
            seller = self.model.agents_by_type[Seller][0]
            buying_type, targeted_house_number, selected_mortgage_rate = self.select_desired_amount_alt(house.price)
        else:
            self.model.buyers_want_home += 1
            return None
        if targeted_house_number > len(self.houses):
            if buying_type == 'mortgage': # Если ипотека -  ежемесячно снимаем деньги
                monthly_mortgage_rate = (1 + selected_mortgage_rate) ** (1/12) - 1
                monthly_payment = (
                        monthly_mortgage_rate + 
                        (monthly_mortgage_rate / ((1+monthly_mortgage_rate)**(mortgage_duration) - 1))
                    ) * house.price * 0.7 # Ежемесячный платёж
                self.mortgage_monthly_payment += monthly_payment
                if (selected_mortgage_rate < self.model.mortgage_rate) or government.is_spending:
                    full_mortgage_rate = (government.mortgage_percent_help + (1+monthly_mortgage_rate)**12 )** (1/12) - 1 
                    full_payment = (
                        full_mortgage_rate + 
                        (full_mortgage_rate / ((1+full_mortgage_rate)**(mortgage_duration) - 1))
                    ) * house.price * 0.7
                    government.money_reserve -= (full_payment - monthly_payment) * mortgage_duration
                    self.model.program_spending += (full_payment - monthly_payment) * mortgage_duration
                self.wealth -= house.price * 0.3 # Первоначальный взнос
                self.model.mortgages_bought += 1
                self.model.mortgage_rates.append(selected_mortgage_rate)
                self.model.mortgage_durations.append(mortgage_duration)
            elif buying_type == 'cash': # Если налик - снимаем деньги разово
                self.wealth -= house.price
                self.model.cash_bought += 1
            self.houses.add(house)
            house.owner = self.unique_id  # Меняем владельца дома
            seller.house_bought(house.price)  # Изменяем резервы продавца
            self.model.sorted_houses.remove(house)
            self.model.vacant_houses.remove(house)


    def __str__(self):
        return 'buyer'


class Government(mesa.Agent):

    def __init__(self, model, money_reserve=0):
        super().__init__(model)
        self.money_reserve = money_reserve
        self.taxes = 0
        self.houses = mesa.agent.AgentSet([])
        self.inheritant_income = 0
        self.is_spending = False
        self.redistribution_mode = False
        self.mortgage_percent_help = 0
    
    def get_lost_inheritance(self, houses, wealth):
        self.inheritant_income += wealth
        for item in houses:
            self.houses.add(item)


class House(mesa.Agent):

    def __init__(self, model, price, owner='developer'):
        super().__init__(model)
        self.owner = owner
        self.months_without_buyer = 0
        self.price = price + (np.random.random()/5 - 0.1) * price
    
    def change_owner(self, change):
        # Менять владельца можно и без этой функции
        # Но с ней через self.do() легко обновлять владельца нескольких домов одновременно
        self.owner = change

    def add_month_without_buyer(self):
        # Менять дни без покупателя можно и без этой функции
        # Но с ней через self.do() легко делать это для нескольких домов одновременно
        self.months_without_buyer += 1
        if self.months_without_buyer > 2:
            self.price = max(0.95*self.price, MINIMUM_PRICE)