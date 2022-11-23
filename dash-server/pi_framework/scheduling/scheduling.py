#!/usr/bin/env python3
"""
Framework for SINFONIES - Scheduling test case
"""

from datetime import datetime
import os
from pathlib import Path as P
import sys
import traceback

import cloudpickle as dill
#import dill
import numpy as np
import matplotlib.pyplot as plt
from numpy.core.fromnumeric import product
from numpy.lib.function_base import iterable
# from pyomo.core.base.set import BoundsInitializer

import pyomo.environ as pyo
import pprint

# pylint: disable=function-redefined


# Generate Model
def scheduling(param, processes, buckets, model=None):
    if model == None:
        model = pyo.ConcreteModel('Scheduling - Demo')

    model.sched = pyo.Block()
    ms = model.sched


    nt = param['nt']
    ### Common components ###

    # Sets
    ms.set_t = pyo.Set(initialize=range(nt))
    ms.set_te = pyo.Set(initialize=range(nt + 1))

    ms.set_proc = pyo.Set(initialize=processes.keys())
    ms.set_buckets = pyo.Set(initialize=buckets.keys())

    # Variables
    ms.var_proc_start = pyo.Var(ms.set_proc, ms.set_t, domain=pyo.Binary, initialize=0)
    ms.var_proc_active = pyo.Var(ms.set_proc, ms.set_t, domain=pyo.NonNegativeReals, bounds=(0,1), initialize=0)

    ms.var_bucket_in = pyo.Var(ms.set_buckets, ms.set_te, domain=pyo.NonNegativeReals, initialize=0)
    ms.var_bucket_out = pyo.Var(ms.set_buckets, ms.set_te, domain=pyo.NonNegativeReals, initialize=0)

    ms.var_bucket_insum = pyo.Var(ms.set_buckets, ms.set_te, domain=pyo.NonNegativeReals, initialize=0)
    ms.var_bucket_outsum = pyo.Var(ms.set_buckets, ms.set_te, domain=pyo.NonNegativeReals, initialize=0)
    ms.var_bucket_soc = pyo.Var(ms.set_buckets, ms.set_te, domain=pyo.Reals, initialize=0)

    # Constraints

    ## Process activity
    def con_rule(m, p, t):
        duration = processes[p]['duration']
        lhs = ms.var_proc_active[p, t]
        rhs = sum(ms.var_proc_start[p, i] for i in range(max(0,t+1-duration), t+1)) # off-by-one errors are hard
        return lhs == rhs
    ms.con_proc_active = pyo.Constraint(ms.set_proc, ms.set_t, rule=con_rule)

    ## Do not start unfinishable processes
    def con_rule(m, p, t):
        duration = processes[p]['duration']
        if t + duration > nt: # those off-by-one errors again
            return ms.var_proc_start[p, t] == 0
        return pyo.Constraint.Skip
    ms.con_proc_finish = pyo.Constraint(ms.set_proc, ms.set_t, rule=con_rule)

    ## Activity count
    def con_rule(m, p):
        activity = processes[p]['activity']
        a_count = activity.get('count')

        expr = sum(ms.var_proc_start[p,i] for i in ms.set_t)

        if a_count is not None:
            return expr == a_count
        else:
            a_count_min = activity.get('count_min')
            a_count_max = activity.get('count_max')
            return (a_count_min, expr, a_count_max)
    ms.con_activity_count = pyo.Constraint(ms.set_proc, rule=con_rule)


    ## Direct time constraints
    allowed_starts = {}
    for k,process in processes.items():
        duration = process['duration']
        constr_time= process['constraint_time']

        start_at = constr_time.get('start_at')
        start_after = constr_time.get('start_after')
        start_before = constr_time.get('start_before')
        finish_after = constr_time.get('finish_after')
        finish_before = constr_time.get('finish_before')

        if start_at is not None:
            it = safe_iter(start_at)
            allowed_start = [False] * nt
            for i in it:
                allowed_start[i] = True

        elif (start_after is not None or start_before is not None or
            finish_after is not None or finish_before is not None):
            
            allowed_start = [True] * nt

            if start_after is not None:
                for idx in range(start_after):
                    allowed_start[idx] = False

            if start_before is not None:
                for idx in range(start_after, nt):
                    allowed_start[idx] = False

            if finish_after is not None:
                for idx in range(finish_after-duration):
                    allowed_start[idx] = False

            if finish_before is not None:
                for idx in range(finish_before-duration, nt):
                    allowed_start[idx] = False

        else:
            allowed_start = [True] * nt

            ### TODO: implement multiple start/end
            # def safe_next(itx, nextx):
            #     try:
            #         x = next(itx)
            #     except StopIteration:
            #         x = None
            #         nextx = False
            #     return x, nextx

            # ita = safe_iter(start_after)
            # itb = safe_iter(start_before)
            # nexta, nextb = True, True

            # while nexta or nextb:
            #     a, nexta = safe_next(ita)
            #     b, nextb = safe_next(itb)

            #     if a is not None:
            #         allowed_start[:a]

        allowed_starts[k] = allowed_start

    def con_rule(m, p, t):
        allowed_start = allowed_starts[p]

        if allowed_start[t] == False:
            return ms.var_proc_start[p,t] == 0
        else:
            return pyo.Constraint.Skip
    ms.con_activity_time = pyo.Constraint(ms.set_proc, ms.set_t, rule=con_rule)


    ## Bucket constraints

    def bucket_inout(inout):
        def con_rule(m, b, t):
            if inout == 'in':
                lhs = ms.var_bucket_in[b, t]
            elif inout == 'out':
                lhs = ms.var_bucket_out[b, t]
            else:
                raise RuntimeError("You should call this with 'in' or 'out' as argument.")
            
            rhs = 0

            for p,process in processes.items():
                process_buckets = process.get('constraint_buckets')

                start_end = (
                    ('at_start', t),
                    ('at_end', t - process['duration']) # prone for off-by-one errors, should by okay
                )
                for index, ti in start_end:
                    if process_buckets is None or not process_buckets.get(index):
                        # No bucket links defined (not at all, or not for start/end)
                        continue
                    if ti < 0 or ti >= nt:
                        # Time index out of range for current start
                        continue
                    for pbi in process_buckets.get(index):
                        if pbi['bucket'] == b:
                            # If specified for current bucket
                            if pbi['change'] > 0 and inout == 'in':
                                # postive change and currently running for in variable
                                rhs += pbi['change'] * ms.var_proc_start[p, ti]
                            elif pbi['change'] < 0 and inout == 'out':
                                # negative change and currently running for out variable
                                rhs -= pbi['change'] * ms.var_proc_start[p, ti]
            return lhs == rhs
        return con_rule

    ms.con_bucket_in = pyo.Constraint(ms.set_buckets, ms.set_te, rule=bucket_inout('in'))
    ms.con_bucket_out = pyo.Constraint(ms.set_buckets, ms.set_te, rule=bucket_inout('out'))

    ## Buckets: in, out, SoC
    def bucket_cumsum_gen(var, var_plus=None, var_minus=None):
        def bucket_cumsum(m, b, t):
            lhs = var[b, t]
            rhs = 0

            if var_plus:
                rhs += sum(var_plus[b, i] for i in range(t+1))

            if var_minus:
                rhs -= sum(var_minus[b, i] for i in range(t+1))

            return lhs == rhs
        return bucket_cumsum

    ms.con_bucket_insum = pyo.Constraint(ms.set_buckets, ms.set_te,
        rule=bucket_cumsum_gen(ms.var_bucket_insum, ms.var_bucket_in))
    ms.con_bucket_outsum = pyo.Constraint(ms.set_buckets, ms.set_te,
        rule=bucket_cumsum_gen(ms.var_bucket_outsum, ms.var_bucket_out))
    ms.con_bucket_soc = pyo.Constraint(ms.set_buckets, ms.set_te,
        rule=bucket_cumsum_gen(ms.var_bucket_soc, ms.var_bucket_in, ms.var_bucket_out))

    ## Buckets: min, max, end
    def con_rule(m, b, t):
        bucket = buckets[b]

        b_min = bucket.get('value_min')
        b_max = bucket.get('value_max')
        b_end = bucket.get('value_end')

        if t == nt and b_end is not None:
            lb, ub = b_end, b_end
        else:
            lb, ub = b_min, b_max

        return (lb, ms.var_bucket_soc[b, t], ub)

    ms.con_bucket_minmax = pyo.Constraint(ms.set_buckets, ms.set_te, rule=con_rule)
    
    ## Buckets: in/out limit
    def inout_limit(inout):
        def con_rule(m, b, t):
            bucket = buckets[b]
            if inout == 'in':
                lhs = ms.var_bucket_in[b, t]
                rhs = bucket.get('in_max')
            elif inout == 'out':
                lhs = ms.var_bucket_out[b, t]
                rhs = bucket.get('out_max')
            else:
                raise RuntimeError("You should call this with 'in' or 'out' as argument.")

            if rhs is not None:
                return lhs <= rhs
            else:
                return pyo.Constraint.Skip

        return con_rule

    ms.con_bucket_max_in = pyo.Constraint(ms.set_buckets, ms.set_te, rule=inout_limit('in'))
    ms.con_bucket_max_out = pyo.Constraint(ms.set_buckets, ms.set_te, rule=inout_limit('out'))

    ## Buckets: min/max in duration
    def minmax_dur_limit(minmax):
        def con_rule(m, b, t):
            bucket = buckets[b]
            if minmax == 'min':
                duration = bucket.get('in_min_duration')
            elif minmax== 'max':
                duration = bucket.get('in_max_duration')
            else:
                raise RuntimeError("You should call this with 'min' or 'max' as argument.")

            if duration is not None and t + duration <= nt:
                if minmax == 'min':
                    return ms.var_bucket_in[b, t] >= ms.var_bucket_out[b, t + duration]
                elif minmax == 'max':
                    return ms.var_bucket_in[b, t] <= ms.var_bucket_out[b, t + duration]
            else:
                return pyo.Constraint.Skip

        return con_rule

    ms.con_bucket_min_in_dur = pyo.Constraint(ms.set_buckets, ms.set_te, rule=minmax_dur_limit('min'))
    ms.con_bucket_max_in_dur = pyo.Constraint(ms.set_buckets, ms.set_te, rule=minmax_dur_limit('max'))

    return model


# Helper functions
def safe_iter(x):
    try:
        return iter(x)
    except TypeError:
        return iter((x,))


# Basic test case
def main():
    param = {'nt': 24}

    sys.path.append(P(__file__, '../..'))
    import cases.combined.combined_settings_scheduling as settings_sched

    processes = settings_sched.processes
    buckets = settings_sched.constraint_buckets

    m = scheduling(param, processes, buckets)

    m.obj_total = pyo.Objective(expr=sum(m.sched.var_proc_active[p,t] * -t for p in m.sched.set_proc for t in m.sched.set_t))

    solver = 'gurobi_direct'
    solver_opts = {
        'warmstart': False,
        'tee': True,
        'options': {
            'Threads': os.cpu_count(),
        }
    }

    opt = pyo.SolverFactory(solver)
    result = opt.solve(m, **solver_opts)

    m.display()


if __name__ == "__main__":
    main()