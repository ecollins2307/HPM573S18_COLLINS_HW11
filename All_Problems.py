# HW 11, All Problems
# requires newest version of SupportLib MarkovModel to be loaded in content root and  Anaconda to be installed locally and chosen as the interpreter

# Problem 1
print("Problem 1:", '\n')
# Part 1
print("Part 1:")
print("Annual rate of stroke associated mortality events, assuming exponential distribution: −ln(1−(36.2÷100000)) = 0.000362066")
print("Annual rate of non-stroke associated mortality events, assuming exponential distribution: −ln(1−(((18×100)−36.2)÷100000)) = 0.017795403", '\n')

# Part 2
print("Part 2:")
print("Annual rate of first-ever stroke events, assuming exponential distribution: −ln(1−(15÷1000)) = 0.015113638", '\n')

# Part 3
print("Part 3:")
print("Annual rate of transition from state “Well” to “Stroke”: 0.9×0.015113638 = 0.013602274")
print("Annual rate of transition from state “Well” to “Stroke Death”: 0.1×0.015113638 = 0.001511364", '\n')

# Part 4
print("Part 4:")
print("Annual rate of recurrent stroke events: −(1÷5)×ln(1−(17÷100)) = 0.037265916", '\n')

# Part 5
print("Part 5:")
print("Annual rate of transition from state “Post-Stroke” to “Stroke”: 0.8×0.037265916 = 0.029812733")
print("Annual rate of transition from state “Post-Stroke” to “Stroke Death”: 0.8×0.037265916 = 0.007453183", '\n')

# Part 6
print("Part 6:")
print("Annual rate of transition from state “Stroke”: 52", '\n')

# Complete matrix
print("Complete transition matrix:")
problem1transmat = [
    [0,  0.013602274,    0,    0.001511364, 0.017795403],   # WELL
    [0,     0,    52,    0, 0],   # STROKE
    [0,     0.029812733,     0,   0.007453183, 0.017795403],   # POSTSTROKE
    [0,     0,      0,   0, 0],   # STROKEDEATH
    [0,     0,      0,   0, 0],   # OTHERDEATH
    ]
print(problem1transmat, "\n")

# Problem 2
print("Problem 2:", '\n')
print("Complete transition matrix after adjustment for anticoagulation:")
problem2transmat = [
    [0,  0.013602274,    0,    0.001511364, 0.017795403],   # WELL
    [0,     0,    52,    0, 0],   # STROKE
    [0,     0.029812733,     0,   0.005589887, 0.018685173],   # POSTSTROKE
    [0,     0,      0,   0, 0],   # STROKEDEATH
    [0,     0,      0,   0, 0],   # OTHERDEATH
    ]
print(problem2transmat, '\n')

# Problem 3

# import required
import scr.MarkovClasses as MarkovCls
from enum import Enum
import scr.SamplePathClasses as PathCls
import scr.StatisticalClasses as StatCls
import scr.RandomVariantGenerators as rndClasses
import scr.FormatFunctions as F
import scr.StatisticalClasses as Stat
import scr.EconEvalClasses as Econ

# Parameter classes, modified from ParameterClasses.py from MarkovModel-ContinousTime branch
# Parameter classes, modified from ParameterClasses.py

class HealthStats(Enum):
    """ health states of patients """
    WELL = 0
    STROKE = 1
    POSTSTROKE = 2
    STROKEDEATH = 3
    OTHERDEATH = 4


class Therapies(Enum):
    """ none vs. anticoag therapy """
    NONE = 0
    ANTICOAG = 1

class _Parameters:

    def __init__(self, therapy):


        # selected therapy
        self._therapy = therapy

        # simulation time step
        self._delta_t = DELTA_T

        # calculate the adjusted discount rate
        self._adjDiscountRate = DISCOUNT * DELTA_T

        # initial health state
        self._initialHealthState = HealthStats.WELL

        # annual treatment cost
        if self._therapy == Therapies.NONE:
            self._annualTreatmentCost = COST_NONE
        else:
            self._annualTreatmentCost = COST_ANTICOAG

         # transition probability matrix of the selected therapy
        self._prob_matrix = []
        if therapy == Therapies.NONE:
            self._prob_matrix[:], p = MarkovCls.continuous_to_discrete(problem1transmat, DELTA_T)
        elif therapy == Therapies.ANTICOAG:
            self._prob_matrix[:], p = MarkovCls.continuous_to_discrete(problem2transmat, DELTA_T)

        # annual state costs and utilities
        self._annualStateCosts = []
        self._annualStateUtilities = []

    def get_initial_health_state(self):
        return self._initialHealthState

    def get_delta_t(self):
        return self._delta_t

    def get_adj_discount_rate(self):
        return self._adjDiscountRate

    def get_transition_prob(self, state):
        return self._prob_matrix[state.value]

    def get_annual_state_cost(self, state):
        if state == HealthStats.STROKEDEATH or state == HealthStats.OTHERDEATH:
            return 0
        else:
            return self._annualStateCosts[state.value]

    def get_annual_state_utility(self, state):
        if state == HealthStats.STROKEDEATH or state == HealthStats.OTHERDEATH:
            return 0
        else:
            return self._annualStateUtilities[state.value]

    def get_annual_treatment_cost(self):
        return self._annualTreatmentCost

