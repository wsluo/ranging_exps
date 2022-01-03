cc2538_on_and_transmit()在contiki的cc2538-opo中定义 
// https://github.com/lab11/contiki/blob/cc2538-opo/cpu/cc2538/dev/cc2538-rf.c
//https://github.com/lab11/opo/blob/1010ea87a4fe4d11ff43be1e50c0a999731cf444/contiki/dev/vtimer/vtimer.c
vtimer get_vtimer(void *c): Returns a vtimer using c as callback
	
绿灯tx
蓝灯rx

opo的range由等待时间参数确定
	
A 10 ms ultrasonic wakeup window covers approximately 3 m of ranging

cc2538_on_and_transmit(tx_start_time);

wakeup_callback : ul_wakeup_time = VTIMER_NOW();

static void rx_sfd_callback() {
	if(opo_state == OPO_RX && sfd_time == 0) { sfd_time = VTIMER_NOW(); }
}

uint32_t diff = (uint32_t) (sfd_time - ul_wakeup_time);
rxmsg.range_dt = (uint32_t)(rxmsg_storage.ul_rf_dt - diff); 


unsigned short delaytime = generate_rand_tx(); 一个小于2000的值


tx_delay_callback : process_poll(&opo8001tx);


### 没有sensor 没有peer:
if(opo_state == OPO_RX) {
	send_rf_debug_msg("opo.c: perform_opo_tx fail OPO_RX\n");
}

opo noise (32)
perform opo tx (33)
opo tx stage 0 (34)
opo tx stage 1 (34)
opo tx stage 2 (34)
rx reset (35)
opo tx failed woo(36)
(44)
restart vt_callback(46)
opo perform tx success (49)
perform_opo_tx fail OPO_RX (53)
opo rx restart process fail (54)
perform_opo_tx fail OPO_RX_RF (56)
opo rx restart success (57)
		
### 没有sensor 有peer 一样？

### 有sensor 有peer 
RX DIFF 84 335 (38)
rx complete (39)
opo rx process reenable (43)
opo rx first stage (45)
opo rx did not get rf packet (55)  大量, 不是false wakeup但是没有接收到rf packet。wakeup的ul count的阈值是40
opo Rx Timing 249, time: xxxxxxxx （少量）



### 有sensor 没peer
opo rx first stage (45)
opo rx did not get rf packet (55) 罕见




volatile static opo_rmsg_t  txmsg;
volatile static opo_data_t  rxmsg;
static opo_rmsg_t           rxmsg_storage;
static opo_meta_t           meta;

rxmsg.tx_id = rxmsg_storage.id;
rxmsg.tx_unixtime = rxmsg_storage.unixtime;
//rxmsg.tx_time_confidence = rxmsg_storage.time_confidence;
rxmsg.m_unixtime = rtc_get_unixtime();
//rxmsg.m_time_confidence = meta.time_confidence;
rxmsg.range_dt = (uint32_t)(rxmsg_storage.ul_rf_dt - diff);  #### range_dt的计算！ diff = sfd_time - ul_wakeup_time
rxmsg.failed_rx_count = failed_rx_count;
txmsg.last_interaction_partner_id = rxmsg.tx_id;

txmsg.last_unixtime = rxmsg.m_unixtime;
txmsg.last_range_dt = rxmsg.range_dt;
txmsg.failed_rx_count = failed_rx_count;




enable_opo_rx()之中调用setup_opo_rx()
setup_opo_rx()中设置rf_rx_callback,rf_packet_received 设为true是在rf_rx_callback()中
setup_opo_rx()中设置rx_sfd_callback,rx_sfd_callback()中获取sfd_time = VTIMER_NOW(); 

[vtimer_now defined in cc2538-opo contiki. timer in ticks!!!!!!!!!!]


收到noise的时候
self_reset_rx = true 重新调用 enable_opo_rx()
	
wakeup callback的时候ul_count++, 如果是初始wakeup, 则 schedule_vtimer_ms(&rx_ul_counter_vt, 2)。2ms后检查ul_count
opo_rx_ul_count_checker()中检查ul_count，小于40的时候noise=true然后ul_count归零

wakeup callback (注册在rx的gpio下)
if(opo_state == OPO_IDLE) {
	ul_wakeup_time = VTIMER_NOW();
	sfd_time = 0;
	opo_state = OPO_RX;
	ul_count++;
	schedule_vtimer_ms(&rx_ul_counter_vt, 2);
	//process_poll(&opo_rx);
}
else if(opo_state == OPO_RX) {
	ul_count++;
}





#### paper中的RX 过程（A版）
收到wakeup
waitRX，收到rf和ul

#### paper中的TX 过程（A版）
enable_opo_ul_tx();
发送wake up
waitTX发送rf和ul
	
waitTX和waitRX的差是预计的超声传播时间


void cc2538_ant_enable() {} is empty
tx_sfd_callback 为空
	
	
	
	
	
static void opo_rx_ul_count_checker() {
	GPIO_DISABLE_INTERRUPT(OPO_RX_PORT_BASE, OPO_RX_PIN_MASK);
	GPIO_DISABLE_POWER_UP_INTERRUPT(OPO_RX_PORT_NUM, OPO_RX_PIN_MASK);
	GPIO_CLEAR_INTERRUPT(OPO_RX_PORT_BASE, OPO_RX_PIN_MASK);
	GPIO_CLEAR_POWER_UP_INTERRUPT(OPO_RX_PORT_NUM, OPO_RX_PIN_MASK);
	if(ul_count < 40) {
		transmission_noise = true;
	}
	ul_count = 0;
	process_poll(&opo_rx);
}


static void rf_rx_callback() {
	INTERRUPTS_DISABLE();
	/* Check to make sure we are in expected Opo state */
	if(opo_state == OPO_RX) {
		/* If packet length and preamble check out, process packet for Opo ranging event */
		uint16_t packet_length = packetbuf_datalen();
		if(packet_length == sizeof(opo_rmsg_t)) {
			/* We have to copy data out of the packetbuf before checking the preamble */
			packetbuf_copyto((void *) &rxmsg_storage);
			packetbuf_clear();
			if(rxmsg_storage.preamble == (uint16_t) ~(rxmsg_storage.id)) { // need cast because C or shitty compiler
				NETSTACK_MAC.off(0);
				cancel_vtimer(&rx_vt);
				opo_state = OPO_RX_RF;
				rf_packet_received = true;
				process_poll(&opo_rx);
			}
		}
	}
	INTERRUPTS_ENABLE();
}


static void rx_vt_callback() {
	if(opo_state == OPO_RX) {
		//send_rf_debug_msg("opo.c: opo rx vt failsafe");
		opo_state = OPO_RX_RF;
		NETSTACK_MAC.off(0);
		process_poll(&opo_rx);
	}
	else {
		//send_rf_debug_msg("opo.c: rx vt failsafe fail");
	}
}	