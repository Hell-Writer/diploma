import mesa
import numpy as np
from .agents import Buyer, Seller, Government, House
from .settings import *
from math import floor


class WorldModel(mesa.Model):
    def __init__(self, num_buyers, seed=None, mortgage_rate=STARTING_MORTGAGE_RATE):
        super().__init__(seed=seed)
        self.num_buyers = num_buyers
        self.sorted_houses = None
        self.vacant_houses = None
        self.mortgage_rate = mortgage_rate
        self.youth_mortgage_rate = YOUTH_MORTGAGE_RATE
        self.family_mortgage_rate = FAMILY_MORTGAGE_RATE
        self.mortgages_bought = 0
        self.cash_bought = 0
        self.deaths = 0
        self.births = 0
        self.transfert_spending = 0
        self.mortgage_rates = []
        self.mortgage_durations = []

        # Создаём агентов
        Buyer.create_agents(model=self, n=num_buyers)
        House.create_agents(model=self, n=floor(num_buyers * STARTING_HOUSE_PER_PERSON), price=PRICE_START)
        Seller.create_agents(model=self, n=1)
        Government.create_agents(model=self, n=1)

        # Генерируем начальные условия
        self.agents_by_type[Buyer].do("generate_kids")
        self.agents_by_type[Buyer].do("generate_houses")
        self.agents_by_type[Buyer].do("generate_wealth")

        # Заново генерируем резервы застройщикам, т.к. в generate_houses раздали все дома
        House.create_agents(model=self, n=RESERVE_START, price=PRICE_START)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "acquired_homes": compute_acquired_homes,
                "existing_homes": compute_existing_homes,
                "demand": store_buyers_want_home,
                "sold_price": store_sold_price,
                "start_price": store_start_price,
                "reserve": store_reserve,
                "alt_reserve": store_alternative_reserve,
                "produce": store_product,
                "sold": store_sold,
                "population": compute_population,
                "fertility": compute_fertility,
                "average_age": compute_average_age,
                "average_wealth": compute_average_wealth,
                "highest_wealth": store_highest_wealth,
                "lowest_wealth": store_lowest_wealth,
                "cash_bought": store_cash_bought,
                "mortgages_bought": store_mortgages_bought,
                "births": store_births,
                "deaths": store_deaths,
                "hai": compute_hai,
                "pir": compute_pir,
                "government_reserve": store_government_reserves,
                "taxes": store_taxes,
                "transferts": store_transfert
            }
        )
        self.buyers_want_home = 0
    
    def update_world(self):
        vacant_houses = self.agents_by_type[House].select(lambda x: x.owner == 'developer')
        self.vacant_houses = vacant_houses
        self.sorted_houses = vacant_houses.sort(lambda x: x.price, ascending=True)
        self.buyers_want_home = 0
        self.mortgages_bought = 0
        self.cash_bought = 0
        self.deaths = 0
        self.births = 0
        self.transfert_spending = 0
        self.mortgage_rates = []

    def step(self):
        self.update_world()
        self.agents_by_type[Buyer].do("change_state")
        self.agents_by_type[Buyer].do("recieve_government_help")
        self.agents_by_type[Buyer].do("buy")
        self.agents_by_type[Seller].do(
            "product", buyers_want_home=self.buyers_want_home
        )
        self.agents_by_type[House].select(lambda x: x.owner == 'developer').do("add_month_without_buyer")
        self.datacollector.collect(self)

    def __str__(self):
        return 'Current world state (settings)'


def compute_acquired_homes(model):
    agent_homes = [len(agent.houses) for agent in model.agents_by_type[Buyer]]
    return sum(agent_homes)

def compute_existing_homes(model):
    return len(model.agents_by_type[House])


def compute_population(model):
    return len(model.agents_by_type[Buyer])


def compute_fertility(model):
    agent_fertility = [
        agent.n_children for agent in model.agents_by_type[Buyer]]
    return sum(agent_fertility)


def compute_average_age(model):
    agent_age = [agent.age for agent in model.agents_by_type[Buyer]]
    return np.mean(agent_age)


def compute_average_wealth(model):
    agent_wealth = [agent.wealth for agent in model.agents_by_type[Buyer]]
    return np.mean(agent_wealth)

# def compute_average_desired_price(model):
#    agent_desired_price = [agent.wealth for agent in model.agents_by_type[Buyer]]
#    return np.mean(agent_desired_price)

def compute_pir(model):
    agent_income = model.agents_by_type[Buyer].agg('wage', np.mean) + (model.transfert_spending/len(model.agents_by_type[Buyer]))
    price = model.agents_by_type[Seller][0].sold_price_history[-2]
    return price / (12 * agent_income)

def compute_hai(model):
    agent_income = model.agents_by_type[Buyer].agg('wage', np.mean) + (model.transfert_spending/len(model.agents_by_type[Buyer]))
    price = model.agents_by_type[Seller][0].sold_price_history[-2]
    avg_mortgage_rate = np.mean(model.mortgage_rates)
    monthly_mortgage_rate = avg_mortgage_rate/12
    mortgage_duration_avg = np.mean(model.mortgage_durations[-50:])
    mortgage_overpay_ratio = (
        monthly_mortgage_rate + 
        (monthly_mortgage_rate / ((1+monthly_mortgage_rate)**(mortgage_duration_avg) - 1))
    ) * mortgage_duration_avg
    return agent_income / ((1/0.35)*0.7*price*mortgage_overpay_ratio/mortgage_duration_avg)



def store_buyers_want_home(model):
    return model.buyers_want_home


def store_sold_price(model):
    # Здесь и далее индекс -2, потому что к моменту забора данных уже появились новые значения
    return model.agents_by_type[Seller][0].sold_price_history[-2]

def store_start_price(model):
    return model.agents_by_type[Seller][0].start_price_history[-1]


def store_reserve(model):
    return model.agents_by_type[Seller][0].reserve_history[-2]

def store_alternative_reserve(model):
    return len(model.sorted_houses)


def store_product(model):
    return model.agents_by_type[Seller][0].produce_history[-2]

def store_sold(model):
    return model.agents_by_type[Seller][0].sold_history[-2]

def store_highest_wealth(model):
    return max(model.agents_by_type[Buyer].get('wealth'))

def store_lowest_wealth(model):
    return min(model.agents_by_type[Buyer].get('wealth'))

def store_cash_bought(model):
    return model.cash_bought

def store_mortgages_bought(model):
    return model.mortgages_bought

def store_births(model):
    return model.births

def store_deaths(model):
    return model.deaths

def store_government_reserves(model):
    return model.agents_by_type[Government][0].money_reserve

def store_taxes(model):
    return model.agents_by_type[Government][0].taxes

def store_transfert(model):
    return model.transfert_spending