class ParametersFixed(_Parameters):
    def __init__(self, therapy):

        # initialize the base class
        _Parameters.__init__(self, therapy)

        # annual state costs and utilities
        self._annualStateCosts = ANNUAL_STATE_COST
        self._annualStateUtilities = ANNUAL_STATE_UTILITY

# Markov classes, modified from MarkovModelClasses.py
class Patient:
    def __init__(self, id, parameters):
        """ initiates a patient
        :param id: ID of the patient
        :param parameters: parameter object
        """

        self._id = id
        # random number generator for this patient
        self._rng = None
        # parameters
        self._param = parameters
        # state monitor
        self._stateMonitor = PatientStateMonitor(parameters)
        # simulation time step
        self._delta_t = parameters.get_delta_t()

    def simulate(self, sim_length):
        """ simulate the patient over the specified simulation length """

        # random number generator for this patient
        self._rng = rndClasses.RNG(self._id)

        k = 0  # current time step

        # while the patient is alive and simulation length is not yet reached
        while self._stateMonitor.get_if_alive() and k*self._delta_t < sim_length:

            # find the transition probabilities of the future states
            trans_probs = self._param.get_transition_prob(self._stateMonitor.get_current_state())
            # create an empirical distribution
            empirical_dist = rndClasses.Empirical(trans_probs)
            # sample from the empirical distribution to get a new state
            # (returns an integer from {0, 1, 2, ...})
            new_state_index = empirical_dist.sample(self._rng)

            # update health state
            self._stateMonitor.update(k, HealthStats(new_state_index))

            # increment time step
            k += 1

    def get_survival_time(self):
        """ returns the patient's survival time"""
        return self._stateMonitor.get_survival_time()

    def get_time_to_STROKE(self):
        """ returns the patient's time to STROKE """
        return self._stateMonitor.get_time_to_STROKE()

    def get_total_discounted_cost(self):
        """ :returns total discounted cost """
        return self._stateMonitor.get_total_discounted_cost()

    def get_total_discounted_utility(self):
        """ :returns total discounted utility"""
        return self._stateMonitor.get_total_discounted_utility()

class PatientStateMonitor:
    """ to update patient outcomes (years survived, cost, etc.) throughout the simulation """
    def __init__(self, parameters):
        """
        :param parameters: patient parameters
        """
        self._currentState = parameters.get_initial_health_state() # current health state
        self._delta_t = parameters.get_delta_t()    # simulation time step
        self._survivalTime = 0          # survival time
        self._numberofstrokes = 0        # number of STROKE

        # monitoring cost and utility outcomes
        self._costUtilityOutcomes = PatientCostUtilityMonitor(parameters)

    def update(self, k, next_state):
        """
        :param k: current time step
        :param next_state: next state
        """

        # if the patient has died, do nothing
        if not self.get_if_alive():
            return

        # update survival time
        if next_state == HealthStats.STROKEDEATH or next_state == HealthStats.OTHERDEATH:
            self._survivalTime = (k)*self._delta_t  # removed the half-cycle effect

        # update time until STROKE
        if self._currentState != HealthStats.POSTSTROKE and next_state == HealthStats.POSTSTROKE:
            self._numberofstrokes = self._numberofstrokes + 1  # had a stroke

        # collect cost and utility outcomes
        self._costUtilityOutcomes.update(k, self._currentState, next_state)

        # update current health state
        self._currentState = next_state

    def get_if_alive(self):
        result = True
        if self._currentState == HealthStats.STROKEDEATH or self._currentState == HealthStats.OTHERDEATH:
            result = False
        return result

    def get_current_state(self):
        return self._currentState

    def get_survival_time(self):
        """ returns the patient survival time """
        # return survival time only if the patient has died
        if not self.get_if_alive():
            return self._survivalTime
        else:
            return None

    def get_time_to_STROKE(self):
        """ returns the number of strokes """
        # return number of strokes
        return self._numberofstrokes

    def get_total_discounted_cost(self):
        """ :returns total discounted cost """
        return self._costUtilityOutcomes.get_total_discounted_cost()

    def get_total_discounted_utility(self):
        """ :returns total discounted utility"""
        return self._costUtilityOutcomes.get_total_discounted_utility()

