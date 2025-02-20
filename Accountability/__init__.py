from otree.api import *
import random

class C(BaseConstants):
    NAME_IN_URL = 'accountability_game'
    PLAYERS_PER_GROUP = 3  # Incumbent, Voter, Challenger
    NUM_ROUNDS = 2  # Two-period game
    SHOCK_PROB = 0.5  # Probability of shock e = 1
    GOOD_TYPE_PROB = 0.5  # Probability that a politician is of good type
    RENT = 10  # Office rent for politicians
    COST = 6  # Policy cost for politicians

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    reelected = models.BooleanField(initial=True)  # Track if incumbent is reelected
    shock = models.BooleanField()  # Stochastic shock e = 0 or 1
    policy_outcome = models.IntegerField()  # Observed outcome = effort + shock
    
class Player(BasePlayer):
    role_choice = models.IntegerField(choices=[0, 1], label="Choose Action (0: Low Effort, 1: High Effort)")
    voter_decision = models.BooleanField(blank=True, label="Reelect the Incumbent?")
    payoff = models.CurrencyField()
    good_type = models.BooleanField()  # True if politician is of good type
    
    def role(self):
        if self.id_in_group == 1:
           return 'Incumbent'
        elif self.id_in_group == 2:
           return 'Voter'
        else:
           return 'Challenger'

def set_shock(group: Group):
    group.shock = random.random() < C.SHOCK_PROB

def assign_types(players):
    for player in players:
        if player.role() in ['Incumbent', 'Challenger']:
            player.good_type = random.random() < C.GOOD_TYPE_PROB

def set_policy_outcome(group: Group):
    players = group.get_players()
    incumbent = players[0]
    effort = incumbent.role_choice
    group.policy_outcome = effort + int(group.shock)

def set_payoffs(group: Group):
    players = group.get_players()
    incumbent = players[0]
    voter = players[1]
    challenger = players[2]
    
    if group.reelected:
        politician = incumbent
    else:
        politician = challenger
    
    effort = politician.role_choice
    
    if politician.good_type:
        politician.payoff = 10 * effort  # Good type benefits from effort
    else:
        politician.payoff = 5  # Bad type does not benefit from effort
    
    voter.payoff = 10 + 5 * group.policy_outcome  # Payoff depends on observed policy outcome

def set_voter_decision(group: Group):
    voter = group.get_players()[1]
    group.reelected = voter.voter_decision

class Decision(Page):
    form_model = 'player'
    form_fields = ['role_choice']
    
    def is_displayed(self):
        return self.player.role() in ['Incumbent', 'Challenger']
    
    def vars_for_template(self):
        return {'shock': self.group.shock}  # Show shock to the incumbent

class Voting(Page):
    form_model = 'player'
    form_fields = ['voter_decision']
    
    def is_displayed(self):
        return self.player.role() == 'Voter'
    
    def vars_for_template(self):
        return {'policy_outcome': self.group.policy_outcome}  # Voter observes policy outcome
    
    def before_next_page(self):
        set_voter_decision(self.group)

class Results(Page):
    def before_next_page(self):
        set_payoffs(self.group)

def before_session_starts(subsession: Subsession):
    for group in subsession.get_groups():
        set_shock(group)
        assign_types(group.get_players())
        set_policy_outcome(group)

def pages():
    return [Decision, Voting, Results]


page_sequence = [
    Introduction,
    Send,
    SendBackWaitPage,
    SendBack,
    ResultsWaitPage,
    Results,
]
