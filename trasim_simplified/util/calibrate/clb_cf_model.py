# -*- coding = uft-8 -*-
# @Time : 2022-04-06 23:24
# @Author : yzbyx
# @File : clb_cf_model.py
# @Software : PyCharm
import joblib

import geatpy as ea
import numpy as np

from trasim_simplified.core.constant import CFM

from trasim_simplified.util.calibrate.gof_func import RMSE
from trasim_simplified.util.calibrate.follow_sim import simulation


cf_param_ranges = {
    CFM.IDM: {
        "s0": [0, 5], "s1": [0, 5], "v0": [0, 40], "T": [0, 5], "omega": [0, 5], "d": [0, 5], "delta": [0, 10]
    },
    CFM.GIPPS: {
        "a": [0, 10], "b": [-10, 0], "v0": [0, 40], "tau": [0, 2], "s": [0, 10], "b_hat": [-10, 0],
    },
    CFM.NON_LINEAR_GHR: {
        "m": [-5, 5], "l": [-5, 5], "a": [-10, 10], "tau": [0, 2]
    },
    CFM.WIEDEMANN_99: {
        "CC0": [0, 5], "CC1": [0, 5], "CC2": [0, 10], "CC3": [-20, 0], "CC4": [-5, 0], "CC5": [0, 5],
        "CC6": [0, 10], "CC7": [0, 5], "CC8": [0, 10], "CC9": [0, 10], "vDesire": [0, 40]
    },
    CFM.OPTIMAL_VELOCITY: {
        "a": [0, 10], "V0": [0, 40], "m": [0, 1], "bf": [0, 50], "bc": [0, 10]
    }
}
cf_param_types = {
    CFM.IDM: {"s0": 0, "s1": 0, "v0": 0, "T": 0, "omega": 0, "d": 0, "delta": 1},
    CFM.GIPPS: {"a": 0, "b": 0, "v0": 0, "tau": 0, "s": 0, "b_hat": 0},
    CFM.NON_LINEAR_GHR: {"m": 0, "l": 0, "a": 0, "tau": 0},
    CFM.WIEDEMANN_99: {"CC0": 0, "CC1": 0, "CC2": 0, "CC3": 0, "CC4": 0, "CC5": 0, "CC6": 0, "CC7": 0, "CC8": 0,
                       "CC9": 0, "vDesire": 0},
    CFM.OPTIMAL_VELOCITY: {"a": 0, "V0": 0, "m": 0, "bf": 0, "bc": 0}
}


def ga_cal(cf_func, df_dataset, dt, ranges: dict, types, seed, drawing=0):
    """
    :param cf_func: 跟驰模型函数
    :param df_dataset: 数据集， 包含obs_x, obs_v, obs_lx, obs_lv, leaderL
    :param dt: 仿真步长
    :param ranges: 参数范围{"a": 1, ...}
    :param types: 参数类型，0：实数；1：整数
    :param seed: GA随机种子
    :param drawing: 是否绘图 0表示不绘图； 1表示绘制最终结果图； 2表示实时绘制目标空间动态图； 3表示实时绘制决策空间动态图。
    """
    param_names = list(ranges.keys())
    obs_x = df_dataset['obs_x']
    obs_v = df_dataset['obs_v']
    obs_lx = df_dataset['obs_lx']
    obs_lv = df_dataset['obs_lv']
    leaderL = df_dataset['leaderL']

    @ea.Problem.single
    def eval_vars(params):  # 定义目标函数（含约束）
        param = {k: v for k, v in zip(ranges.keys(), params)}
        x, v, _ = simulation(
            cf_func=cf_func, obs_x=obs_x, obs_v=obs_v, obs_lx=obs_lx, obs_lv=obs_lv,
            cf_params=param, leaderL=leaderL, dt=dt, update_method="Euler")
        return RMSE(sim_x=x, sim_v=v, obs_x=obs_x, obs_v=obs_v, obs_lx=obs_lx, eval_params=["dhw"])

    problem = ea.Problem(name='test',
                         M=1,  # 目标维数
                         maxormins=[1],  # 目标最小最大化标记列表，1：最小化该目标；-1：最大化该目标
                         Dim=len(ranges),  # 决策变量维数
                         varTypes=[types[name] for name in param_names],  # 决策变量的类型列表，0：实数；1：整数
                         lb=[ranges[name][0] for name in param_names],  # 决策变量下界
                         ub=[ranges[name][1] for name in param_names],  # 决策变量上界
                         evalVars=eval_vars)

    # 构建算法
    algorithm = ea.soea_SEGA_templet(problem,
                                     ea.Population(Encoding='RI', NIND=30),
                                     MAXGEN=300,  # 最大进化代数。
                                     logTras=1,  # 表示每隔多少代记录一次日志信息，0表示不记录。
                                     trappedValue=1e-6,  # 单目标优化陷入停滞的判断阈值。
                                     maxTrappedCount=50)  # 进化停滞计数器最大上限值。
    algorithm.mutOper.Pm = 0.5  # 变异概率
    algorithm.recOper.XOVR = 0.7  # 重组概率

    # 求解
    res = ea.optimize(algorithm, verbose=False, seed=seed, drawing=drawing, outputMsg=False, drawLog=False,
                      saveFlag=False)
    print(f"{cf_func.__name__}-seed{seed}: {res['ObjV'][0]}, {res['Vars'][0]}, {res['executeTime']}")
    return res


def clb_run(cf_func, cf_name, traj_s, dt, seed, drawing=0) -> list[dict]:
    result = joblib.Parallel(n_jobs=-1)(
        joblib.delayed(ga_cal)(cf_func=cf_func, traj=traj, dt=dt, ranges=cf_param_ranges[cf_name],
                               types=cf_param_types[cf_name], seed=seed, drawing=drawing)
        for traj in traj_s)
    return result


def aggregate_result(result):
    avg_obj = np.mean([res['ObjV'] for res in result])
    avg_param = np.mean([res['Vars'] for res in result], axis=0)
    std_obj = np.std([res['ObjV'] for res in result])
    std_param = np.std([res['Vars'] for res in result], axis=0)
    return avg_obj, avg_param, std_obj, std_param
