from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import logging
import random



author = 'Ozan Pekmezci'

doc = """
Bank run system for an IDP
"""


class Constants(BaseConstants):
    name_in_url = 'bank_run'
    players_per_group = None
    # TODO
    # unfortunately, number of rounds can't be dynamic as of version 1.1 of oTree http://otree.readthedocs.io/en/latest/models.html#constants
    # it can only be changed by modifying the next line
    num_rounds = 30
    # TODO
    # this could be done dynamically. However dynamic values are stored on "session" and the session can be only reached through "self.session"
    # http://otree.readthedocs.io/en/latest/conceptual_overview.html#what-is-self
    # to have a maximum value for the "withdraw" field of the "Player" model, we need to have reach session but session can only be reached from
    #methods like "set_payoffs" because they receive the variable self as a parameter.


class Subsession(BaseSubsession):
    #problem: this method is called at the beginning for every round: so dont't use variables that change during the game
    def before_session_starts(self):
        logging.warning(self.round_number)
        #Period 0
        if self.round_number == 1:
            logging.warning("round 1 ")
            self.session.vars["bankrupt"] = False
            self.session.vars["total_money_of_bank"] = c(0)
            self.session.vars["total_money_withdrew"] = c(0)
            self.session.vars["amount_of_players"] = len(self.get_players())
            for p in self.get_players():
                p.payoff = c(self.session.config['starting_money'])
                #p.participant.payoff = Constants.starting_money
                p.participant.vars["money_at_hand"] = c(self.session.config['starting_money'])
                p.participant.vars["money_at_bank"] = c(0)
                p.participant.vars["joined"] = False
                p.participant.vars["withdrew"] = False
        #Period 1
        if 2 <= self.round_number < self.session.config['number_rounds']:
            for p in self.get_players():
                rand = random.uniform(0, 1)
                if rand <= self.session.config['forced_withdraw_in_period1_percent']:
                    p.forced_withdraw = True

        if self.round_number >= 3:
            logging.warning("round 3 ")


class Group(BaseGroup):
    def set_payoffs(self):
        for p in self.get_players():
            if p.participant.vars.get("joined", False):
                if p.withdraw <= p.participant.vars["money_at_bank"]:
                    if p.forced_withdraw:
                        if p.withdraw <= self.session.config['forced_withdraw_in_period1_minimum_amount']:
                            p.withdraw = c(self.session.config['forced_withdraw_in_period1_minimum_amount'])

                    p.participant.vars["money_at_hand"] += p.withdraw
                    p.participant.vars["money_at_bank"] -= p.withdraw
                else:
                    p.participant.vars["money_at_hand"] += p.participant.vars["money_at_bank"]
                    p.participant.vars["money_at_bank"] = c(0)
                p.payoff = p.participant.vars.get("money_at_hand",0) + p.participant.vars.get("money_at_bank",0)

            else:
                p.payoff = c(self.session.config['starting_money'])

    def set_join(self):
        for p in self.get_players():
            if p.join == 'Put money on bank':
                p.joined = True
                p.participant.vars["joined"] = True
                p.participant.vars["money_at_bank"] = c(self.session.config['starting_money'])
                p.participant.vars["money_at_hand"] = c(0)
                p.payoff = p.participant.vars["money_at_bank"]
                self.session.vars["total_money_of_bank"] += p.participant.vars["money_at_bank"]
            elif p.join == 'Put money on a risk-free investment':
                p.joined = False
                p.participant.vars["joined"] = False
                p.participant.vars["money_at_hand"] = c(0)

    def set_bank(self):
        if self.session.vars.get("total_money_withdrew", c(0)) >=\
                (self.session.vars.get("total_money_of_bank", c(0)) * self.session.config['required_percent_for_bank_run']):
            self.session.vars["bankrupt"] = True
        if self.round_number != self.session.config['number_rounds'] and self.session.vars.get("bankrupt",False) is False:
            for p in self.get_players():
                if p.participant.vars.get("joined", False):
                    #if self.session.vars.get("bankrupt", False):
                     #   p.participant.vars["money_at_bank"] = 0
                    p.participant.vars["money_at_bank"] *= (1 + self.session.config['interest'])
                    #p.participant.vars["money_at_hand"] += p.participant.vars["money_at_bank"]
                    #p.participant.vars["money_at_bank"] = 0
                    #p.payoff = p.participant.vars.get("money_at_hand", 0)
                    p.payoff = p.participant.vars.get("money_at_hand", 0) + p.participant.vars.get("money_at_bank", 0)
                else:
                    p.payoff = c(self.session.config['starting_money'])
                    #p.participant.vars["money_at_hand"] = c(self.session.config['starting_money'])
        if self.session.vars.get("bankrupt",False) is True:
            for p in self.get_players():
                if p.participant.vars.get("joined", False):
                    p.participant.vars["money_at_bank"] = 0
                    p.payoff = p.participant.vars.get("money_at_hand", 0)
                else:
                    p.payoff = c(self.session.config['starting_money'])
        if self.round_number == self.session.config['number_rounds']:
            for p in self.get_players():
                if p.participant.vars.get("joined", False):
                    p.participant.vars["money_at_hand"] += p.participant.vars["money_at_bank"]
                    p.participant.vars["money_at_bank"] = 0
                    p.payoff = p.participant.vars.get("money_at_hand", 0)
                else:
                    p.payoff = c(self.session.config['starting_money'])
                    p.participant.vars["money_at_hand"] = c(self.session.config['starting_money'])







class Player(BasePlayer):
    join = models.CharField(
        choices=['Put money on bank', 'Put money on a risk-free investment'],
        widget=widgets.RadioSelect()
    )
    withdraw = models.CurrencyField(min=0)
    joined = models.BooleanField(initial=False)
    forced_withdraw = models.BooleanField(initial=False)
