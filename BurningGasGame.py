#!/usr/bin/python3
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/1/14 16:48
# @Author  : Twodonkeys
# @Email   :liangzhilv@qq.com
# @Site    : 
# @File    : BuringGasGame.py
# @Software: PyCharm
import math
import time
from huepy import *
import random
class BuringGas():
    def __init__(self,valve_Gas,valve_Air):#初始化
        self.terminal=False#True为失败，False为正常
        self.random_Flow=0.02#空气煤气流量扰动幅度
        self.t=0#step次数
        self.time_cycle=1#扫描周期时间s
        self.T_waste=100#燃烧散失温度（80~100）
        #煤气中各组分含量比例
        self.Component_CO=0.14
        self.Component_H2=0.055
        self.Component_CH4=0.01
        self.Component_C2H4=0.001
        self.Component_CO2=0.105
        self.Component_N2=0.665
        self.Component_O2=0.001
        self.Component_H2O=0.023
        #煤气参数
        self.Radius_Gas=1 #煤气管道半径m
        self.Density_Gas=1.300 #煤气密度，不能为0
        self.Pressure_Gas=10 #煤气压力
        self.Flow_K_Gas=0.65 #煤气流量系数（0.6~0.65）
        self.Flow_Gas=3 #煤气流量m3/s
        self.ValueOpening_Gas=valve_Gas #煤气阀门开度
        self.T_pre_Gas=80#煤气预热温度
        # 空气参数
        self.Radius_Air=0.8#空气管道半径
        self.Density_Air=1.293 #空气密度,不能为0
        self.Pressure_Air=9 #空气压力
        self.Flow_K_Air=0.65 #空气流量系数（0.6~0.65）
        self.Flow_Air=3 #空气流量m3/s
        self.ValueOpening_Air=valve_Air #空气阀门开度
        self.T_pre_Air=50#空气预热温度
        print(lightred("初始化成功..."))
    def Gas_Heat(self,CO,H2,CH4,C2H4):#热值
        return (127.7*CO+107.6*H2+358.8*CH4+599.6*C2H4)*100

    def GetAirFuelRatio(self,CO,H2,CH4,C2H4,O2):#理论最优空燃比，单位煤气所用空气量
        return(4.76 * (0.5 * CO + 0.5 * H2 + 2 * CH4 + 3 * C2H4 - O2))

    def Flow(self,Radius,Density,Pressure,Flow_K,ValueOpening):#流量公式
        Area=math.pi*Radius*Radius*(1-math.cos(ValueOpening*math.pi/300))/5 #有效截面积
        Flow_PerSecond=math.sqrt(2*Pressure*38.6/(Density))*Flow_K*Area#每秒的流量
        Flow_PerHour=Flow_PerSecond*3600#每小时流量
        return Flow_PerSecond

    def getV_burned(self,H2,CO,CH4,C2H4,CO2,N2,H2O,AirFuelRatio):#单位（m3）煤气燃烧后的气体体积
        return (H2 + CO + 3 * CH4 + 4 * C2H4 + CO2 + N2 + H2O) + 0.79 * AirFuelRatio

    def FirstOrderInertia(self,input:float,output:float,lamda:float):#lamda越小延迟越大
        lamda=0.0 if (1.0 if lamda>1 else lamda)<0 else lamda
        out_num=input if abs(output-input)<1 else (input*lamda+output*(1-lamda))
        return out_num

    def buring(self):
        if self.Flow_Gas>(self.Flow_Air/self.AirFuelRatio):#煤气过量
            #单位煤气不完全燃烧产生的热量
            self.Heat_Unit=(self.Heat*(self.Flow_Air/self.AirFuelRatio))/self.Flow_Gas
            # 废气总体积（煤气为1单位时）
            self.V_burned = ((self.Flow_Air/self.AirFuelRatio)*self.V_burned_Unit
                        +(self.Flow_Gas-self.Flow_Air/self.AirFuelRatio))/self.Flow_Gas#燃烧生成的废气加上过量煤气，除以煤气总量
            # 元素占废气总体积比例
            self.V_burned_CO2=abs((self.Component_CO+self.Component_CH4+2*self.Component_C2H4)
                             *(self.AirFuelRatio_Actual/self.AirFuelRatio)+self.Component_CO2)/self.V_burned
            self.V_burned_H2O=abs((self.Component_H2+2*self.Component_CH4)+2*self.Component_C2H4)\
                         *(self.AirFuelRatio_Actual/self.AirFuelRatio)+self.Component_H2O/self.V_burned
            self.V_burned_N2=abs((self.Component_N2+0.79*self.AirFuelRatio_Actual)/self.V_burned)
            self.V_burned_O2 = 0
            self.V_burned_CH4=abs(self.Component_CH4*(1-self.AirFuelRatio_Actual/self.AirFuelRatio)/self.V_burned)
            self.V_burned_C2H4 = abs(self.Component_C2H4 * (1 - self.AirFuelRatio_Actual / self.AirFuelRatio) / self.V_burned)
            self.V_burned_CO = abs(self.Component_CO * (1 - self.AirFuelRatio_Actual / self.AirFuelRatio) / self.V_burned)
            self.V_burned_H2 = abs(self.Component_H2 * (1 - self.AirFuelRatio_Actual / self.AirFuelRatio) / self.V_burned)
        else:#煤气不够或刚好
            #单位煤气完全燃烧产生的热量
            self.Heat_Unit=self.Heat
            #废气总体积（煤气为1单位时）
            self.V_burned = self.V_burned_Unit + (self.Flow_Air / self.Flow_Gas - self.AirFuelRatio)#单位煤气燃烧产物体积=完全燃烧废气（单位）+剩余空气（单位）
            #元素占废气总体积比例
            self.V_burned_CO2=abs((self.Component_CO + self.Component_CH4 + 2 * self.Component_C2H4 + self.Component_CO2) / self.V_burned)
            self.V_burned_H2O = abs((self.Component_H2 + 2*self.Component_CH4 + 2 * self.Component_C2H4 + self.Component_H2O) / self.V_burned)
            self.V_burned_N2=abs((self.Component_N2+0.79*self.AirFuelRatio_Actual)/self.V_burned)
            self.V_burned_O2 = abs(0.21*(self.AirFuelRatio_Actual-self.AirFuelRatio)/ self.V_burned)
            self.V_burned_CH4 = 0
            self.V_burned_C2H4=0
            self.V_burned_CO=0
            self.V_burned_H2=0
    def reset(self):
        print(lightpurple("重置..."))
        time.sleep(0.5)
        self.__init__()

    def print_out(self):
        print("\r 煤气阀门设定和反馈:({0},{1});空气阀门设定和反馈:({2},{3});燃烧温度:({4});最优空燃比:({5});实际空燃比:({6});煤气热值:({7})..."
              .format(str(round(self.valve_Gas,1)), str(round(self.ValueOpening_Gas,1)), str(round(self.valve_Air,1)),
                      str(round(self.ValueOpening_Air,1)), str(round(self.T_buring,1)), str(round(self.AirFuelRatio,3)),
                      str(round(self.AirFuelRatio_Actual,3)),str(round(self.Heat_Unit))) + "循环" + str(self.t)+"次", end="")  # 没有end不会此行更新

    def step(self, valve_Gas, valve_Air):  # 动作传入
        self.valve_Gas=(float(valve_Gas) if valve_Gas<100 else 100) if valve_Gas>0 else 0
        self.valve_Air=(float(valve_Air) if valve_Air<100 else 100) if valve_Air>0 else 0
        self.ValueOpening_Gas=self.FirstOrderInertia(float(self.valve_Gas),float(self.ValueOpening_Gas),0.5)
        self.ValueOpening_Air=self.FirstOrderInertia(float(self.valve_Air),float(self.ValueOpening_Air),0.5)

        # 煤气流量
        self.Flow_Gas = self.Flow(Radius=self.Radius_Gas, Density=self.Density_Gas, Pressure=self.Pressure_Gas,
                                  Flow_K=self.Flow_K_Gas, ValueOpening=self.ValueOpening_Gas)+random.uniform(0,self.random_Flow)
        # 空气流量
        self.Flow_Air = self.Flow(Radius=self.Radius_Air, Density=self.Density_Air, Pressure=self.Pressure_Air,
                                  Flow_K=self.Flow_K_Air, ValueOpening=self.ValueOpening_Air)+random.uniform(0,self.random_Flow)
        # 单位煤气最佳燃烧所需空气量：理论最佳空煤比
        self.AirFuelRatio = self.GetAirFuelRatio(CO=self.Component_CO, H2=self.Component_H2, CH4=self.Component_CH4,
                                              C2H4=self.Component_C2H4, O2=self.Component_O2)
        # 单位煤气理论生成废气
        self.V_burned_Unit = self.getV_burned(H2=self.Component_H2, CO=self.Component_CO, CH4=self.Component_CH4,
                                           C2H4=self.Component_C2H4, CO2=self.Component_CO2, N2=self.Component_N2,
                                           H2O=self.Component_H2O, AirFuelRatio=self.AirFuelRatio)
        # 单位煤气热量：热值
        self.Heat = self.Gas_Heat(self.Component_CO, self.Component_H2, self.Component_CH4, self.Component_C2H4)
        # 实际空燃比
        self.AirFuelRatio_Actual = self.Flow_Air / self.Flow_Gas
        # 燃烧ing
        self.buring()
        # 空气比热容
        self.C_Air = 1.3
        # 煤气比热容
        self.C_Gas = 1.2979 * self.Component_CO + 1.277 * self.Component_H2 + 1.5491 * self.Component_CH4 \
                     + 1.8255 * self.Component_C2H4 + 1.5994 * self.Component_CO2 + 1.2937 * self.Component_N2 \
                     + 1.3063 * self.Component_O2 + 1.4947 * self.Component_H2O + 0.0075 * self.T_pre_Gas / 100
        # 废气比热容
        self.C_Exhaust = 1.2979 * self.V_burned_CO + 1.277 * self.V_burned_H2 + 1.5491 * self.V_burned_CH4 \
                         + 1.8255 * self.V_burned_C2H4 + 1.5994 * self.V_burned_CO2 + 1.2937 * self.V_burned_N2 \
                         + 1.3063 * self.V_burned_O2 + 1.4947 * self.V_burned_H2O
        # 单位煤气燃烧释放的热量
        self.i_H = self.Heat_Unit
        # 空气显热
        self.i_Air = self.AirFuelRatio_Actual * self.C_Air * self.T_pre_Air
        # 煤气显热
        self.i_Gas = 1 * self.C_Gas * self.T_pre_Gas
        # 燃烧后总热量
        self.i_Sum = (self.i_Air + self.i_Gas + self.i_H) / self.V_burned
        # 理论燃烧温度计算
        self.T_buring = self.i_Sum / self.C_Exhaust-self.T_waste

        state=(self.valve_Gas,self.valve_Air,self.ValueOpening_Gas,self.ValueOpening_Air,self.T_buring)
        if self.ValueOpening_Air<=3 or self.ValueOpening_Gas<=3 or abs(self.AirFuelRatio_Actual-self.AirFuelRatio)>0.5:
            # 燃烧条件失败，游戏结束
            self.terminal=True
            print("游戏失败！")
            time.sleep(self.time_cycle)
        self.t+=1
        self.print_out()
        time.sleep(self.time_cycle)
        return(state,self.terminal)

if __name__=='__main__':
    valve_gas=70
    valve_air=68
    bur=BuringGas(valve_gas,valve_air)
    while 1:
        #valve_gas += 1
        bur.step(valve_Gas=valve_gas,valve_Air=valve_air)

