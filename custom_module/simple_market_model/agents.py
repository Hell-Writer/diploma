import mesa
import numpy as np


class Seller(mesa.Agent):

    def __init__(self, model):
        super().__init__(model)
        self.reserve = 0
        self.produce = 1
        self.sold_prev = 0
        self.sold_cur = 0
        self.price = 60
        self.price_prev = 50
        self.days_with_no_demand = 0

    def product(self, buyers_want_home=0):
        self.reserve += self.produce
        self.produce += min([buyers_want_home, 10]) - self.days_with_no_demand

        if self.price < self.price_prev and self.sold_cur > self.sold_prev:
            self.price_prev = self.price
            self.price += 5
        elif self.price > self.price_prev and self.sold_cur < self.sold_prev:
            self.price_prev = self.price
            self.price -= 5
        else:
            self.price_prev = self.price
            self.price += 1

        if self.produce < 0:
            self.produce = 0
        if buyers_want_home == 0:
            self.days_with_no_demand += 1
        if buyers_want_home > 0:
            self.days_with_no_demand = 0

        self.sold_prev = self.sold_cur
        self.sold_cur = 0

    def house_bought(self):
        self.reserve -= 1
        self.sold_cur += 1

    def calc_elasticity(self):
        try:
            e = ((self.sold_cur - self.sold_prev)/(self.sold_cur + self.sold_prev)
                 )/((self.price - self.price_prev)/(self.price + self.price_prev))
        except ZeroDivisionError:
            e = -1
        return e


class Buyer(mesa.Agent):

    def __init__(self, model):
        super().__init__(model)
        self.n_children = 0
        self.wage = np.random.random() * 10
        self.wealth = np.random.random() * 25 - 10
        self.will_to_buy = 0
        self.n_of_houses = 0

    def change_state(self):
        self.n_children += np.random.choice(a=[0, 1, 2], p=[0.8, 0.18, 0.02])
        self.wealth += self.wage
        self.wage += np.random.choice(a=[0, 1], p=[0.7, 0.3])  # promotion
        self.will_to_buy += (self.n_children + 1) / (self.n_of_houses + 1)

    def buy(self):
        seller = self.model.agents_by_type[Seller][0]
        if ((self.wealth - (20 - self.will_to_buy)*seller.price) > 1) and (self.wealth > seller.price):
            if seller.reserve > 2:
                self.wealth -= seller.price
                self.will_to_buy -= 100
                self.n_of_houses += 1
                seller.house_bought()  # Change seller's reserves
            else:
                self.model.buyers_want_home += 1

    def __str__(self):
        return 'buyer'