class PatientCostUtilityMonitor:
    def __init__(self, parameters):

        # model parameters for this patient
        self._param = parameters

        # total cost and utility
        self._totalDiscountedCost = 0
        self._totalDiscountedUtility = 0

    def update(self, k, current_state, next_state):
        """ updates the discounted total cost and health utility
        :param k: simulation time step
        :param current_state: current health state
        :param next_state: next health state
        """

        # update cost
        cost = 0.5 * (self._param.get_annual_state_cost(current_state) +
                      self._param.get_annual_state_cost(next_state)) * self._param.get_delta_t()
        # update utility
        utility = 0.5 * (self._param.get_annual_state_utility(current_state) +
                         self._param.get_annual_state_utility(next_state)) * self._param.get_delta_t()

         # add the cost of treatment
        # if DEATH will occur
        if next_state in [HealthStats.STROKEDEATH] or next_state in [HealthStats.OTHERDEATH] and current_state in [HealthStats.POSTSTROKE]:
            cost += 0.5 * self._param.get_annual_treatment_cost() * self._param.get_delta_t()
        elif next_state in [HealthStats.STROKE] and (current_state in [HealthStats.POSTSTROKE] or current_state in [HealthStats.WELL]):
            cost += 5000
        elif current_state in [HealthStats.POSTSTROKE]:
            cost += 1 * self._param.get_annual_treatment_cost() * self._param.get_delta_t()

         # update total discounted cost and utility (removed the half-cycle effect)
        self._totalDiscountedCost += \
            Econ.pv(cost, self._param.get_adj_discount_rate() / 2, k + 1)
        self._totalDiscountedUtility += \
            Econ.pv(utility, self._param.get_adj_discount_rate() / 2, k + 1)

    def get_total_discounted_cost(self):
        """ :returns total discounted cost """
        return self._totalDiscountedCost

    def get_total_discounted_utility(self):
        """ :returns total discounted utility"""
        return  self._totalDiscountedUtility

class Cohort:
    def __init__(self, id, therapy):
        """ create a cohort of patients
        :param id: an integer to specify the seed of the random number generator
        """
        self._initial_pop_size = POP_SIZE
        self._patients = []      # list of patients

        # populate the cohort
        for i in range(self._initial_pop_size):
            # create a new patient (use id * pop_size + i as patient id)
            patient = Patient(id * self._initial_pop_size + i, ParametersFixed(therapy))
            # add the patient to the cohort
            self._patients.append(patient)

    def simulate(self):
        """ simulate the cohort of patients over the specified number of time-steps
        :returns outputs from simulating this cohort
        """
        # simulate all patients
        for patient in self._patients:
            patient.simulate(SIM_LENGTH)

        # return the cohort outputs
        return CohortOutputs(self)

    def get_initial_pop_size(self):
        return self._initial_pop_size

    def get_patients(self):
        return self._patients

class CohortOutputs:
    def __init__(self, simulated_cohort):
        """ extracts outputs from a simulated cohort
        :param simulated_cohort: a cohort after being simulated
        """

        self._survivalTimes = []        # patients' survival times
        self._times_to_STROKE = []        # patients' times to STROKE
        self._costs = []                # patients' discounted total costs
        self._utilities =[]             # patients' discounted total utilities

    # survival curve
        self._survivalCurve = \
            PathCls.SamplePathBatchUpdate('Population size over time', id, simulated_cohort.get_initial_pop_size())

        # find patients' survival times
        for patient in simulated_cohort.get_patients():
            # get the patient survival time
            survival_time = patient.get_survival_time()
            if not (survival_time is None):
                self._survivalTimes.append(survival_time)           # store the survival time of this patient
                self._survivalCurve.record(survival_time, -1)       # update the survival curve

            # get the patient's time to STROKE
            time_to_STROKE = patient.get_time_to_STROKE()
            self._times_to_STROKE.append(time_to_STROKE)

            # cost and utility
            self._costs.append(patient.get_total_discounted_cost())
            self._utilities.append(patient.get_total_discounted_utility())

         # summary statistics
        self._sumStat_survivalTime = StatCls.SummaryStat('Patient survival time', self._survivalTimes)
        self._sumState_timeToSTROKE = StatCls.SummaryStat('Average number of strokes', self._times_to_STROKE)
        self._sumStat_cost = StatCls.SummaryStat('Patient discounted cost', self._costs)
        self._sumStat_utility = StatCls.SummaryStat('Patient discounted utility', self._utilities)

    def get_survival_times(self):
        return self._survivalTimes

    def get_times_to_STROKE(self):
        return self._times_to_STROKE

    def get_costs(self):
        return self._costs

    def get_utilities(self):
        return self._utilities

    def get_sumStat_survival_times(self):
        return self._sumStat_survivalTime

    def get_sumStat_time_to_STROKE(self):
        return self._sumState_timeToSTROKE

    def get_sumStat_discounted_cost(self):
        return self._sumStat_cost

    def get_sumStat_discounted_utility(self):
        return self._sumStat_utility

    def get_survival_curve(self):
        return self._survivalCurve

