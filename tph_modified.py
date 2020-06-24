import numpy as np
import time
import logging as log
from datetime import datetime
from random import randint

# log.basicConfig(level=log.DEBUG)

import warnings
warnings.filterwarnings("ignore")


'''
Проверка по логу запрос/ответ (генерация всех возможных значений). 
Первая не бъется с ходу т.к. rsp_rand = 0 (а не 4)  
    i3 = 2
    i4(pos) = 0
1:OK!!! hex:"a908041a70b86215"  rsp_rand: 4, r: 184, r2: 98 
    должно быть i4+6 = 5 (т.е. pos должен быть -1) 
2:OK!!! hex:"a90804b4da825c15"  rsp_rand: 3, r: 218, r2: 130
'''


class TreadmillProtocolHelper:


    pos = 0
    recvPos = 0
    buffer = np.zeros(512, dtype=np.int8)
    # соглашение. видимо для понимания - новая/старая модель дорожки?
    agreement_status = 0
    check_date = datetime.utcnow()
    is_connected = False
    req_random_num = 134
    rsp_random_num = 0
    first_handshake_passed = False
    i_error_code = 0
    i_error_count = 0
    time_after_handshake = 0
    run_state = -1
    query_speed_slope = False
    has_slope_func = False
    cur_pulse = 0
    query_equip = False
    is_speed_changed = False
    is_slope_changed = False

    def manage_data(self, barr):
        log.debug('manage_data: %s', self.get_hex(barr))
        if self.pos > 255:
            for i in range(0, self.recvPos - self.pos, 1):
                self.buffer[i] = self.buffer[self.pos + i]
            self.recvPos -= self.pos
            if self.recvPos < 0:
                self.recvPos = 0
            self.pos = 0

        for i2 in range(0, len(barr), 1):
            self.buffer[self.recvPos + i2] = barr[i2]

        self.recvPos += len(barr)
        if self.agreement_status == 2:
            self.manage_data_by_new()
        elif self.agreement_status == 1:
            self.manage_data_by_old()
        return self.send_data_arr

    def on_device_msg_rec(self, code):
        log.debug("on_device_msg_rec %s", code)

    def send_code(self, code):
        log.debug("send_code: %s", code)
        if code == 1:
            if self.agreement_status == 2:
                self.send_new_code(code)
            else:
                self.send_old_code(code)
        elif self.agreement_status == 1:
            self.send_old_code(code)
        else:
            self.send_new_code(code)

    def send_new_code(self, code):
        if code == 1:
            self.send_first_check_code()
        elif code == 2:
            self.send_check_resp_code()
            #self.test_send_ckeck_resp_code()
        elif code == 3:
            self.send_query_speed_slope()
        elif code == 4:
            self.send_reset_data_code()
        elif code == 5 and self.is_speed_changed:
            self.is_speed_changed = False
            #self.set_speed_by_thread()
        elif code == 6:
            self.send_hearbeat_code()
        elif code == 7 and self.is_slope_changed:
            self.is_slope_changed = False
            #self.set_slope_by_thread()
        elif code == 8:
            log.debug('send_query_equip')

    def send_old_code(self, code):
        log.debug("send_old_code %s", code)
        if code == 1:
            self.send_first_check_code()
        elif code == 2:
            self.send_check_resp_code_by_old()
        elif code == 5:
            log.debug("self.set_speed_by_thread_by_old()")
        elif code == 7 and self.is_slope_changed:
            self.is_slope_changed = False
            log.debug("self.set_slope_by_thread_by_old()")


    def manage_data_by_old(self):
        log.error("not implement yet")

    def manage_data_by_new(self):
        #log.debug("manage_data_by_new, %s", self.get_hex(self.buffer))
        while self.recvPos - self.pos > 4:
            self.check_date = datetime.utcnow()
            barr = self.buffer
            i = self.pos
            if barr[i] != np.int8(169):
                self.pos = i+1
            else:
                b = barr[i+1]
                b2 = barr[i+2]
                if self.recvPos >= i+4+b2:
                    xor = self.xor_result(barr, i, i+2+b2)
                    barr2 = self.buffer
                    i2 = self.pos
                    z = False
                    if barr2[i2+3+b2] != xor:
                        self.pos = i2+1
                        if self.buffer[self.pos+3+b2] == xor:
                            z = True
                        log.debug("ding")
                    else:
                        if not self.is_connected:
                            if b == np.int8(254) and b2 == np.int8(1):
                                if barr2[i2+3] == np.int8(1):
                                    self.on_device_msg_rec(38)
                                self.pos += b2+4
                            elif b == np.int8(8):
                                if b2 == np.int8(4):
                                    i3 = self.req_random_num % 6
                                    barr3 = self.buffer
                                    i4 = self.pos
                                    b3 = barr3[i4+3]
                                    b4 = barr3[i4+4]
                                    b5 = barr3[i4+5]
                                    b6 = barr3[i4+6]
                                    self.rsp_random_num = -1
                                    if i3 == np.int8(0):
                                        if b5 == np.int8((b3+b4)%256) and b6 == np.int8((b3*b4)%256):
                                            self.rsp_random_num = b6
                                            self.send_code(2)
                                    elif i3 == np.int8(1):
                                        if b5 == np.int8((b3*b4)%256) and b6 == np.int8((b3+b4)%256):
                                            self.rsp_random_num = b6
                                            self.send_code(2)
                                    elif i3 == np.int8(2):
                                        if b3 == np.int8((b4+b5)%256) and b6 == np.int8((b4*b5)%256):
                                            self.rsp_random_num = b6
                                            self.send_code(2)
                                    elif i3 == np.int8(3):
                                        if b3 == np.int8((b4*b5)%256) and b6 == np.int8((b4+b5)%256):
                                            self.rsp_random_num = b6
                                            self.send_code(2)
                                    elif i3 == np.int8(4):
                                        if b3 == np.int8((b5+b6)%256) and b4 == np.int8((b5*b6)%256):
                                            self.rsp_random_num = b6
                                            self.send_code(2)
                                    elif i3 == np.int8(5) and b3 == np.int8((b5*b6)%256) and b4 == np.int8((b5+b6)%256):
                                        self.rsp_random_num = b6
                                        self.send_code(2)
                                    self.pos += b2+4
                                    if self.rsp_random_num == -1:
                                        log.debug("BT CHECK FAILED =(")
                                    else:
                                        self.first_handshake_passed = True
                                        log.debug("BT CHECK SUCCESS!")
                                elif self.buffer[self.pos+3] == np.int8(255) and self.first_handshake_passed:
                                    if self.time_after_handshake == 0:
                                        self.time_after_handshake = 1000 # time after boot
                                    elif self.time_after_handshake - 1000 >= 2000:
                                        self.first_handshake_passed = False
                                        self.time_after_handshake = 0
                                self.pos += b2+4
                            elif self.first_handshake_passed:
                                self.is_connected = True
                            else:
                                self.pos += b2 + 4
                        if b == np.int8(8) and b2 == np.int8(1):
                            log.warning("BT receive connect request 08 01 ff")
                            if self.buffer[self.pos+3] == 255:
                                log.warning("BT receive connect request 08 01 ff")
                                self.is_connected = False
                                self.first_handshake_passed = False
                                self.time_after_handshake = 0
                            elif b == np.int8(9) and b2 == np.int8(1):
                                b7 = self.buffer[self.pos+3]
                                if b7 != self.run_state:
                                    self.run_state = b7
                                    log.debug("Получено изменение статуса", b7)
                                    # self.on_device_msg_rec(DEVICE_RUN_STATE, b7, 1)
                            elif b == np.int8(10) and b2 == np.int8(1):
                                self.query_speed_slope = True
                                b8 = self.buffer[self.pos+3]
                                #setMaxSlope(b8)
                                if b8 <= np.int8(1):
                                    b8 = np.int8(0)
                                # self.on_device_msg_rec(DEVICE_SPEED_SLOPE_LIMIT...)
                            elif b == np.int8(10) and b2 == np.int8(4):
                                self.query_speed_slope = True
                                barr4 = self.buffer
                                i5 = self.pos
                                b9 = barr4[i5+3]
                                b10 = barr4[i5+4]
                                b11 = barr4[i5+5]
                                b12 = barr4[i5+6]
                                if b9 > b10:
                                    b9, b10 = b10, b9
                                if b11 <= b12:
                                    b11, b12 = b12, b11
                                if b11 == b12:
                                    self.has_slope_func = False
                                #setMinSpeed(b9)
                                #setMaxSpeed(b10)
                                #setMinSlope(b12)
                                #setMaxSlope(b11)
                                #on_device_msg_rec(DEVICE_SPEED_SLOPE_LIMIT)
                            elif b == np.int8(5) and b2 == np.int8(1):
                                barr5 = self.buffer
                                i6 = self.pos
                                bval = barr5[i6+3]
                                switcher = {
                                    1: 35,
                                    2: 36,
                                    3: 31,
                                    4: 32,
                                    5: 33,
                                    6: 34,
                                    7: 38,
                                    8: 39,
                                    9: 46,
                                    10: 42,
                                    11: 43,
                                    12: 44,
                                    19: 44,
                                    13: 45,
                                    20: 45,
                                    14: 48,
                                    15: 47,
                                    16: 51,
                                    17: 52,
                                    18: 55,
                                    21: 56,
                                    22: 50,
                                    23: 57,
                                    24: 49,
                                    25: 53,
                                    26: 54,
                                    27: 91,
                                    28: 101,
                                    29: 104,
                                    30: 92,
                                    32: 106,
                                    33: 107,
                                    34: 108,
                                    35: 112,
                                    36: 113,
                                    37: 116,
                                    38: 117,
                                    48: 109,
                                    49: 110,
                                    50: 111,
                                    51: 114,
                                    52: 115
                                }
                                if bval in switcher:
                                    self.on_device_msg_rec(switcher[bval])
                                else:
                                    log.error('command error, b, bval', b, bval)
                            elif b == np.int8(2):
                                b15 = self.buffer[self.pos + 3]
                                self.cur_pulse = b15
                                if b15 <= np.int8(50) or b15 <= np.int8(135):
                                    b16 = b15
                                elif b15 > np.int8(150):
                                    b16 = 137
                                elif b15 > np.int8(140):
                                    b16 = 137
                                else:
                                    b16 = 135

                                if b2 >= np.int8(13):
                                    log.error('xdh - ошибка данные пульса')
                                    #get run data values
                                    #self.on_device_msg_rec(DEVICE_RUN_DATA, RunData(i,i2...
                            elif b == np.int8(3):
                                barr12 = self.buffer
                                i13 = self.pos
                                b17 = barr12[i13+3]
                                if b2 == np.int8(2):
                                    b18 = barr12[i13+4]
                                else:
                                    b18 = b17
                                self.i_error_count += 1
                                log.error('device report error, error cnt', self.i_error_count)
                            elif b == np.int8(12) and b2 == np.int8(2):
                                barr13 = self.buffer
                                i14 = self.pos
                                b19 = barr13[i14+3]
                                b20 = barr13[i14 + 4]
                            elif b == np.int8(224) and b2 == np.int8(1):
                                b21 = self.buffer[self.pos+3]
                                #self.on_device_msg_rec(24, b21, b21)
                            elif b == np.int8(226) and b2 == np.int8(1):
                                if self.buffer[self.pos + 3] == np.int8(1):
                                    self.on_device_msg_rec(84)
                                else:
                                    self.on_device_msg_rec(85)
                            elif b == np.int8(227) and b2 == np.int8(1) and self.buffer[self.pos + 3] == np.int8(2):
                                self.on_device_msg_rec(85)
                            elif b == np.int8(228) and b2 == np.int8(1):
                                b23 = self.buffer[self.pos + 3]
                            elif b == np.int8(30) and b2 == np.int8(5):
                                self.query_equip = True
                                barr14 = self.buffer
                                i15 = self.pos
                                b24 = barr14[i15+3]
                                b25 = barr14[i15+4]
                                b26 = barr14[i15+5]
                                b27 = barr14[i15+6]
                                b28 = barr14[i15+7]
                                #Create EquipInfo instance
                                #self.on_device_mag_rec(DEVICE_INFO, equip)
                            else:
                                log.error("command error")

                        self.pos += b2+4
                else:
                    return

    @staticmethod
    def get_hex(b):
        return 'hex:"'+b.tobytes().hex()+'"'

    @classmethod
    def xor_result(cls, buffer, i, i2):
        b = np.int8(0)
        if i < 0:
            i = 0
        if len(buffer) <= i2:
            i2 = len(buffer) - 1

        b = buffer[i]
        while True:
            i = i + 1
            if i > i2:
                break
            b = b ^ buffer[i]

        #log.debug("xor_result. input %s, output %s", cls.get_hex(buffer), b)
        return b

    @classmethod
    def send_single_code(cls, b, b2):
        barr = np.array([-87, b, 1, b2, 0], dtype=np.int8)
        barr[4] = cls.xor_result(barr, 0, 3)
        log.debug("send single code: %s", cls.get_hex(barr))
        print(barr)
        return barr

    def send_data_to_ble(self, b):
        log.debug("send data to BLE: %s", b.tobytes().hex())
        self.send_data_arr = b.tobytes()

    @classmethod
    def send_first_check_code(cls):
        req_random_num = 134
        agreement = 2
        if agreement == 1:
            cls.send_data_to_ble(np.array([8, 1, req_random_num], dtype=np.int8))
        elif agreement == 2:
            cls.send_single_code(8, req_random_num)
        else:
            cls.send_data_to_ble(np.array([8, 1, req_random_num], dtype=np.int8))
            time.sleep(1)
            cls.send_single_code(8, req_random_num)

    def test_send_ckeck_resp_code(self):
        for random in range(0, 255):
            for random2 in range(0, 255):
                for i in range(0, 6):
                    barr = np.zeros(8, dtype=np.int8)
                    barr[0] = -87
                    barr[1] = 8
                    barr[2] = 4
                    # i = self.rsp_random_num % 6
                    if i == 0:
                        barr[3] = np.int8(random)
                        barr[4] = np.int8(random2)
                        barr[5] = np.int8((random + random2) % 256)
                        barr[6] = np.int8((random * random2) % 256)
                    elif i == 1:
                        barr[3] = random
                        barr[4] = random2
                        barr[5] = (random * random2) % 256
                        barr[6] = (random + random2) % 256
                    elif i == 2:
                        barr[3] = (random + random2) % 256
                        barr[4] = random
                        barr[5] = random2
                        barr[6] = (random * random2) % 256
                    elif i == 3:
                        barr[3] = (random * random2) % 256
                        barr[4] = random
                        barr[5] = random2
                        barr[6] = (random + random2) % 256
                    elif i == 4:
                        barr[3] = (random + random2) % 256
                        barr[4] = (random * random2) % 256
                        barr[5] = random
                        barr[6] = random2
                    elif i == 5:
                        barr[3] = (random * random2) % 256
                        barr[4] = (random + random2) % 256
                        barr[5] = random
                        barr[6] = random2

                    barr[7] = self.xor_result(barr, 0, 6)
                    if 'a908041a70b86215' in self.get_hex(barr) or \
                            'a90804b4da825c15' in self.get_hex(barr):
                        print("OK!!! %s  i: %s, r: %s, r2: %s" % (self.get_hex(barr), i, random, random2))

    def send_check_resp_code(self):
        log.debug("send_check_resp_code")
        random = randint(0, 255)
        random2 = randint(0, 255)
        barr = np.zeros(8, dtype=np.int8)
        barr[0] = -87
        barr[1] = 8
        barr[2] = 4
        i = self.rsp_random_num % 6
        if i == 0:
            barr[3] = random
            barr[4] = random2
            barr[5] = (random + random2) % 256
            barr[6] = (random * random2) % 256
        elif i == 1:
            barr[3] = random
            barr[4] = random2
            barr[5] = (random * random2) % 256
            barr[6] = (random + random2) % 256
        elif i == 2:
            barr[3] = (random + random2) % 256
            barr[4] = random
            barr[5] = random2
            barr[6] = (random * random2) % 256
        elif i == 3:
            barr[3] = (random * random2) % 256
            barr[4] = random
            barr[5] = random2
            barr[6] = (random + random2) % 256
        elif i == 4:
            barr[3] = (random + random2) % 256
            barr[4] = (random * random2) % 256
            barr[5] = random
            barr[6] = random2
        elif i == 5:
            barr[3] = (random * random2) % 256
            barr[4] = (random + random2) % 256
            barr[5] = random
            barr[6] = random2

        barr[7] = self.xor_result(barr, 0, 6)
        self.send_data_to_ble(barr)

    def send_query_speed_slope(self):
        log.debug("send_query_speed_slope")

    def send_reset_data_code(self):
        log.debug("send_reset_data_code")

    def send_hearbeat_code(self):
        log.debug("send_hearbeat_code")

    def send_check_resp_code_by_old(self):
        log.debug("send_check_resp_code_by_old")


