#!/usr/bin/env python3
"""
Robot Server for EduBot Explorer
Run this on Raspberry Pi: python3 RobotServer.py
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
        print("Initializing RealEduBot...")
        
        # Motor pins - adjust these according to your connections
        self.MOTOR_LEFT_FORWARD = 17
        self.MOTOR_LEFT_BACKWARD = 18
        self.MOTOR_RIGHT_FORWARD = 22
        self.MOTOR_RIGHT_BACKWARD = 23
        
        # Sensor pins (optional)
        self.TRIGGER_PIN = 24
        self.ECHO_PIN = 25
        
        self.setup_gpio()
        print("GPIO setup completed")
        
    def setup_gpio(self):
        """Setup GPIO pins"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            
            # Setup motor pins
            motor_pins = [
                self.MOTOR_LEFT_FORWARD, self.MOTOR_LEFT_BACKWARD,
                self.MOTOR_RIGHT_FORWARD, self.MOTOR_RIGHT_BACKWARD
            ]
            
            for pin in motor_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            
            # Setup distance sensor (optional)
            GPIO.setup(self.TRIGGER_PIN, GPIO.OUT)
            GPIO.setup(self.ECHO_PIN, GPIO.IN)
            GPIO.output(self.TRIGGER_PIN, GPIO.LOW)
            
            print("Motor and sensor pins initialized")
            
        except Exception as e:
            print(f"GPIO setup error: {e}")
    
    def move_forward(self, duration=0.5):
        """Move forward"""
        try:
            print("Moving forward")
            self.stop_motors()
            GPIO.output(self.MOTOR_LEFT_FORWARD, GPIO.HIGH)
            GPIO.output(self.MOTOR_RIGHT_FORWARD, GPIO.HIGH)
            time.sleep(duration)
            self.stop_motors()
        except Exception as e:
            print(f"Move forward error: {e}")
    
    def move_backward(self, duration=0.5):
        """Move backward"""
        try:
            print("Moving backward")
            self.stop_motors()
            GPIO.output(self.MOTOR_LEFT_BACKWARD, GPIO.HIGH)
            GPIO.output(self.MOTOR_RIGHT_BACKWARD, GPIO.HIGH)
            time.sleep(duration)
            self.stop_motors()
        except Exception as e:
            print(f"Move backward error: {e}")
    
    def turn_left(self, duration=0.3):
        """Turn left"""
        try:
            print("Turning left")
            self.stop_motors()
            GPIO.output(self.MOTOR_RIGHT_FORWARD, GPIO.HIGH)
            GPIO.output(self.MOTOR_LEFT_BACKWARD, GPIO.HIGH)
            time.sleep(duration)
            self.stop_motors()
        except Exception as e:
            print(f"Turn left error: {e}")
    
    def turn_right(self, duration=0.3):
        """Turn right"""
        try:
            print("Turning right")
            self.stop_motors()
            GPIO.output(self.MOTOR_LEFT_FORWARD, GPIO.HIGH)
            GPIO.output(self.MOTOR_RIGHT_BACKWARD, GPIO.HIGH)
            time.sleep(duration)
            self.stop_motors()
        except Exception as e:
            print(f"Turn right error: {e}")
    
    def stop_motors(self):
        """Stop all motors"""
        try:
            pins = [
                self.MOTOR_LEFT_FORWARD, self.MOTOR_LEFT_BACKWARD,
                self.MOTOR_RIGHT_FORWARD, self.MOTOR_RIGHT_BACKWARD
            ]
            for pin in pins:
                GPIO.output(pin, GPIO.LOW)
        except Exception as e:
            print(f"Stop motors error: {e}")
    
    def get_distance(self):
        """Measure distance using HC-SR04 sensor"""
        try:
            # Ensure TRIG is low
            GPIO.output(self.TRIGGER_PIN, GPIO.LOW)
            time.sleep(0.1)
            
            # Send pulse
            GPIO.output(self.TRIGGER_PIN, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(self.TRIGGER_PIN, GPIO.LOW)
            
            # Wait for pulse start
            start_time = time.time()
            while GPIO.input(self.ECHO_PIN) == 0:
                start_time = time.time()
                if time.time() - start_time > 0.1:  # timeout after 0.1 seconds
                    return 0.0
            
            # Wait for pulse end
            stop_time = time.time()
            while GPIO.input(self.ECHO_PIN) == 1:
                stop_time = time.time()
                if time.time() - start_time > 0.1:  # timeout after 0.1 seconds
                    return 0.0
            
            # Calculate distance
            time_elapsed = stop_time - start_time
            distance = (time_elapsed * 34300) / 2
            return round(distance, 2)
            
        except Exception as e:
            print(f"Distance sensor error: {e}")
            return 0.0
    
    def get_sensor_data(self):
        """Collect all sensor data"""
        try:
            return {
                'distance': self.get_distance(),
                'temperature': 25.0,  # Can add temperature sensor later
                'battery': 85,        # Simulate battery level
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
        self.clients = []  # Store connected clients
        
        # Setup shutdown signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"Received signal {signum}, shutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def start_server(self):
        """Start the robot server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1)  # timeout to check self.running
            
            print(f"Robot server started on {self.host}:{self.port}")
            print("Waiting for connections...")
            self.running = True
            
            # Start thread for automatic sensor data broadcasting
            sensor_thread = threading.Thread(target=self.sensor_broadcast_loop)
            sensor_thread.daemon = True
            sensor_thread.start()
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"New connection from {address}")
                    
                    # Add client to list
                    self.clients.append(client_socket)
                    
                    # Start thread to handle client
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
        """Handle client connection"""
        print(f"Handling client {address}")
        try:
            while self.running:
                # Receive data from client
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
            # Remove client from list and close connection
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            print(f"Disconnected from {address}")
    
    def process_message(self, message, client_socket, address):
        """Process incoming message"""
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
                        
                elif command == 'stop':
                    self.robot.stop_motors()
                    response['message'] = 'Emergency stop executed'
                    
                elif command == 'get_sensors':
                    sensor_data = self.robot.get_sensor_data()
                    response['sensor_data'] = sensor_data
                    response['message'] = 'Sensor data retrieved'
                    
                else:
                    response['status'] = 'error'
                    response['message'] = f'Unknown command: {command}'
                    
            except Exception as e:
                response['status'] = 'error'
                response['message'] = str(e)
                print(f"Command execution error: {e}")
                
            # Send response
            client_socket.send(json.dumps(response).encode())
            print(f"Sent response to {address}: {response['status']}")
            
        elif msg_type == 'test':
            # Connection test message
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
        """Broadcast sensor data to all connected clients periodically"""
        while self.running:
            try:
                if self.clients:
                    sensor_data = self.robot.get_sensor_data()
                    broadcast_msg = {
                        'type': 'sensor_data',
                        'data': sensor_data,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Send to all connected clients
                    for client in self.clients[:]:  # Use slice copy for safe iteration
                        try:
                            client.send(json.dumps(broadcast_msg).encode())
                        except:
                            # Remove disconnected clients
                            self.clients.remove(client)
                
                time.sleep(2)  # Broadcast every 2 seconds
                
            except Exception as e:
                print(f"Sensor broadcast error: {e}")
                time.sleep(1)
    
    def cleanup(self):
        """Cleanup resources"""
        print("Cleaning up resources...")
        self.running = False
        
        # Close all client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # Close server socket
        try:
            self.server_socket.close()
        except:
            pass
        
        # Cleanup GPIO
        try:
            self.robot.stop_motors()
            GPIO.cleanup()
            print("GPIO cleaned up")
        except:
            pass
        
        print("Server shutdown complete")

if __name__ == "__main__":
    # Get host IP (optional)
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"Host IP: {local_ip}")
    except:
        print("Could not determine host IP")
    
    # Create and start server
    server = RobotServer()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("Server interrupted by user")
        server.cleanup()
