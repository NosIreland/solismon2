#    Project      : solismon2
#    Filename     : main
#    Created by   : Andrius Kozeniauskas
#    Created on   : 10/04/2021 17:39


from pyModbusTCP.client import ModbusClient
from prometheus_client import start_http_server, Summary, Info
from prometheus_client.core import GaugeMetricFamily, REGISTRY
import sys, time, logging
import paho.mqtt.client as mqtt

# MODBUS server IP, port, timeout
MODBUS_SERVER = "XXX.XXX.XXX.XXX"
MODBUS_PORT = 502
MODBUS_TIMEOUT = 7

c = ModbusClient(MODBUS_SERVER, MODBUS_PORT, timeout=MODBUS_TIMEOUT)
c.host(MODBUS_SERVER)
c.port(MODBUS_PORT)
c.unit_id(1)
c.auto_close(False)


# MODBUS debug message
#c.debug(True)

# How often to check(does not apply on prometheus)
check_interval = 60

# MQTT server IP, port, topic, keepalive
MQTT_SERVER = "XXX.XXX.XXX.XXX"
MQTT_PORT = 1883
MQTT_TOPIC = "/solis"
MQTT_KEEPALIVE = 60

# MODBUS Registers, prometheus name and description
all_regs = (
    (33030, (
        ('total_generation', 'Total Generation(kWh)'),
        ('not_used', 'Not Used'),
        ('generated_this_month', 'Generated This Month(kWh)'),
        ('not_used', 'Not Used'),
        ('generated_last_month', 'Generated Last Month(kWh)'),
        ('generated_today', 'Generated Today(0.1kWh)'),
        ('generated_yesterday', 'Generated Yesterday(0.1kWh)'),
        ('not_used', 'Not Used'),
        ('generated_this_year', 'Generated This Year(kWh)'),
        ('not_used', 'Not Used'),
        ('generated_last_year', 'Generated Last Year(kWh)'))),
    (33049, (
        ('dc_voltage_1', 'DC Voltage 1(0.1V)'),
        ('dc_current_1', 'DC Current 1(0.1A)'),
        ('dc_voltage_2', 'DC Voltage 2(0.1V)'),
        ('dc_current_2', 'DC Current 2(0.1A)'))),
    (33057, (
        ('not_used', 'Not Used'),
        ('total_dc_output_power', 'Total DC Output Power(W)'))),
    (33071, (
        ('dc_bus_voltage', 'DC bus Voltage(0.1V)'),
        ('not_used', 'Not Used'),
        ('phase_a_voltage', 'Phase A Voltage(0.1V)'),
        ('not_used', 'Not Used'),
        ('not_used', 'Not Used'),
        ('phase_a_current', 'Phase A Current(0.1A)'))),
    (33080, (
        ('active_power', 'Active Power(W)'),
        ('not_used', 'Not Used'),
        ('reactive_power', 'Reactive power(W)'),
        ('not_used', 'Not Used'),
        ('apparent_power', 'Apparent Power(VA)'))),
    (33091, (
        ('standard_working_mode', 'Standard Working Mode'),
        ('national_standard', 'National Standard'),
        ('inverter_temperature', 'Inverter Temperature(0.1C)'),
        ('grid_frequency', 'Grid Frequency(0.01Hz'),
        ('current_state_of_inverter', 'Current State Of Inverter'))),
    (33104, (
        ('actual_power_limit', 'Actual Power Limit(0.01%)'),
        ('actual_power', 'Actual Power(0.01)'))),
    (33115, (
        ('set_the_flag_bit', 'Set The Flag Bit'),
        ('fault_code_01', 'Fault Code 01'),
        ('fault_code_02', 'Fault Code 02'),
        ('fault_code_03', 'Fault Code 03'),
        ('fault_code_04', 'Fault Code 04'),
        ('fault_code_05', 'Fault Code 05'),
        ('working_status', 'Working Status'))),
    (33126, (
        ('electricity_meter_total_active_power_generation_1', 'Electricity Meter Total Active Power Generation 1(Wh)'),
        ('electricity_meter_total_active_power_generation_2', 'Electricity Meter Total Active Power Generation 2(Wh)'),
        ('meter_voltage', 'Meter Voltage(0.1V)'),
        ('meter_current', 'Meter Current(0.1A)'),
        ('meter_active_power_1', 'Meter Active Power 1(0.1W)'),
        ('meter_active_power_2', 'Meter Active Power 2(0.1W)'),
        ('energy_storage_control_switch', 'Energy Storage Control Switch'),
        ('battery_voltage', 'Battery Voltage(0.1V)'),
        ('battery_current', 'Battery Current(0.1A)'),
        ('battery_current_direction', 'Battery Current_Direction(0=Charging, 1=Discharging'),
        ('llcbus_voltage', 'LLCbus Voltage(0.1V)'),
        ('bypass_ac_voltage', 'Bypass AC Voltage(0.1V)'),
        ('bypass_ac_current', 'Bypass AC Current(0.1A)'),
        ('battery_capacity_soc', 'Battery Capacity SOC(%)'),
        ('battery_health_soh', 'Battery Health SOH(%)'),
        ('battery_voltage', 'Battery Voltage(0.01V)'),
        ('battery_current', 'Battery Current(0.01A)'),
        ('battery_charge_current_limit', 'Battery Charge Current Limit(0.1A)'),
        ('battery_discharge_current_limit', 'Battery Discharge Current Limit(0.1A)'),
        ('battery_failure_info_01', 'Battery Failure Information 01'),
        ('battery_failure_info_02', 'Battery Failure Information 02'),
        ('house_load_power', 'House Load Power(W)'),
        ('bypass_load_power', 'Bypass Load Power(W)'),
        ('battery_power_1', 'Battery Power 1(W)'),
        ('battery_power_2', 'Battery Power 2(W)'))),
    (33161, (
        ('total_battery_charge_1', 'Total Battery Charge 1(kWh)'),
        ('total_battery_charge_2', 'Total Battery Charge 2(kWh)'),
        ('battery_charge_today', 'Battery Charge Today(0.1kWh)'),
        ('battery_charge_yesterday', 'Battery Charge Yesterday(0.1kWh)'),
        ('total_battery_discharge_1', 'Total Battery Discharge 1(kWh)'),
        ('total_battery_discharge_2', 'Total Battery Discharge 2(kWh)'),
        ('battery_discharge_capacity', 'Battery Discharge Capacity(0.1kWh)'),
        ('battery_discharge_power_yesterday', 'Battery Discharge Power Yesterday(0.1kWh)'),
        ('total_imported_power_1', 'Total Imported Power 1(kWh)'),
        ('total_imported_power_2', 'Total Imported Power 2(kWh)'),
        ('grid_power_imported_today', 'Grid Power Imported Today(0.1kWh)'),
        ('grid_power_imported_yesterday', 'Grid Power Imported Yesterday(0.1kWh)'),
        ('total_exported_power_1', 'Total Exported Power 1(kWh)'),
        ('total_exported_power_2', 'Total Exported Power 2(kWh)'),
        ('grid_power_exported_today', 'Grid Power Exported Today(0.1kWh)'),
        ('grid_power_exported_yesterday', 'Grid Power Exported Yesterday(0.1kWh)'),
        ('total_house_load_1', 'Total House Load 1(kWh)'),
        ('total_house_load_2', 'Total House Load 2(kWh)'),
        ('house_load_today', 'House Load Today(0.1kWh)'),
        ('house_load_yesterday', 'House Load Yesterday(0.1kWh)'))),
    (33251, (
        ('meter_ac_voltage_a', 'Meter AC Voltage A(0.1V)'),
        ('meter_ac_current_a', 'Meter AC Current A(0.01A)'),
        ('meter_ac_voltage_b', 'Meter AC Voltage B(0.1V)'),
        ('meter_ac_current_b', 'Meter AC Current B(0.01A)'),
        ('meter_ac_voltage_c', 'Meter AC Voltage C(0.1V)'),
        ('meter_ac_current_c', 'Meter AC Current C(0.01A)'),
        ('not_used', 'Not Used'),
        ('meter_active_power_a', 'Meter Active Active Power A(0.001kW)'),
        ('meter_active_power_b', 'Meter Active Active Power B(0.001kW)'),
        ('meter_active_power_c', 'Meter Active Active Power C(0.001kW)'),
        ('meter_total_active_power', 'Meter Total active Power(0.001kW)'))),
    (33266, (
        ('meter_reactive_power_a', 'Meter Active Reactive Power A(VA)'),
        ('meter_reactive_power_b', 'Meter Active Reactive Power B(VA)'),
        ('meter_reactive_power_c', 'Meter Active Reactive Power C(VA)'),
        ('meter_total_reactive_power', 'Meter Total Reactive Power(VA)'))),
    (33274, (
        ('meter_apparent_power_a', 'Meter Active Apparent Power A(VA)'),
        ('meter_apparent_power_b', 'Meter Active Apparent Power B(VA)'),
        ('meter_apparent_power_c', 'Meter Active Apparent Power C(VA)'),
        ('meter_total_apparent_power', 'Meter Total Apparent Power(VA)'))),
    (33281, (
        ('meter_power_factor', 'Meter Power Factor'),
        ('meter_grid_frequency', 'Meter Grid Frequency(0.01Hz)'),
        ('meter_total_active_imported_1', 'Meter Total Active Imported 1(0.01kWh)'),
        ('meter_total_active_imported_2', 'Meter Total Active Imported 2(0.01kWh)'),
        ('meter_total_active_exported_1', 'Meter Total Active Exported 1(0.01kWh)'),
        ('meter_total_active_exported_2', 'Meter Total Active Exported 2(0.01kWh)'))),
                )

