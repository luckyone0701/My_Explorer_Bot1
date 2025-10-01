#!/usr/bin/env python3
"""
Robot Server for EduBot Explorer
"""

import socket
import json
import RPi.GPIO as GPIO
import time
import threading
import signal
import sys
from datetime import datetime

class RealEduBot:
    def __init__(self):
        print("Initializing RealEduBot with enhanced controls...")
        
        self.MOTOR_LEFT_FORWARD = 17
        self.MOTOR_LEFT_BACKWARD = 18
        self.MOTOR_RIGHT_FORWARD = 22
        self.MOTOR_RIGHT_BACKWARD = 23
        
        self.TRIGGER_PIN = 24
        self.ECHO_PIN = 25
        
        self.is_moving = False
        self.current_direction = None
        self.auto_mode = False
        
        self.setup_gpio()
        print("Enhanced GPIO setup completed")
    
    def setup_gpio(self):
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            
            motor_pins = [
                self.MOTOR_LEFT_FORWARD, self.MOTOR_LEFT_BACKWARD,
                self.MOTOR_RIGHT_FORWARD, self.MOTOR_RIGHT_BACKWARD
            ]
            
            for pin in motor_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            
            GPIO.setup(self.TRIGGER_PIN, GPIO.OUT)
            GPIO.setup(self.ECHO_PIN, GPIO.IN)
            GPIO.output(self.TRIGGER_PIN, GPIO.LOW)
            
            print("All pins initialized successfully")
            
        except Exception as e:
            print(f"GPIO setup error: {e}")
    
    def emergency_stop(self):
        try:
            print("EMERGENCY STOP - Immediate halt!")
            self.stop_motors()
            self.is_moving = False
            self.current_direction = None
            self.auto_mode = False
            
            return {"status": "success", "message": "Emergency stop executed"}
        except Exception as e:
            return {"status": "error", "message": f"Stop error: {e}"}
    
    def smart_stop(self):
        try:
            print("Smart stop with gradual slowdown")
            
            if self.is_moving and self.current_direction:
                for i in range(3, 0, -1):
                    if self.current_direction == "forward":
                        self.move_forward(duration=0.1)
                    elif self.current_direction == "backward":
                        self.move_backward(duration=0.1)
                    elif self.current_direction == "left":
                        self.turn_left(duration=0.05)
                    elif self.current_direction == "right":
                        self.turn_right(duration=0.05)
                    time.sleep(0.1)
            
            self.stop_motors()
            self.is_moving = False
            self.current_direction = None
            
            return {"status": "success", "message": "Smart stop completed"}
        except Exception as e:
            return {"status": "error", "message": f"Smart stop error: {e}"}
    
    def start_autonomous_navigation(self, target_data=None):
        try:
            print("Starting autonomous navigation mode")
            self.auto_mode = True
            
            if target_data:
                target_x = target_data.get('target_x')
                target_y = target_data.get('target_y')
                print(f"Target coordinates: ({target_x}, {target_y})")
            
            autonomous_response = {
                "status": "success",
                "message": "Autonomous navigation started",
                "mode": "autonomous",
                "target": target_data,
                "sensor_data": self.get_sensor_data()
            }
            
            return autonomous_response
            
        except Exception as e:
            return {"status": "error", "message": f"Autonomous start error: {e}"}
    
    def stop_autonomous_navigation(self):
        try:
            print("Stopping autonomous navigation")
            self.auto_mode = False
            self.stop_motors()
            
            return {
                "status": "success", 
                "message": "Autonomous navigation stopped",
                "final_sensor_data": self.get_sensor_data()
            }
        except Exception as e:
            return {"status": "error", "message": f"Autonomous stop error: {e}"}
    
    def autonomous_obstacle_avoidance(self):
        try:
            distance = self.get_distance()
            
            if distance < 15:
                print("Obstacle detected! Avoiding...")
                self.stop_motors()
                time.sleep(0.5)
                
                self.turn_right(duration=0.3)
                right_distance = self.get_distance()
                
                self.turn_left(duration=0.6)
                left_distance = self.get_distance()
                
                if right_distance > left_distance and right_distance > 20:
                    self.turn_right(duration=0.3)
                    print("Turning right - clearer path")
                else:
                    print("Turning left - clearer path")
                
                return True
            return False
            
        except Exception as e:
            print(f"Obstacle avoidance error: {e}")
            return False
    
    def move_forward(self, duration=0.5):
        try:
            print("Moving forward")
            self.stop_motors()
            GPIO.output(self.MOTOR_LEFT_FORWARD, GPIO.HIGH)
            GPIO.output(self.MOTOR_RIGHT_FORWARD, GPIO.HIGH)
            
            self.is_moving = True
            self.current_direction = "forward"
            
            time.sleep(duration)
            self.stop_motors()
            
        except Exception as e:
            print(f"Move forward error: {e}")
    
    def move_backward(self, duration=0.5):
        try:
            print("Moving backward")
            self.stop_motors()
            GPIO.output(self.MOTOR_LEFT_BACKWARD, GPIO.HIGH)
            GPIO.output(self.MOTOR_RIGHT_BACKWARD, GPIO.HIGH)
            
            self.is_moving = True
            self.current_direction = "backward"
            
            time.sleep(duration)
            self.stop_motors()
            
        except Exception as e:
            print(f"Move backward error: {e}")
    
    def turn_left(self, duration=0.3):
        try:
            print("Turning left")
            self.stop_motors()
            GPIO.output(self.MOTOR_RIGHT_FORWARD, GPIO.HIGH)
            GPIO.output(self.MOTOR_LEFT_BACKWARD, GPIO.HIGH)
            
            self.is_moving = True
            self.current_direction = "left"
            
            time.sleep(duration)
            self.stop_motors()
            
        except Exception as e:
            print(f"Turn left error: {e}")
    
    def turn_right(self, duration=0.3):
        try:
            print("Turning right")
            self.stop_motors()
            GPIO.output(self.MOTOR_LEFT_FORWARD, GPIO.HIGH)
            GPIO.output(self.MOTOR_RIGHT_BACKWARD, GPIO.HIGH)
            
            self.is_moving = True
            self.current_direction = "right"
            
            time.sleep(duration)
            self.stop_motors()
            
        except Exception as e:
            print(f"Turn right error: {e}")
    
    def stop_motors(self):
        try:
            pins = [
                self.MOTOR_LEFT_FORWARD, self.MOTOR_LEFT_BACKWARD,
                self.MOTOR_RIGHT_FORWARD, self.MOTOR_RIGHT_BACKWARD
            ]
            for pin in pins:
                GPIO.output(pin, GPIO.LOW)
                
            self.is_moving = False
            self.current_direction = None
            
        except Exception as e:
            print(f"Stop motors error: {e}")
    
    def get_distance(self):
        try:
            GPIO.output(self.TRIGGER_PIN, GPIO.LOW)
            time.sleep(0.1)
            
            GPIO.output(self.TRIGGER_PIN, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(self.TRIGGER_PIN, GPIO.LOW)
            
            start_time = time.time()
            while GPIO.input(self.ECHO_PIN) == 0:
                start_time = time.time()
                if time.time() - start_time > 0.1:
                    return 0.0
            
            stop_time = time.time()
            while GPIO.input(self.ECHO_PIN) == 1:
                stop_time = time.time()
                if time.time() - start_time > 0.1:
                    return 0.0
            
            time_elapsed = stop_time - start_time
            distance = (time_elapsed * 34300) / 2
            return round(distance, 2)
            
        except Exception as e:
            print(f"Distance sensor error: {e}")
            return 0.0
    
    def get_sensor_data(self):
        try:
            return {
                'distance': self.get_distance(),
                'temperature': 25.0,
                'battery': 85,
                'timestamp': datetime.now().isoformat(),
                'status': 'active'
            }
        except Exception as e:
            print(f"Sensor data error: {e}")
            return {
                'distance': 0.0,
                'temperature': 25.0,
                'battery': 85,
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }

class RobotServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.robot = RealEduBot()
        self.running = False
        self.clients = []
        
        self.autonomous_thread = None
        self.autonomous_running = False
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        print(f"Received signal {signum}, shutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def autonomous_navigation_loop(self, target_data=None):
        print("Starting autonomous navigation loop")
        self.autonomous_running = True
        
        try:
            while self.autonomous_running and self.running:
                obstacle_detected = self.robot.autonomous_obstacle_avoidance()
                
                if not obstacle_detected:
                    self.robot.move_forward(duration=0.8)
                
                sensor_data = self.robot.get_sensor_data()
                broadcast_msg = {
                    'type': 'autonomous_update',
                    'data': {
                        'sensor_data': sensor_data,
                        'obstacle_detected': obstacle_detected,
                        'mode': 'autonomous',
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
                for client in self.clients[:]:
                    try:
                        client.send(json.dumps(broadcast_msg).encode())
                    except:
                        self.clients.remove(client)
                
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Autonomous navigation error: {e}")
        finally:
            self.robot.stop_motors()
            self.autonomous_running = False
            print("Autonomous navigation loop stopped")
    
    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1)
            
            print(f"Robot server started on {self.host}:{self.port}")
            print("Waiting for connections...")
            self.running = True
            
            sensor_thread = threading.Thread(target=self.sensor_broadcast_loop)
            sensor_thread.daemon = True
            sensor_thread.start()
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"New connection from {address}")
                    
                    self.clients.append(client_socket)
                    
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Accept error: {e}")
                    break
                    
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def handle_client(self, client_socket, address):
        print(f"Handling client {address}")
        try:
            while self.running:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                try:
                    message = json.loads(data)
                    self.process_message(message, client_socket, address)
                except json.JSONDecodeError as e:
                    error_msg = {'type': 'error', 'message': f'Invalid JSON: {str(e)}'}
                    client_socket.send(json.dumps(error_msg).encode())
                    print(f"JSON error from {address}: {e}")
                    
        except Exception as e:
            print(f"Client handling error for {address}: {e}")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            print(f"Disconnected from {address}")
    
    def process_message(self, message, client_socket, address):
        msg_type = message.get('type')
        print(f"Received message from {address}: {msg_type}")
        
        if msg_type == 'command':
            command = message.get('command')
            data = message.get('data', {})
            
            response = {
                'type': 'command_response', 
                'command': command, 
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                if command == 'move':
                    direction = data.get('direction', '').lower()
                    
                    if direction == 'forward':
                        self.robot.move_forward()
                        response['message'] = 'Moving forward'
                    elif direction == 'backward':
                        self.robot.move_backward()
                        response['message'] = 'Moving backward'
                    elif direction == 'left':
                        self.robot.turn_left()
                        response['message'] = 'Turning left'
                    elif direction == 'right':
                        self.robot.turn_right()
                        response['message'] = 'Turning right'
                    elif direction == 'stop':
                        self.robot.stop_motors()
                        response['message'] = 'Stopping motors'
                    else:
                        response['status'] = 'error'
                        response['message'] = f'Unknown direction: {direction}'
                        
                elif command == 'emergency_stop':
                    stop_result = self.robot.emergency_stop()
                    response.update(stop_result)
                    self.autonomous_running = False
                    
                elif command == 'smart_stop':
                    stop_result = self.robot.smart_stop()
                    response.update(stop_result)
                    
                elif command == 'start_autonomous':
                    auto_result = self.robot.start_autonomous_navigation(data)
                    response.update(auto_result)
                    
                    if auto_result['status'] == 'success':
                        self.autonomous_thread = threading.Thread(
                            target=self.autonomous_navigation_loop,
                            args=(data,)
                        )
                        self.autonomous_thread.daemon = True
                        self.autonomous_thread.start()
                        
                elif command == 'stop_autonomous':
                    self.autonomous_running = False
                    stop_result = self.robot.stop_autonomous_navigation()
                    response.update(stop_result)
                    
                elif command == 'get_status':
                    status_data = {
                        'is_moving': self.robot.is_moving,
                        'current_direction': self.robot.current_direction,
                        'auto_mode': self.robot.auto_mode,
                        'autonomous_running': self.autonomous_running,
                        'sensor_data': self.robot.get_sensor_data()
                    }
                    response['status_data'] = status_data
                    response['message'] = 'Status retrieved'
                    
                elif command == 'get_sensors':
                    sensor_data = self.robot.get_sensor_data()
                    response['sensor_data'] = sensor_data
                    response['message'] = 'Sensor data retrieved'
                    
                elif command == 'stop':
                    self.robot.stop_motors()
                    response['message'] = 'Emergency stop executed'
                    
                else:
                    response['status'] = 'error'
                    response['message'] = f'Unknown command: {command}'
                    
            except Exception as e:
                response['status'] = 'error'
                response['message'] = str(e)
                print(f"Command execution error: {e}")
                
            client_socket.send(json.dumps(response).encode())
            print(f"Sent response to {address}: {response['status']}")
            
        elif msg_type == 'test':
            test_response = {
                'type': 'test_response', 
                'message': 'Connection test successful',
                'timestamp': datetime.now().isoformat()
            }
            client_socket.send(json.dumps(test_response).encode())
            print(f"Sent test response to {address}")
            
        else:
            error_msg = {'type': 'error', 'message': f'Unknown message type: {msg_type}'}
            client_socket.send(json.dumps(error_msg).encode())
    
    def sensor_broadcast_loop(self):
        while self.running:
            try:
                if self.clients:
                    sensor_data = self.robot.get_sensor_data()
                    broadcast_msg = {
                        'type': 'sensor_data',
                        'data': sensor_data,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    for client in self.clients[:]:
                        try:
                            client.send(json.dumps(broadcast_msg).encode())
                        except:
                            self.clients.remove(client)
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Sensor broadcast error: {e}")
                time.sleep(1)
    
    def cleanup(self):
        print("Cleaning up resources...")
        self.running = False
        self.autonomous_running = False
        
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        try:
            self.server_socket.close()
        except:
            pass
        
        try:
            self.robot.stop_motors()
            GPIO.cleanup()
            print("GPIO cleaned up")
        except:
            pass
        
        print("Server shutdown complete")

if __name__ == "__main__":
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"Host IP: {local_ip}")
    except:
        print("Could not determine host IP")
    
    server = RobotServer()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("Server interrupted by user")
        server.cleanup()