# Markov support functions, based on SupportMarkovModel.py
def print_outcomes(simOutput, therapy_name):
    """ prints the outcomes of a simulated cohort
    :param simOutput: output of a simulated cohort
    :param therapy_name: the name of the selected therapy
    :param Problem7: is this for problem 7?
    """
    # mean and confidence interval text of patient survival time
    survival_mean_CI_text = F.format_estimate_interval(
        estimate=simOutput.get_sumStat_survival_times().get_mean(),
        interval=simOutput.get_sumStat_survival_times().get_t_CI(alpha=ALPHA),
        deci=2)

    # mean and confidence interval text of time to STROKE
    time_to_STROKE_death_CI_text = F.format_estimate_interval(
        estimate=simOutput.get_sumStat_time_to_STROKE().get_mean(),
        interval=simOutput.get_sumStat_time_to_STROKE().get_t_CI(alpha=ALPHA),
        deci=2)

    # mean and confidence interval text of discounted total cost
    cost_mean_CI_text = F.format_estimate_interval(
        estimate=simOutput.get_sumStat_discounted_cost().get_mean(),
        interval=simOutput.get_sumStat_discounted_cost().get_t_CI(alpha=ALPHA),
        deci=0,
        form=F.FormatNumber.CURRENCY)

    # mean and confidence interval text of discounted total utility
    utility_mean_CI_text = F.format_estimate_interval(
        estimate=simOutput.get_sumStat_discounted_utility().get_mean(),
        interval=simOutput.get_sumStat_discounted_utility().get_t_CI(alpha=ALPHA),
        deci=2)

        # print outcomes
    print(therapy_name)
    print("  Estimate of discounted cost and {:.{prec}%} confidence interval:".format(1 - ALPHA, prec=0),
          cost_mean_CI_text)
    print("  Estimate of discounted utility and {:.{prec}%} confidence interval:".format(1 - ALPHA, prec=0),
          utility_mean_CI_text)
    print("")

# Functions modified from SupportMarkovModel.py
def print_comparative_outcomes(simOutputs_mono, simOutputs_combo):
    """ prints average increase in survival time, discounted cost, and discounted utility
    under combination therapy compared to mono therapy
    :param simOutputs_mono: output of a cohort simulated under mono therapy
    :param simOutputs_combo: output of a cohort simulated under combination therapy
    """

    # increase in survival time under combination therapy with respect to mono therapy
    increase_survival_time = Stat.DifferenceStatIndp(
        name='Change in number of strokes',
        x=simOutputs_combo.get_times_to_STROKE(),
        y_ref=simOutputs_mono.get_times_to_STROKE())

    # estimate and CI
    estimate_CI = F.format_estimate_interval(
        estimate=increase_survival_time.get_mean(),
        interval=increase_survival_time.get_t_CI(alpha=ALPHA),
        deci=2)
    print("Average change in number of strokes "
          "and {:.{prec}%} confidence interval:".format(1 - ALPHA, prec=0),
          estimate_CI)

    # increase in discounted total cost under combination therapy with respect to mono therapy
    increase_discounted_cost = Stat.DifferenceStatIndp(
        name='Increase in discounted cost',
        x=simOutputs_combo.get_costs(),
        y_ref=simOutputs_mono.get_costs())

    # estimate and CI
    estimate_CI = F.format_estimate_interval(
        estimate=increase_discounted_cost.get_mean(),
        interval=increase_discounted_cost.get_t_CI(alpha=ALPHA),
        deci=0,
        form=F.FormatNumber.CURRENCY)
    print("Average increase in discounted cost "
          "and {:.{prec}%} confidence interval:".format(1 - ALPHA, prec=0),
          estimate_CI)

    # increase in discounted total utility under combination therapy with respect to mono therapy
    increase_discounted_utility = Stat.DifferenceStatIndp(
        name='Increase in discounted cost',
        x=simOutputs_combo.get_utilities(),
        y_ref=simOutputs_mono.get_utilities())

    # estimate and CI
    estimate_CI = F.format_estimate_interval(
        estimate=increase_discounted_utility.get_mean(),
        interval=increase_discounted_utility.get_t_CI(alpha=ALPHA),
        deci=2)
    print("Average increase in discounted utility "
          "and {:.{prec}%} confidence interval:".format(1 - ALPHA, prec=0),
          estimate_CI)

