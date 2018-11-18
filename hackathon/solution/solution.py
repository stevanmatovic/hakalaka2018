"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir

global blackout_happened
blackout_happened = 0

def calcPerc(load1, load2, load3):
    perc = 0.0
    if load1:
        perc += 0.2
    if load2:
        perc += 0.4
    if load3:
        perc += 0.4
    return perc



def worker(msg: DataMessage) -> ResultsMessage:
    """TODO: This function should be implemented by contestants."""
    # Details about DataMessage and ResultsMessage objects can be found in /utils/utils.py
    print('hello')
    load_one = True
    load_two = True
    load_three = True
    power_reference = 0.0
    pv_mode = PVMode.ON
    global blackout_happened
    minBatteryLife = 0.18

    #kada se desio blekaut onda mozemo bateriju od kraja da punimo
    if blackout_happened == 1 and msg.id % 1440 == 0:
        blackout_happened = 0

    if msg.grid_status == 0 and blackout_happened == 0:
        blackout_happened = 1;
        print('another blackout')

    if blackout_happened:
        minBatteryLife = 0.0




    # kada se vise isplati da placamo penale nego cenu struje
    if msg.buying_price > 6 and msg.current_load > 5.625:
        load_three = False

    if msg.buying_price > 6 and msg.current_load > 6.5625:
        load_two = False


    if 5 + msg.solar_production < msg.current_load and msg.grid_status == 0:
        load_three = False

    if 5+msg.solar_production < msg.current_load * 0.6 and msg.grid_status == 0:
        load_two = False
        load_three = False





    #ukoliko je skupa struja, a mala potrosnja koristimo bateriju da bi ustedeli
    #ukoliko imamo viska sunca punimo bateriju
    if msg.buying_price > 5 and load_two and load_one and msg.bessSOC > minBatteryLife:
        power_reference = msg.current_load*calcPerc(load_one,load_two,load_three) - msg.solar_production
        if power_reference > 5.0:
            power_reference = 5.0

    #ukoliko imamo viska solarne energije a jako je prazna baterija punimo bateriju
    if msg.solar_production > msg.current_load*calcPerc(load_one,load_two,load_three) and msg.bessSOC < minBatteryLife:
        power_reference = msg.current_load*calcPerc(load_one,load_two,load_three) - msg.solar_production

    # ukoliko je jeftina struja punimo bateriju do kraja
    if msg.buying_price < 6 and msg.bessSOC < 1 and msg.id < 7140:
        power_reference = -5.0

    # ukoliko solarni panel proizvodi previse energije, cak i za sve loadove i maks punjenje baterije - gasimo panel
    if msg.solar_production > 5 + msg.current_load:
        pv_mode = pv_mode.OFF

    #pred kraj poslednjeg dana trosimo sve iz baterije
    if (60*24*5 - msg.id) * 5 <= msg.bessSOC*20*60:
        power_reference = 5.0

    # Dummy result is returned in every cycle here
    return ResultsMessage(data_msg=msg,
                          load_one=load_one,
                          load_two=load_two,
                          load_three=load_three,
                          power_reference=power_reference,
                          pv_mode=pv_mode)


def run(args) -> None:
    prepare_dot_dir()
    config_outs(args, 'solution')

    cntrl = Control()

    for data in cntrl.get_data():
        cntrl.push_results(worker(data))
