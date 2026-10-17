SLOW_START = "Slow Start"
CONGESTION_AVOIDANCE = "Congestion Avoidance"

class CongestionControl:
    def __init__(self, mss_init: int):
        #estado del control de congestion (slow_start o congestion_avoid)
        self.current_state = SLOW_START
        self.mss = mss_init #maximo de bytes de un segmento
        self.cwnd = self.mss #tamaño de la ventana de congestion en bytes (1 MSS)
        self.ssthresh = None #Slow start threshold
        self.debug = False

    def get_cwnd(self) -> bytes:
        return self.cwnd

    def get_MSS_in_cwnd(self) -> int:
        return self.get_cwnd() // self.mss

    def increase_cwnd(self, n):
        if self.debug: 
            print(f"increase_cwnd: [STATUS] cwnd={self.cwnd}, mss={self.mss}, ssthresh={self.ssthresh}, MSS en cwnd={self.get_MSS_in_cwnd()}, timeout counter={self.timeout_counter}")
            print(f"increase_cwnd: Sumandole {n} a cwnd={self.cwnd}")
        self.cwnd += n
        # Si se cumple la condicion, se cambia de slow_start a congestion avoidance
        if self.get_ssthresh() and self.get_cwnd() >= self.get_ssthresh() and self.is_state_slow_start():
            if self.debug: print("increase_cwnd: se cumple la condicion, cambiando status a CA")
            self.set_status(CONGESTION_AVOIDANCE)

    def event_ack_received(self):
        if self.debug: print(f"event_ack_received: [STATUS] cwnd={self.cwnd}, mss={self.mss}, ssthresh={self.ssthresh}, MSS en cwnd={self.get_MSS_in_cwnd()}")
        if self.is_state_slow_start():
            if self.debug: print("event_ack_received: Event ack received, Slow Start")
            self.increase_cwnd(self.mss)
        elif self.is_state_congestion_avoidance():
            if self.debug: print("event_ack_received: Event ack received, Congestion Avoidance")
            self.increase_cwnd((1/self.get_MSS_in_cwnd())*self.mss)

    def set_status(self, status):
        if self.debug: print(f"set_status: Cambiando status de {self.current_state} a {status}")
        self.current_state = status
        if status == SLOW_START:
            self.ssthresh = self.cwnd//2
            self.cwnd = self.mss # 1 MSS
        if self.debug: print(f"set_status: [STATUS] cwnd={self.cwnd}, mss={self.mss}, ssthresh={self.ssthresh}, MSS en cwnd={self.get_MSS_in_cwnd()}")


    def event_timeout(self):
       #La primera vez que se detecta timeout se setea el ssthresh = cwnd/2 y cwnd = 1 MSS.
        if self.is_state_slow_start():
            if self.debug: print("event_timeout: nos dio timeout con SS, re-seteamos SS.")
            self.set_status(SLOW_START)
        #Si ocurre un timeout se vuelve a slow start con ssthresh = cwnd/2 y cwnd = 1 MSS
        elif self.is_state_congestion_avoidance():
            if self.debug: print("event_timeout: nos dio timeout con CA, cambiamos a SS")
            self.set_status(SLOW_START) 
            

    def is_state_slow_start(self):
        if self.current_state == SLOW_START:
            return True
        else: 
            return False
    
    def is_state_congestion_avoidance(self):
        if self.current_state == CONGESTION_AVOIDANCE:
            return True
        else: 
            return False

    def get_ssthresh(self):
        return self.ssthresh
        
           

            

    