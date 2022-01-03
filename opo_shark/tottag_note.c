//---------------------------------------external RTC chit-------------------------------------------//
void ab1815_printTime(ab1815_time_t time)
{
   printf("INFO: Time is %02u:%02u:%02u, 20%02u/%02u/%02u\n", time.hours, time.minutes, time.seconds, time.years, time.months, time.date);
}
#endif  // #if (BOARD_V >= 0x0F)

uint8_t ab1815_init_time(void){
//取得屏幕时间储存在comp_time中
return ab1815_set_time(comp_time);
}


//Thu Dec  9 02:49:49 UTC 2021 ->  45:85:85, 20165/25/45

ab1815_time_t comp_time;
comp_time.hundredths = 0;
comp_time.seconds = ascii_to_i(_datetime[17]) * 10 + ascii_to_i(_datetime[18]);//yes!
comp_time.minutes = ascii_to_i(_datetime[14]) * 10 + ascii_to_i(_datetime[15]);//yes!
comp_time.hours = ascii_to_i(_datetime[11]) * 10 + ascii_to_i(_datetime[12]);//yes!

comp_time.date = ascii_to_i(_datetime[8]) * 10 + ascii_to_i(_datetime[9]);//yes!
comp_time.months = month_to_i(&_datetime[4]);//yes!
comp_time.years = ascii_to_i(_datetime[26]) * 10 + ascii_to_i(_datetime[27]);//yes!
comp_time.weekday = 0;  // default


// Initialize time
success = (success && ab1815_init_time());

// Set nRF time from the RTC
ab1815_time_t time = { 0 };
success = (success && ab1815_get_time(&time)); //time是储存在comp_time中的时间set了之后又读出来的
if (success)
{
  rtc_set_current_time(ab1815_to_unix(time).tv_sec);
  ab1815_printTime(time);
}
   
   
//time_bufffer
buf[0] = (get_tens(time.hundredths) & 0xF) << 4 | (get_ones(time.hundredths) & 0xF);
buf[1] = (get_tens(time.seconds) & 0x7) << 4 | (get_ones(time.seconds) & 0xF);
buf[2] = (get_tens(time.minutes) & 0x7) << 4 | (get_ones(time.minutes) & 0xF);
buf[3] = (get_tens(time.hours) & 0x3) << 4 | (get_ones(time.hours) & 0xF);
buf[4] = (get_tens(time.date) & 0x3) << 4 | (get_ones(time.date) & 0xF);
buf[5] = (get_tens(time.months) & 0x1) << 4 | (get_ones(time.months) & 0xF);
buf[6] = (get_tens(time.years) & 0xF) << 4 | (get_ones(time.years) & 0xF);
buf[7] = time.weekday & 0x7;



//older version reset rtc
00> WARNING: Chip experienced a reset with reason 2
00> INFO: Initializing nRF...
00> INFO: Bluetooth address: c0:98:e5:42:00:22
00> INFO: Initialized critical hardware and software services
00> INFO: Time is 03:51:09, 2020/12/09
00> ERROR: RTC chip returned an impossible Unix timestamp: 1607485869
00> INFO: Time is 00:00:00, 2000/00/00
00> ERROR: RTC chip returned an impossible Unix timestamp: 943920001
00> INFO: Time is 00:00:00, 2000/00/00
00> INFO: Initialized supplementary hardware and software services
00> INFO: Device is NOT PLUGGED IN and NOT CHARGI
	
	
rtc_get_current_time() //the rtc on nrf (1815 is the external rtc)
	
rtc_set_current_time(epoch);//in main.c, rtc is set to the epoch time	
	
	
	
   // If the SquarePoint module appears to have crashed, try to reset it and re-discover networks
    if (app_enabled && nrfx_atomic_flag_fetch(&_app_flags.squarepoint_running) &&
          (nrfx_atomic_u32_fetch(&_app_flags.squarepoint_timeout_counter) > APP_RUNNING_RESPONSE_TIMEOUT_SEC))
    {
       // Update the app state and reset the SquarePoint module
       log_printf("INFO: SquarePoint communications appear to be down...restarting\n");
       nrfx_atomic_flag_clear(&_app_flags.squarepoint_running);
       ble_clear_scheduler_eui();
       squarepoint_stop();
       sd_card_flush();
    }	
	
	
///------------------------SD CARD SHIT---------------------------//	
	
https://github.com/lab11/socitrack/blob/b37943e657a87f93c0fe3445ccf5c4598db52a13/software/tottag/firmware/peripherals/src/sd_card.c

