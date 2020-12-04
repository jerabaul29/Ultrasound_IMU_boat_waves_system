/*
  - code for controlling and logging the QT50UBL sensor.
  - output is set to analog voltage, taken to 5V by a divider of tension (2 x 4.16 k Ohm)
  - control is set to the tare wire configured for taring; it is wired as (to allow to control from
  a 5V board, given its 7V default high with a 13.2V power supply and 12 k Ohm ampedance):
    gray wire ------------ resistor 25 k Ohm --------------- ground
                    |
                    |
                  digital control pin

  - special characters used for the simple protocol by serial:
  -- M: message
  -- S: start of a reading
  -- E: end of a reading
  -- L: too late compared to schedule
*/

#define PIN_MEAS A15
#define LOGGING_PERIOD_MS 20UL

#define PIN_TARE 5

#define SERIAL_OUT Serial
#define BAUD_RATE 57600

#define TARE_PULSE_MS 100  // duration of a tare pulse high or low
#define TARE_RESPONSE_TIME_MS 2000UL  // time it takes the sensor to answer a tare command

unsigned short gauge_reading;
unsigned long time_last_read;
char crrt_char;

unsigned long measurement_nbr = 0;

struct gauges_data {
  unsigned long reading_time;
  unsigned short reading_value;
  unsigned long measurement_nbr;
};

gauges_data gauges_data_instance;

static const int len_gauges_data_instance = sizeof(gauges_data_instance);

void setup(){
  SERIAL_OUT.begin(BAUD_RATE);
  delay(100);

  SERIAL_OUT.print(F("\nM Booted\n"));
  SERIAL_OUT.print(F("struct size: "));
  SERIAL_OUT.println(len_gauges_data_instance);

  pinMode(PIN_TARE, INPUT);  // let the pin float high when not in use

  time_last_read = millis();
}

void loop(){

  // check if time to measure
  if (millis() - time_last_read > LOGGING_PERIOD_MS){
    time_last_read += LOGGING_PERIOD_MS;
    read_and_print();

    if (millis() - time_last_read > LOGGING_PERIOD_MS){
      Serial.print("L");
    }
  }

  // check if some commands
  if (SERIAL_OUT.available() > 0){
    crrt_char = SERIAL_OUT.read();
    
    if (crrt_char == 'T'){
      tare_around_position();
    }
  }

}

void read_and_print(void){
  /*
    Read and print on serial the ultrasonic gauge reading.
    Print in plain ascii for ease: no need for high speed anyway.
  */
  gauge_reading = analogRead(PIN_MEAS);
  measurement_nbr += 1;

  gauges_data_instance.reading_time = millis();
  gauges_data_instance.reading_value = gauge_reading;
  gauges_data_instance.measurement_nbr = measurement_nbr;

  SERIAL_OUT.print("S");
  Serial.write((uint8_t *)&gauges_data_instance, len_gauges_data_instance);
  SERIAL_OUT.print("E\n");
}

void tare_around_position(void){
  /*
    Tare the gauge using the autotare feature, ie a 1m window centered on
    the position taught, using the gray wire.
  */

  SERIAL_OUT.print(F("\n\nM start taring...\n"));

  // phase 1: autotare min position
  low_tare_pulse(3);
  
  // let the sensor the time to react
  delay(TARE_RESPONSE_TIME_MS);

  // phase 2: autotare max position
  low_tare_pulse(3);

  // let the sensor the time to react
  delay(TARE_RESPONSE_TIME_MS);

  SERIAL_OUT.print(F("M done taring!\n"));

  // avoid timing problems
  time_last_read = millis();
}

void low_tare_pulse(unsigned int number_of_pulses){
  for (unsigned int i=0; i<number_of_pulses; i++){
    // put low
    pinMode(PIN_TARE, OUTPUT);
    digitalWrite(PIN_TARE, LOW);
    delay(TARE_PULSE_MS);

    // float high
    pinMode(PIN_TARE, INPUT);
    delay(TARE_PULSE_MS);
  }

}