def report_CEA(simOutputs_mono, simOutputs_combo):
    """ performs cost-effectiveness analysis
    :param simOutputs_mono: output of a cohort simulated under mono therapy
    :param simOutputs_combo: output of a cohort simulated under combination therapy
    """

    # define two strategies
    mono_therapy_strategy = Econ.Strategy(
        name='WITHOUT anticoagulation',
        cost_obs=simOutputs_mono.get_costs(),
        effect_obs=simOutputs_mono.get_utilities()
    )
    combo_therapy_strategy = Econ.Strategy(
        name='WITH anticoagulation',
        cost_obs=simOutputs_combo.get_costs(),
        effect_obs=simOutputs_combo.get_utilities()
    )

    # CEA
    CEA = Econ.CEA(
            strategies=[mono_therapy_strategy, combo_therapy_strategy],
            if_paired=False
    )
    # show the CE plane
    CEA.show_CE_plane(
        title='Problem 4: Cost-Effectiveness Analysis',
        x_label='Additional discounted utility',
        y_label='Additional discounted cost',
        show_names=True,
        show_clouds=True,
        show_legend=True,
        figure_size=6,
        transparency=0.3
    )
    # report the CE table
    CEA.build_CE_table(
        interval=Econ.Interval.CONFIDENCE,
        alpha=ALPHA,
        cost_digits=0,
        effect_digits=2,
        icer_digits=2,
    )

def report_CBA(simOutputs_mono, simOutputs_combo):
    """ performs cost-effectiveness analysis
    :param simOutputs_mono: output of a cohort simulated under mono therapy
    :param simOutputs_combo: output of a cohort simulated under combination therapy
    """

    # define two strategies
    mono_therapy_strategy = Econ.Strategy(
        name='WITHOUT anticoagulation',
        cost_obs=simOutputs_mono.get_costs(),
        effect_obs=simOutputs_mono.get_utilities()
    )
    combo_therapy_strategy = Econ.Strategy(
        name='WITH anticoagulation',
        cost_obs=simOutputs_combo.get_costs(),
        effect_obs=simOutputs_combo.get_utilities()
    )
    # CBA
    NBA = Econ.CBA(
            strategies=[mono_therapy_strategy, combo_therapy_strategy],
            if_paired=False
    )
    # show the net monetary benefit figure
    NBA.graph_deltaNMB_lines(
        min_wtp=0,
        max_wtp=50000,
        title='Problem 4: Cost-Benefit Analysis',
        x_label='Willingness-to-pay for one additional QALY ($)',
        y_label='Incremental Net Monetary Benefit ($)',
        interval=Econ.Interval.CONFIDENCE,
        show_legend=True,
        figure_size=6
    )

# simulation settings
POP_SIZE = 2000     # cohort population size
SIM_LENGTH = 15    # length of simulation (years)
ALPHA = 0.05        # significance level for calculating confidence intervals
DELTA_T = 1/52     # years
DISCOUNT = 0.03     # annual discount rate
COST_ANTICOAG = 550 # annual cost of anticoag treatment
COST_NONE = 0

# annual cost of each health state
ANNUAL_STATE_COST = [
    0.0,   # WELL
    0.0,   # STROKE
    200.0   # POSTSTROKE
    ]

# annual health utility of each health state
ANNUAL_STATE_UTILITY = [
    1.0,   # CD4_200to500
    0.2,   # STROKE
    0.9,   # POSTSTROKE
    ]

# run simulations
# create a cohort
notreatment = Cohort(
    id=0,
    therapy=Therapies.NONE)
# simulate the cohort
notreatmentOutputs = notreatment.simulate()
# create a cohort
treatment = Cohort(
    id=1,
    therapy=Therapies.ANTICOAG)
# simulate the cohort
treatmentOutputs = treatment.simulate()
# Output the required information
print("Problems 3 and 4:")
print("")
print_outcomes(notreatmentOutputs, 'WITHOUT anticoagulation')
print_outcomes(treatmentOutputs, 'WITH anticoagulation')
