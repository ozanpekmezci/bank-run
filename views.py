from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants


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
        if 2 <= self.round_number < self.session.config['number_rounds'] and self.player.in_all_rounds()[0].joined and self.session.vars.get("bankrupt",False) is False:
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
        if self.player.withdraw != c(0) and self.player.participant.vars.get("withdrew",False) is False:
            #self.session.vars["amount_of_players_withdrew"] += 1
            self.session.vars["total_money_withdrew"] += self.player.withdraw
            self.player.participant.vars["withdrew"] = True


class WithdrawWaitPage(WaitPage):
    def is_displayed(self):
        return 2 <= self.round_number < self.session.config['number_rounds'] and self.session.vars.get("bankrupt",False) is False

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
            'all_players_withdrew_situation': [ p.id_in_group for p in self.group.get_players() if p.participant.vars.get("withdrew",False)],
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
