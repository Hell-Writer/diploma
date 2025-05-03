import mesa
from .agents import Buyer, Seller


class WorldModel(mesa.Model):
    def __init__(self, n, seed=None):
        super().__init__(seed=seed)
        self.num_agents = n
        # Create agents
        Buyer.create_agents(model=self, n=n)
        Seller.create_agents(model=self, n=1)
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "homes": compute_homes,
                "demand": store_buyers_want_home,
                "price": store_price,
                "reserve": store_reserve,
                "produce": store_product}
        )
        self.buyers_want_home = 0

    def step(self):
        self.buyers_want_home = 0
        self.agents_by_type[Buyer].do("change_state")
        self.agents_by_type[Buyer].do("buy")
        self.agents_by_type[Seller].do(
            "product", buyers_want_home=self.buyers_want_home)
        self.datacollector.collect(self)

    def __str__(self):
        return 'Current world state (settings)'


def compute_homes(model):
    agent_homes = [agent.n_of_houses for agent in model.agents_by_type[Buyer]]
    return sum(agent_homes)


def store_buyers_want_home(model):
    return model.buyers_want_home


def store_price(model):
    return model.agents_by_type[Seller][0].price


def store_reserve(model):
    return model.agents_by_type[Seller][0].reserve


def store_product(model):
    return model.agents_by_type[Seller][0].produce

# вдаыьпомываоьмдж
