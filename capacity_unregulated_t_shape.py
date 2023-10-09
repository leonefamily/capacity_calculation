#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 23:27:54 2023

@author: leonefamily
"""

import sys
import math
import argparse
from typing import Union, Literal


TFS = {
    4: {
        1: 2.6,
        7: 2.6,
        6: 3.1,
        12: 3.1,
        5: 3.3,
        11: 3.3,
        4: 3.5,
        10: 3.5
    },
    6: {
        1: 2.6,
        7: 2.6,
        6: 3.7,
        12: 3.7,
        5: 3.9,
        11: 3.9,
        4: 4.1,
        10: 4.1
    }
}
LOS = {
    'A': 10,
    'B': 20,
    'C': 30,
    'D': 55,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--i2', type=int)
    parser.add_argument('--i3', type=int)
    parser.add_argument('--i4', type=int)
    parser.add_argument('--i6', type=int)
    parser.add_argument('--i7', type=int)
    parser.add_argument('--i8', type=int)
    args = parser.parse_args(sys.argv[1:])
    return args


def get_follow_up_offset(
        flow_num: int,
        p_sign: Literal[4, 6] = 4
) -> float:
    if p_sign not in [4, 6]:
        raise ValueError('Wrong P sign number')
    if flow_num not in TFS[p_sign]:
        raise ValueError('Wrong flow number')
    return TFS[p_sign][flow_num]


def get_critical_time_offset(
        flow_num: int,
        free_flow_speed: Union[int, float]
) -> float:
    if flow_num in [7, 1]:
        return 3.4 + 0.021 * 0.85 * free_flow_speed
    elif flow_num in [6, 12]:
        return 2.8 + 0.038 * 0.85 * free_flow_speed
    elif flow_num in [5, 11]:
        return 4.4 + 0.036 * 0.85 * free_flow_speed
    elif flow_num in [4, 10]:
        return 5.2 + 0.022 * 0.85 * free_flow_speed
    else:
        raise ValueError('Wrong flow number')


def get_base_capacity(
        tf: float,
        tg: float,
        ih: Union[int, float]
) -> float:
    cgn = 3600 / tf * math.e ** - ((ih / 3600) * (tg - tf / 2))
    return cgn


def get_load_coefficient(
        i: Union[int, float],
        c: Union[int, float]
) -> float:
    if i > 0:
        return i / c
    return sys.maxsize


def get_unbloated_flow_probability(
        i_n: Union[int, float],
        cgn: Union[int, float]
) -> float:
    p0n = max(0, 1 - get_load_coefficient(i_n, cgn))
    return p0n


def get_mean_delay(
        i_n: Union[int, float],
        cn: Union[int, float],
        t: Union[int, float] = 3600
) -> float:
    avn = get_load_coefficient(i_n, cn)
    twn = 3600 / cn + t / 4 * (
        (avn - 1) + math.sqrt(
            (avn - 1) ** 2 + (3600 * 8 * min(avn, 1)) / (cn * t)
        )
    )
    return twn


def get_queue_length(
        i_n: Union[int, float],
        cn: Union[int, float]
) -> float:
    if cn <= 0:
        raise ValueError('Capacity must be greater than 0')

    avn = get_load_coefficient(i_n, cn)
    l95 = 3 / 2 * cn * (
        avn - 1 + math.sqrt(
            (1 - avn) ** 2 + 3 * (8 * avn / cn)
        )
    )
    return l95


def get_level_of_service(
        i_n: Union[int, float],
        cn: Union[int, float],
        twn: Union[int, float]
) -> str:
    for los, los_max in LOS.items():
        if twn < los_max:
            return los
    if i_n < cn:
        return 'E'
    return 'F'


def main(
        i2: int,
        i3: int,
        i4: int,
        i6: int,
        i7: int,
        i8: int
):
    # i2=396
    # i3=567
    # i4=284
    # i6=6
    # i7=6
    # i8=401

    ih6 = round(i2 + 0.5 * i3)
    ih4 = round(i2 + 0.5 * i3 + i8 + i7)
    ih7 = i2 + i3

    c2 = c3 = c8 = 1800
    cg4 = get_base_capacity(
        tf=get_follow_up_offset(flow_num=4, p_sign=4),
        tg=get_critical_time_offset(flow_num=4, free_flow_speed=50),
        ih=ih4
    )
    c6 = get_base_capacity(
        tf=get_follow_up_offset(flow_num=6, p_sign=4),
        tg=get_critical_time_offset(flow_num=6, free_flow_speed=50),
        ih=ih6
    )
    c7 = get_base_capacity(
        tf=get_follow_up_offset(flow_num=7, p_sign=4),
        tg=get_critical_time_offset(flow_num=7, free_flow_speed=50),
        ih=ih7
    )
    p07 = get_unbloated_flow_probability(i_n=i7, cgn=c7)
    c4 = cg4 * p07

    av2 = get_load_coefficient(i2, c2)
    av3 = get_load_coefficient(i3, c3)
    av4 = get_load_coefficient(i4, c4)
    av6 = get_load_coefficient(i6, c6)
    av7 = get_load_coefficient(i7, c7)
    av8 = get_load_coefficient(i8, c8)

    i2_3 = sum([i2, i3])
    i4_6 = sum([i4, i6])
    i7_8 = sum([i7, i8])

    c2_3 = round(c2)
    c4_6 = round(i4_6 / sum([av4, av6]))
    c7_8 = round(i7_8 / sum([av7, av8]))

    tw2_3 = 0
    tw4_6 = round(get_mean_delay(i4_6, c4_6), 2)
    tw7_8 = round(get_mean_delay(i7_8, c7_8), 2)

    l95_2_3 = 0
    l95_4_6 = round(get_queue_length(i4_6, c4_6), 2)
    l95_7_8 = round(get_queue_length(i7_8, c7_8), 2)

    los2_3 = get_level_of_service(i2_3, c2_3, tw2_3)
    los4_6 = get_level_of_service(i4_6, c4_6, tw4_6)
    los7_8 = get_level_of_service(i7_8, c7_8, tw7_8)

    print(
        f'Kapacita: 2-3: {c2_3}, 4-6: {c4_6}, 7-8: {c7_8}',
        f'Střední doba zdržení 2-3: {tw2_3} s, 4-6: {tw4_6} s, 7-8: {tw7_8} s',
        f'Délka fronty 2-3: {l95_2_3} m, 4-6: {l95_4_6} m, 7-8: {l95_7_8} m',
        f'ÚKD 2-3: {los2_3}, 4-6: {los4_6}, 7-8: {los7_8}',
        sep='\n'
    )


if __name__ == '__main__':
    args = parse_args()
    main(
        i2=args.i2,
        i3=args.i3,
        i4=args.i4,
        i6=args.i6,
        i7=args.i7,
        i8=args.i8
    )