void sd_card_log_ranges(const uint8_t *data, uint16_t length)
	
	
//when called in main.c: sd_card_log_motion(true, rtc_get_current_time(), false);	
void sd_card_log_motion(bool in_motion, uint32_t current_time, bool flush)
{
   // Start a new log file if it is a new day
   if (_next_day_timestamp && (current_time >= _next_day_timestamp))
   {
      printf("INFO: Starting new SD card log file...new day detected\n");
      sd_card_create_log(current_time, false);
   }

   printf("INFO: Device is now %s\n", in_motion ? "IN MOTION" : "STATIONARY");
   uint16_t bytes_written = (uint16_t)snprintf(_sd_write_buf, sizeof(_sd_write_buf), "### MOTION CHANGE: %s; Timestamp: %lu\n", in_motion ? "IN MOTION" : "STATIONARY", current_time);
   sd_card_write(_sd_write_buf, bytes_written, flush);
}


//when the buffer is about to be full, automatically flush even when the flush tag is set to false
void sd_card_write(const char *data, uint16_t length, bool flush)
{
   // Flush the buffer if necessary
   if (((APP_SDCARD_BUFFER_LENGTH - _sd_card_buffer_length - 1) <= length) && !sd_card_flush()) 
	   //#define APP_SDCARD_BUFFER_LENGTH                10240
	   //#define APP_BLE_BUFFER_LENGTH                   256   buffer every 256 data points?
      return;

   // Append data to the buffer
   memcpy(_sd_card_buffer + _sd_card_buffer_length, data, length);
   _sd_card_buffer_length += length;

   // Flush the buffer if requested
   if (flush)
      sd_card_flush();
}



bool sd_card_flush(void)
{
   // Ensure that there is data to flush
   if (!_sd_card_buffer_length) // length == 0
      return true;

   // Power ON the SD card
   if (!sd_card_power_on()) //power is off
   {
      printf("ERROR: Unable to power on the SD Card!\n");
      sd_card_power_off();
      return false;
   }

   // Send data in chunks of 254 bytes, as this is the maximum which the nRF DMA can handle
   uint8_t nr_writes = (_sd_card_buffer_length / (sizeof(_sd_write_buf) - 1)) + ((_sd_card_buffer_length % (sizeof(_sd_write_buf) - 1)) ? 1 : 0);
   for (uint8_t i = 0; i < nr_writes; ++i)
   {
      // Copy chunks to the write buffer and log data
      if (i == (nr_writes - 1))             // Last chunk
      {
         uint8_t rest_length = _sd_card_buffer_length - (i * (sizeof(_sd_write_buf) - 1));
         memcpy(_sd_write_buf, _sd_card_buffer + (i * (sizeof(_sd_write_buf) - 1)), rest_length);
         _sd_write_buf[rest_length] = '\0';
      }
      else
      {
         memcpy(_sd_write_buf, _sd_card_buffer + (i * (sizeof(_sd_write_buf) - 1)), sizeof(_sd_write_buf) - 1);
         _sd_write_buf[sizeof(_sd_write_buf)-1] = '\0';
      }

      // Attempt to write the data string to the SD card
      if ((f_puts(_sd_write_buf, &_file) < 0) || (f_sync(&_file) != FR_OK))
         printf("ERROR: Problem writing data to the SD card!\n");
   }

   // Reset the buffer and turn off power to the SD card
   _sd_card_buffer_length = 0;
   sd_card_power_off();
   return true;
}

//----------------------------BLE address SHIT-----------------------------------//

//what is _networked_device_addr???
static ble_gap_addr_t _wl_addr_base = { 0 }, _networked_device_addr = { 0 };


ble_request_timestamp: get timestamp from _networked_device_addr
	
	
	
//--------------------------squarepoint SHIT------------------------------------//
static void squarepoint_data_handler(uint8_t *data, uint32_t len) 
	//data[0] indicates case swtich
	//data[1]: number of ranges
	
squarepoint_init(&_app_flags.squarepoint_data_received, squarepoint_data_handler, ble_get_eui()) == NRFX_SUCCESS)
	
// https://github.com/lab11/socitrack/blob/5ef57259f063636ddd6170be992901630390e954/software/tottag/firmware/peripherals/src/squarepoint_interface.c
	
	
// Use 30 broadcasts per device for ranging: (3 channels * 3 antennas on requester * 3 antennas on responder) + 3
#define NUM_RANGING_BROADCASTS ((NUM_RANGING_CHANNELS*NUM_ANTENNAS*NUM_ANTENNAS) + NUM_RANGING_CHANNELS)
static uint64_t _rx_TOAs[NUM_RANGING_BROADCASTS];	

//Take the median range as the final range estimate

//id and ranges stored in ids_and_ranges(buffer)
uint8_t perform_ranging(uint8_t *ids_and_ranges, PROTOCOL_EUI_TYPE *expected_devices, uint8_t expected_devices_len)
	
