# -*- coding: utf-8 -*-
# @Time : 2023/5/27 12:21
# @Author : yzbyx
# @File : run_basic_diagram.py
# Software: PyCharm
from trasim_simplified.core.constant import CFM
from trasim_simplified.util.flow_basic.basic_diagram import BasicDiagram


def run_basic_diagram(cf_name_, tau_, is_jam_, cf_param_, initial_v=0., random_v=False,
                      car_length_=5., start=0.01, end=1., step=0.02, plot=True, resume=False):
    diag = BasicDiagram(1000, car_length_, initial_v, random_v, cf_mode=cf_name_, cf_param=cf_param_)
    diag.run(start, end, step, resume=resume, file_name="result_" + cf_name_ + ("_jam" if is_jam_ else "") +
                                                        f"_{initial_v}_{random_v}",
             dt=tau_, jam=is_jam_, state_update_method="Euler")
    diag.get_by_equilibrium_state_func()
    if plot: diag.plot()


if __name__ == '__main__':
    cf_name = CFM.KK
    tau = 1
    speed = 0  # 初始速度为负代表真实的初始速度为跟驰模型期望速度
    cf_param = {"lambda": 0.8, "original_acc": False, "v_safe_dispersed": True, "tau": tau, "k2": 0.3}
    car_length = 7.5
    run_basic_diagram(cf_name, tau, False, cf_param, car_length_=car_length, initial_v=speed, resume=False)