i = Info('my_build_version', 'Description of info')
i.info({'version': '0.4'})

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')


class CustomCollector(object):
    def __init__(self):
        pass

    def collect(self):
        try:
            logging.info('Connecting to MQTT Server')
            mqttc = mqtt.Client()
            mqttc.connect(MQTT_SERVER, MQTT_PORT, MQTT_KEEPALIVE)
            mqttc.on_connect = logging.info("Connected to MQTT " + MQTT_SERVER + ":" + str(MQTT_PORT))

            logging.info('Connecting to MODBUS Server')
            if not c.is_open():
                if not c.open():
                    logging.error("unable to connect to MODBUS " + MODBUS_SERVER + ":" + str(MODBUS_PORT))
                else:
                    logging.info("Connected to MODBUS " + MODBUS_SERVER + ":" + str(MODBUS_PORT))

            logging.info('Scraping...')
            for r in all_regs:
                reg = r[0]
                reg_len = len(r[1])
                reg_des = r[1]

                if c.is_open():
                    # read registers at address , store result in regs list
                    regs = c.read_input_registers(reg, reg_len)
                    # if success display registers
                    if regs:
                        logging.debug("reg ad #" + str(reg) + " length " + str(reg_len))
                        logging.debug(regs)

                    for (i, item) in enumerate(regs):
                        if reg_des[i][0] != 'not_used':
                            logging.debug(i, item, reg_des[i][0], reg_des[i][1])
                            yield GaugeMetricFamily(reg_des[i][0], reg_des[i][1], value=item)
                            mqttc.publish(MQTT_TOPIC + '/' + str(reg_des[i][0]), item)

            mqttc.disconnect()
            c.close()
            logging.info('Scraped')
        except Exception as e:
            logging.error('Cannot scrape: ', repr(e))
            sys.exit(1)


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])

        logging.info('Starting Web Server')
        start_http_server(18000)
        REGISTRY.register(CustomCollector())
        while True:
            time.sleep(check_interval)

    except Exception as e:
        logging.error('Cannot start: ', repr(e))
        sys.exit(1)