//output_buffer_index initialized as 1, the first element saves the number of ranges in the end	
ids_and_ranges[0] = _state.num_ranges;
	
#define MIN_VALID_RANGES_PER_DEVICE 8
	
//NORMAL: there are NUM_RANGING_BROADCASTS  ranging msgs, of which MIN_VALID_RANGES_PER_DEVICE ranges have to be valid. the valid ranges are sorted, then the median value is taken
	
	
// in scheduler.c
	
#define PACKET_SINGLE_RESULT_LENGTH      (PROTOCOL_EUI_SIZE + sizeof(int32_t)) //modify:  sizeof(int32_t)* NUM_RANGING_BROADCASTS 
	
static uint8_t ids_and_ranges[((PROTOCOL_MAX_NUM_RESPONDERS + PROTOCOL_MAX_NUM_HYBRIDS) * PACKET_SINGLE_RESULT_LENGTH) + 1 + sizeof(_schedule_packet.epoch_time_unix)];

_num_successful_ranges = perform_ranging(ids_and_ranges, _expected_valid_ranges, _num_expected_valid_ranges);
memcpy(scratch_ranges, ids_and_ranges, 1 + (ids_and_ranges[0] * PACKET_SINGLE_RESULT_LENGTH));
 
static PROTOCOL_EUI_TYPE _expected_valid_ranges[PROTOCOL_MAX_NUM_RESPONDERS + PROTOCOL_MAX_NUM_HYBRIDS]; 

//keep-alive message to the host
host_interface_notify_ranges(ids_and_ranges, 1 + PROTOCOL_EUI_SIZE + sizeof(_schedule_packet.epoch_time_unix));
//error correction phase, everything is copied in the original version, no worry
ids_and_ranges[0] = scratch_ranges[0];
memcpy(ids_and_ranges + 1, &_schedule_packet.scheduler_eui, PROTOCOL_EUI_SIZE);
memcpy(ids_and_ranges + 1 + PROTOCOL_EUI_SIZE, scratch_ranges + 1, scratch_ranges[0] * PACKET_SINGLE_RESULT_LENGTH);
memcpy(ids_and_ranges + 1 + PROTOCOL_EUI_SIZE + (ids_and_ranges[0] * PACKET_SINGLE_RESULT_LENGTH), &_schedule_packet.epoch_time_unix, sizeof(_schedule_packet.epoch_time_unix));
host_interface_notify_ranges(ids_and_ranges, 1 + PROTOCOL_EUI_SIZE + (ids_and_ranges[0] * PACKET_SINGLE_RESULT_LENGTH) + sizeof(_schedule_packet.epoch_time_unix));

//in host_interface.c
void host_interface_notify_ranges(uint8_t *ids_ranges, uint8_t len)
	
scratch_ranges
	
	
//structure of ids_and_ranges??? normal mode
// 0: number   then: _schedule_packet.scheduler_eui  body:response->responder_eui+range, end: timestamp 
	

//on rx side. on the tx side, the bit is set in txBuffer[1]
#define SQUAREPOINT_INCOMING_RANGES                     0x01
#define SQUAREPOINT_INCOMING_CALIBRATION                0x02
#define SQUAREPOINT_INCOMING_WAKEUP                     0x03
#define SQUAREPOINT_INCOMING_STOPPED                    0x04
#define SQUAREPOINT_INCOMING_REQUEST_TIME               0x05
#define SQUAREPOINT_INCOMING_PING                       0x06
	
	
//ble_config.h	
#define APP_LOG_RANGE_LENGTH                    (SQUAREPOINT_EUI_LEN + 4)
	//=> change to 
#define SQUAREPOINT_RX_COUNT                    30 //created for receiving more data
#define APP_LOG_RANGE_LENGTH                    (SQUAREPOINT_EUI_LEN + 4 * SQUAREPOINT_RX_COUNT )
	
//main.c
_range_buffer_length = (uint16_t)MIN(len - 1, APP_BLE_BUFFER_LENGTH);
memcpy(_range_buffer, data + 1, _range_buffer_length);

// Check if new ranging data was received
if (nrfx_atomic_flag_clear_fetch(&_app_flags.range_buffer_updated))
{
   sd_card_log_ranges(_range_buffer, _range_buffer_length);
   ble_update_ranging_data(_range_buffer, _range_buffer_length); //what is this doing?
}

ble_update_ranging_data //TODO: need modifying? in bluetooth.c
	
	
//ranging data first saved in ids_and_ranges, then copied to scratch_ranges, then use received results to update	
	
	
//modification list
ranging.c
scheduler.c
scheduler.h	
host_interface.c
ble.config.h
main.c