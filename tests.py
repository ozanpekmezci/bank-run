from otree.api import Currency as c, currency_range
from . import views
from ._builtin import Bot
from .models import Constants


class PlayerBot(Bot):

    def play_round(self):
        yield (views.Join, {'join': 'Put money on bank'})
        yield (views.Withdraw, {'withdraw': c(42)})
        yield (views.Results)
