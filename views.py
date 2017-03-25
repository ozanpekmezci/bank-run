from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import logging


class Join(Page):
    form_model = models.Player
    form_fields = ['join']
    timeout_seconds = 60
    timeout_submission = {'join': 'Put money on a risk-free investment'}

    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return{
            'starting_money': self.session.config['starting_money']
        }

    def before_next_page(self):
        pass


class JoinWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number == 1

    def after_all_players_arrive(self):
        self.group.set_join()


class Withdraw(Page):
    form_model = models.Player
    form_fields = ['withdraw']
    timeout_seconds = 60
    timeout_submission = {'withdraw': c(0)}

    def is_displayed(self):
        if 2 <= self.round_number < self.session.config['number_rounds'] and self.player.in_all_rounds()[0].joined:
            return True

    def vars_for_template(self):
        return{
            'money_at_hand': self.player.participant.vars.get("money_at_hand","0"),
            'money_at_bank': self.player.participant.vars.get("money_at_bank", "0"),
            'period': self.round_number-1,
            'forced_withdraw': self.player.forced_withdraw,
            'forced_withdraw_in_period1_minimum_amount': self.session.config['forced_withdraw_in_period1_minimum_amount']
        }

    def before_next_page(self):
        #only withdrawals of unique players are counted
        #TODO withdrew meselesi
        #TODO set_bank'te forced olanlar ne boh yiyecek
        #TODO forced ama o kadar parasi yoksa
        #TODO multiple round test, multiple withdraw test, son round olayini adam et ve onu da test et
        total_money_withdrew = self.session.vars.get("total_money_withdrew", c(0))
        total_money_of_bank = self.session.vars.get("total_money_of_bank", c(0))
        required_percent_for_bank_run = self.session.config['required_percent_for_bank_run']
        minimum_withdraw_amount = self.session.config['forced_withdraw_in_period1_minimum_amount']

        if self.player.forced_withdraw:
            if self.player.withdraw <= minimum_withdraw_amount:
                self.player.withdraw = c(minimum_withdraw_amount)

        if self.player.withdraw > self.player.participant.vars["money_at_bank"] :
            self.player.withdraw = self.player.participant.vars["money_at_bank"]

        if total_money_withdrew >= (total_money_of_bank * required_percent_for_bank_run):
            #already went bankrupt
            self.player.withdraw = c(0)
        elif (self.player.withdraw + total_money_withdrew) >= (total_money_of_bank * required_percent_for_bank_run):
            self.player.withdraw = total_money_of_bank * required_percent_for_bank_run - total_money_withdrew
            self.session.vars["bankrupt"] = True
        self.session.vars["total_money_withdrew"] += self.player.withdraw


class WithdrawWaitPage(WaitPage):
    def is_displayed(self):
        return 2 <= self.round_number < self.session.config['number_rounds']

    def after_all_players_arrive(self):
        self.group.set_payoffs()


class ResultsWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number >= 2

    def after_all_players_arrive(self):
        self.group.set_bank()


class Results(Page):
    def vars_for_template(self):
        return {
            'total_payoff': sum([p.payoff
                                 for p in self.player.in_all_rounds()]),
            'player_in_all_rounds': self.player.in_all_rounds(),
            'joined': self.player.in_all_rounds()[0].joined,
            'money_at_hand': self.player.participant.vars.get("money_at_hand","0"),
            'bankrupt': self.session.vars.get("bankrupt",False),
            'total_money_withdrew': self.session.vars.get("total_money_withdrew",c(0)),
            'end': self.round_number == self.session.config['number_rounds'] or self.session.vars.get("bankrupt",False) is True,
            'last_round': self.session.config['number_rounds'],
            'possible_to_watch_others': self.session.config['possible_to_watch_others'],
            'all_players': self.group.get_players(),
            'all_players_join_situation': [p.id_in_group for p in self.group.get_players() if p.in_all_rounds()[0].joined],
            'player_id': self.player.id_in_group,
        }


page_sequence = [
    Join,
    JoinWaitPage,
    Withdraw,
    WithdrawWaitPage,
    ResultsWaitPage,
    Results
]
