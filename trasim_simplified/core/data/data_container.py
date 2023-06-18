# -*- coding = uft-8 -*-
# @Time : 2023-03-31 16:20
# @Author : yzbyx
# @File : data_container.py
# @Software : PyCharm
from typing import TYPE_CHECKING, Optional

import pandas as pd

if TYPE_CHECKING:
    from trasim_simplified.core.frame.micro.lane_abstract import LaneAbstract


class DataContainer:
    def __init__(self, lane_abstract: 'LaneAbstract'):
        self.lane = lane_abstract
        self.data_pd: Optional[pd.DataFrame] = None
        self.save_info: set = set()
        self.total_car_list_has_data = None
        self.data_df: Optional[pd.DataFrame] = None

    def config(self, save_info=None, add_all=True):
        """默认包含车辆ID"""
        if add_all:
            self.save_info.update(Info.get_all_info().values())
            return
        if save_info is None:
            save_info = {}
        self.save_info.update(save_info)

    def add_basic_info(self):
        self.save_info.update([Info.lane_add_num, Info.id, Info.time, Info.step])

    def data_to_df(self):
        data: dict[str, list] = {info: [] for info in self.save_info}
        total_car_list_has_data = self.get_total_car_has_data()
        info_list = list(self.save_info)
        for info in info_list:
            for car in total_car_list_has_data:
                data[info].extend(car.get_data_list(info))
        self.data_df = pd.DataFrame(data, columns=info_list).sort_values(by=[Info.id, Info.time]).reset_index(drop=True)
        return self.data_df

    def get_total_car_has_data(self):
        """仿真完成后调用"""
        if self.total_car_list_has_data is None:
            car_on_lane_has_data = [car for car in self.lane.car_list if car.has_data()]
            self.total_car_list_has_data = car_on_lane_has_data + self.lane.out_car_has_data
        return self.total_car_list_has_data

    def get_data(self, id_, info_name):
        """仿真完成后调用"""
        return self.data_df[self.data_df[Info.id] == id_][info_name]


class Info:
    lane_add_num = "Lane Add Num"
    """车辆所在车道在该路段的添加次序，以0为开始依次累加"""
    id = "ID"
    """车辆ID"""
    step = "Step"
    """仿真步次"""
    time = "Time [s]"
    """仿真时间"""
    a = "Acceleration [m/s^2]"
    """加速度"""
    v = "Velocity [m/s]"
    """速度"""
    x = "Position [m]"
    """位置"""
    dhw = "Distance Headway [m]"
    """车头间距"""
    thw = "Time Headway [s]"
    """车头时距"""
    gap = "Gap [m]"
    """净间距"""
    dv = "Dv [m/s]"
    """前车与后车速度差"""
    cf_id = "cf model ID"
    """跟驰模型类别ID"""
    lc_id = "lc model ID"
    """换到模型类别ID"""

    safe_ttc = "ttc(s)"
    safe_tet = "tet"
    safe_tit = "tit(s)"
    safe_picud = "picud(m)"
    safe_picud_KK = "picud_KK (m)"
    """KK模型适用的picud计算方式（前车最大减速度等于当前车的最大减速度）"""

    @classmethod
    def get_all_info(cls):
        dict_ = Info.__dict__
        values = {}
        for key in dict_.keys():
            if isinstance(dict_[key], str) and key[:2] != "__":
                values.update({key: dict_[key]})
        return values


if __name__ == '__main__':
    print(Info.get_all_info())
