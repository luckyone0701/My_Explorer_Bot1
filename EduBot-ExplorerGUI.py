# -*- coding: utf-8 -*-

"""
Created on Sunday October 19 15:46:55 2025

@author:  luckyone0701 ^__^
"""

# -*- coding: utf-8 -*-

import sys, random, math, socket, json, threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QTextEdit, QProgressBar, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QFrame,
    QGraphicsRectItem, QGraphicsLineItem, QGroupBox, QCheckBox, QLineEdit, QMessageBox,
    QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QBrush, QColor, QPen, QFont

class RobotConnection:
    def __init__(self, parent):
        self.parent = parent
        self.socket = None
        self.connected = False
        self.host = "192.168.1.100"
        self.port = 5000
        self.receive_thread = None
        
    def connect_to_robot(self, host, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((host, port))
            self.connected = True
            self.host = host
            self.port = port
            
            self.receive_thread = threading.Thread(target=self.receive_data)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            return True
        except Exception as e:
            self.parent.log.append(f"Connection error: {str(e)}")
            return False
    
    def send_command(self, command, data=None):
        if not self.connected or not self.socket:
            self.parent.log.append("Not connected to robot")
            return False
            
        try:
            message = {
                'type': 'command',
                'command': command,
                'data': data or {}
            }
            self.socket.send(json.dumps(message).encode())
            return True
        except Exception as e:
            self.parent.log.append(f"Send error: {str(e)}")
            self.connected = False
            return False
    
    def receive_data(self):
        while self.connected:
            try:
                data = self.socket.recv(1024).decode()
                if data:
                    message = json.loads(data)
                    self.handle_received_message(message)
            except:
                break
    
    def handle_received_message(self, message):
        if message.get('type') == 'sensor_data':
            self.parent.update_real_sensors(message.get('data', {}))
        elif message.get('type') == 'autonomous_update':
            self.parent.handle_autonomous_update(message.get('data', {}))

class EduBotExplorer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduBot Explorer - Real Robot Control")
        
        self.setGeometry(50, 50, 900, 650)
        
        self.robot_x, self.robot_y = 100, 100
        self.start_x, self.start_y = 100, 100
        self.robot_trail = []
        self.trail_lines = []
        self.obstacles = []
        self.autonomous_mode = False
        self.target_x, self.target_y = None, None
        self.target_item = None
        self.target_selection_mode = False
        self.autonomous_timer = QTimer()
        
        self.robot_connection = RobotConnection(self)
        
        self.setup_ui()
        self.setup_connections()
        self.setup_timer()
        self.draw_map()

    def setup_ui(self):
        self.controls = {
            "Forward": QPushButton("↑"),
            "Backward": QPushButton("↓"),
            "Left": QPushButton("←"),
            "Right": QPushButton("→"),
            "Stop": QPushButton("Stop"),
            "Clear": QPushButton("Clear"),
            "Home": QPushButton("Home"),
            "Auto": QPushButton("Auto"),
            "EmergencyStop": QPushButton("Emergency Stop"),
            "SmartStop": QPushButton("Smart Stop"),
            "StartAuto": QPushButton("Start Auto"),
            "StopAuto": QPushButton("Stop Auto"),
            "GetStatus": QPushButton("Get Status")
        }
        
        for btn in self.controls.values():
            btn.setFixedSize(80, 35)
        
        self.controls["Forward"].setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.controls["Backward"].setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.controls["Left"].setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.controls["Right"].setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.controls["Stop"].setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.controls["Clear"].setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold;")
        self.controls["Home"].setStyleSheet("background-color: #607D8B; color: white; font-weight: bold;")
        self.controls["Auto"].setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold;")
        self.controls["EmergencyStop"].setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold;")
        self.controls["SmartStop"].setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.controls["StartAuto"].setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.controls["StopAuto"].setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.controls["GetStatus"].setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.controls["Left"])
        control_layout.addWidget(self.controls["Forward"])
        control_layout.addWidget(self.controls["Backward"])
        control_layout.addWidget(self.controls["Right"])
        control_layout.addWidget(self.controls["Stop"])
        control_layout.setSpacing(3)

        extra_controls_layout = QHBoxLayout()
        extra_controls_layout.addWidget(self.controls["Clear"])
        extra_controls_layout.addWidget(self.controls["Home"])
        extra_controls_layout.addWidget(self.controls["Auto"])
        extra_controls_layout.setSpacing(3)
        
        advanced_controls_layout = QHBoxLayout()
        advanced_controls_layout.addWidget(self.controls["EmergencyStop"])
        advanced_controls_layout.addWidget(self.controls["SmartStop"])
        advanced_controls_layout.addWidget(self.controls["StartAuto"])
        advanced_controls_layout.addWidget(self.controls["StopAuto"])
        advanced_controls_layout.addWidget(self.controls["GetStatus"])
        advanced_controls_layout.setSpacing(3)
        
        connection_group = QGroupBox("Connection")
        connection_group.setMaximumHeight(100)
        connection_layout = QGridLayout()
        
        self.host_input = QLineEdit("192.168.1.100")
        self.host_input.setMaximumHeight(25)
        self.port_input = QLineEdit("5000")
        self.port_input.setMaximumHeight(25)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMaximumHeight(25)
        self.connect_btn.setStyleSheet("background-color: #2E7D32; color: white;")
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setMaximumHeight(25)
        self.disconnect_btn.setStyleSheet("background-color: #C62828; color: white;")
        self.disconnect_btn.setEnabled(False)
        
        self.connection_status = QLabel("Status: Disconnected")
        self.connection_status.setMaximumHeight(20)
        self.connection_status.setStyleSheet("font-size: 10px; background-color: #FFCDD2; padding: 2px;")
        
        connection_layout.addWidget(QLabel("IP:"), 0, 0)
        connection_layout.addWidget(self.host_input, 0, 1)
        connection_layout.addWidget(QLabel("Port:"), 0, 2)
        connection_layout.addWidget(self.port_input, 0, 3)
        connection_layout.addWidget(self.connect_btn, 1, 0, 1, 2)
        connection_layout.addWidget(self.disconnect_btn, 1, 2, 1, 2)
        connection_layout.addWidget(self.connection_status, 2, 0, 1, 4)
        
        connection_group.setLayout(connection_layout)
        
        autonomous_group = QGroupBox("Autonomous")
        autonomous_group.setMaximumHeight(80)
        autonomous_layout = QVBoxLayout()
        
        self.autonomous_check = QCheckBox("Enable Auto")
        self.autonomous_check.setStyleSheet("font-size: 11px;")
        
        self.target_btn = QPushButton("Set Target")
        self.target_btn.setMaximumHeight(25)
        self.target_btn.setStyleSheet("background-color: #E91E63; color: white; font-size: 11px;")
        
        self.target_label = QLabel("Target: Not set")
        self.target_label.setMaximumHeight(20)
        self.target_label.setStyleSheet("font-size: 10px; background-color: #FFECB3;")
        
        autonomous_layout.addWidget(self.autonomous_check)
        autonomous_layout.addWidget(self.target_btn)
        autonomous_layout.addWidget(self.target_label)
        autonomous_group.setLayout(autonomous_layout)

        self.sensor_label = QLabel("Distance: -- cm | Temp: -- °C")
        self.sensor_label.setMaximumHeight(20)
        self.sensor_label.setStyleSheet("font-size: 11px; background-color: #E1F5FE;")

        self.battery_bar = QProgressBar()
        self.battery_bar.setValue(100)
        self.battery_bar.setFormat("Battery: %p%")
        self.battery_bar.setMaximumHeight(18)
        self.battery_bar.setStyleSheet("QProgressBar { height: 15px; font-size: 10px; }")

        self.scene = QGraphicsScene(0, 0, 350, 200)
        self.map_view = QGraphicsView(self.scene)
        self.map_view.setFixedHeight(200)
        self.map_view.setFrameShape(QFrame.Box)
        self.map_view.setStyleSheet("background-color: #F5F5F5;")
        self.map_view.setSceneRect(0, 0, 350, 200)
        self.map_view.mousePressEvent = self.map_clicked

        self.robot_item = QGraphicsEllipseItem(0, 0, 15, 15)
        self.robot_item.setBrush(QBrush(QColor("#FF5722")))
        self.robot_item.setPen(QPen(Qt.black, 1))
        self.scene.addItem(self.robot_item)
        self.robot_item.setPos(self.robot_x, self.robot_y)

        self.position_label = QLabel("Position: (100, 100)")
        self.position_label.setMaximumHeight(18)
        self.position_label.setStyleSheet("font-size: 10px; background-color: #FFF9C4;")

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Command log...")
        self.log.setMaximumHeight(80)
        self.log.setStyleSheet("font-size: 9px;")

        layout = QVBoxLayout()
        layout.addWidget(connection_group)
        layout.addLayout(control_layout)
        layout.addLayout(extra_controls_layout)
        layout.addLayout(advanced_controls_layout)
        
        compact_layout = QHBoxLayout()
        compact_layout.addWidget(autonomous_group)
        compact_layout.addWidget(self.sensor_label)
        
        layout.addLayout(compact_layout)
        layout.addWidget(self.position_label)
        layout.addWidget(self.battery_bar)
        layout.addWidget(QLabel("Robot Map"))
        layout.addWidget(self.map_view)
        layout.addWidget(QLabel("Command Log"))
        layout.addWidget(self.log)
        
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)
        
        self.setStyleSheet("font-size: 11px;")

    def draw_map(self):
        for x in range(0, 350, 15):
            line = QGraphicsLineItem(x, 0, x, 200)
            line.setPen(QPen(QColor("#E0E0E0"), 0.5))
            self.scene.addItem(line)
            
        for y in range(0, 200, 15):
            line = QGraphicsLineItem(0, y, 350, y)
            line.setPen(QPen(QColor("#E0E0E0"), 0.5))
            self.scene.addItem(line)
        
        border = QGraphicsRectItem(0, 0, 350, 200)
        border.setPen(QPen(Qt.black, 2))
        self.scene.addItem(border)
        
        obstacle_positions = [
            (40, 40, 25, 25), (150, 60, 30, 15), 
            (110, 120, 15, 30), (220, 90, 25, 25)
        ]
        
        for x, y, w, h in obstacle_positions:
            obstacle = QGraphicsRectItem(x, y, w, h)
            obstacle.setBrush(QBrush(QColor("#9E9E9E")))
            obstacle.setPen(QPen(Qt.black, 1))
            self.scene.addItem(obstacle)
            self.obstacles.append(obstacle)

    def setup_connections(self):
        self.controls["Forward"].clicked.connect(lambda: self.move_robot(0, -8, "forward"))
        self.controls["Backward"].clicked.connect(lambda: self.move_robot(0, 8, "backward"))
        self.controls["Left"].clicked.connect(lambda: self.move_robot(-8, 0, "left"))
        self.controls["Right"].clicked.connect(lambda: self.move_robot(8, 0, "right"))
        self.controls["Stop"].clicked.connect(self.emergency_stop)
        self.controls["Clear"].clicked.connect(self.clear_map)
        self.controls["Home"].clicked.connect(self.return_to_start)
        self.controls["Auto"].clicked.connect(self.auto_move_random)
        self.autonomous_check.stateChanged.connect(self.toggle_autonomous_mode)
        self.target_btn.clicked.connect(self.enable_target_selection)
        
        self.controls["EmergencyStop"].clicked.connect(self.emergency_stop_robot)
        self.controls["SmartStop"].clicked.connect(self.smart_stop_robot)
        self.controls["StartAuto"].clicked.connect(self.start_autonomous_navigation)
        self.controls["StopAuto"].clicked.connect(self.stop_autonomous_navigation)
        self.controls["GetStatus"].clicked.connect(self.get_robot_status)
        
        self.connect_btn.clicked.connect(self.connect_to_robot)
        self.disconnect_btn.clicked.connect(self.disconnect_from_robot)
        
        self.autonomous_timer.timeout.connect(self.autonomous_move)

    def connect_to_robot(self):
        host = self.host_input.text()
        try:
            port = int(self.port_input.text())
        except:
            QMessageBox.warning(self, "Error", "Invalid port number")
            return
        
        if self.robot_connection.connect_to_robot(host, port):
            self.connection_status.setText("Status: Connected")
            self.connection_status.setStyleSheet("font-size: 10px; background-color: #C8E6C9; padding: 2px;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.log.append(f"Connected to {host}:{port}")
        else:
            self.connection_status.setText("Status: Connection failed")
            self.log.append("Connection failed")

    def disconnect_from_robot(self):
        if self.robot_connection.socket:
            self.robot_connection.socket.close()
        self.robot_connection.connected = False
        self.connection_status.setText("Status: Disconnected")
        self.connection_status.setStyleSheet("font-size: 10px; background-color: #FFCDD2; padding: 2px;")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.log.append("Disconnected")

    def map_clicked(self, event):
        if self.target_selection_mode:
            pos = self.map_view.mapToScene(event.pos())
            self.set_target(pos.x(), pos.y())
        event.accept()

    def set_target(self, x, y):
        if self.target_item:
            self.scene.removeItem(self.target_item)
        
        self.target_x, self.target_y = x, y
        self.target_item = QGraphicsEllipseItem(x-10, y-10, 20, 20)
        self.target_item.setBrush(QBrush(QColor("#FF0000")))
        self.target_item.setPen(QPen(Qt.black, 1))
        self.target_item.setZValue(10)
        self.scene.addItem(self.target_item)
        
        self.target_label.setText(f"Target: ({int(x)}, {int(y)})")
        self.log.append(f"Target: ({int(x)}, {int(y)})")
        
        self.target_selection_mode = False
        self.target_btn.setStyleSheet("background-color: #E91E63; color: white; font-size: 11px;")
        
        if self.autonomous_mode:
            self.autonomous_timer.start(100)

    def enable_target_selection(self):
        self.target_selection_mode = True
        self.log.append("Click on map to set target")
        self.target_btn.setStyleSheet("background-color: #C2185B; color: white; font-size: 11px;")

    def toggle_autonomous_mode(self, state):
        self.autonomous_mode = state == Qt.Checked
        if self.autonomous_mode:
            self.log.append("Autonomous enabled")
            if self.target_x is not None:
                self.autonomous_timer.start(100)
            else:
                self.log.append("Set target first")
                self.autonomous_check.setChecked(False)
                self.autonomous_mode = False
        else:
            self.log.append("Autonomous disabled")
            self.autonomous_timer.stop()

    def autonomous_move(self):
        if self.target_x is None or not self.autonomous_mode:
            self.autonomous_timer.stop()
            return
            
        dx = self.target_x - (self.robot_x + 7)
        dy = self.target_y - (self.robot_y + 7)
        
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 10:
            self.log.append("Target reached!")
            self.autonomous_timer.stop()
            return
            
        dx = dx / distance * 4
        dy = dy / distance * 4
        
        self.move_robot(dx, dy, "autonomous")

    def auto_move_random(self):
        random_x = random.randint(15, 335)
        random_y = random.randint(15, 185)
        self.set_target(random_x, random_y)
        
        if not self.autonomous_mode:
            self.autonomous_check.setChecked(True)
            self.autonomous_mode = True
            self.autonomous_timer.start(100)

    def emergency_stop(self):
        self.autonomous_mode = False
        self.autonomous_check.setChecked(False)
        self.autonomous_timer.stop()
        
        if self.robot_connection.connected:
            self.robot_connection.send_command('stop')
        
        self.send_command("Emergency Stop")

    def emergency_stop_robot(self):
        if self.robot_connection.connected:
            self.robot_connection.send_command('emergency_stop')
        self.log.append("Emergency Stop executed")

    def smart_stop_robot(self):
        if self.robot_connection.connected:
            self.robot_connection.send_command('smart_stop')
        self.log.append("Smart Stop executed")

    def start_autonomous_navigation(self):
        if self.robot_connection.connected:
            target_data = {
                'target_x': self.target_x,
                'target_y': self.target_y
            }
            self.robot_connection.send_command('start_autonomous', target_data)
        self.log.append("Autonomous navigation started")

    def stop_autonomous_navigation(self):
        if self.robot_connection.connected:
            self.robot_connection.send_command('stop_autonomous')
        self.log.append("Autonomous navigation stopped")

    def get_robot_status(self):
        if self.robot_connection.connected:
            self.robot_connection.send_command('get_status')
        self.log.append("Requesting robot status")

    def handle_autonomous_update(self, data):
        sensor_data = data.get('sensor_data', {})
        obstacle_detected = data.get('obstacle_detected', False)
        
        self.update_real_sensors(sensor_data)
        
        if obstacle_detected:
            self.log.append("Obstacle detected and avoided")

    def clear_map(self):
        for line in self.trail_lines:
            self.scene.removeItem(line)
        self.trail_lines.clear()
        self.robot_trail.clear()
        
        if self.target_item:
            self.scene.removeItem(self.target_item)
            self.target_item = None
            self.target_x, self.target_y = None, None
            self.target_label.setText("Target: Not set")
            
        self.log.append("Map cleared")

    def return_to_start(self):
        self.robot_x, self.robot_y = self.start_x, self.start_y
        self.robot_item.setPos(self.robot_x, self.robot_y)
        self.position_label.setText(f"Position: ({self.robot_x}, {self.robot_y})")
        self.log.append("Returned to start")

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sensors)
        self.timer.start(1000)

    def move_robot(self, dx, dy, command):
        self.robot_trail.append((self.robot_x, self.robot_y))
        
        new_x = max(8, min(self.robot_x + dx, 342))
        new_y = max(8, min(self.robot_y + dy, 192))
        
        self.robot_x = new_x
        self.robot_y = new_y
        
        self.robot_item.setPos(self.robot_x, self.robot_y)
        
        if len(self.robot_trail) > 1:
            prev_x, prev_y = self.robot_trail[-1]
            trail_line = QGraphicsLineItem(prev_x + 7, prev_y + 7, self.robot_x + 7, self.robot_y + 7)
            trail_line.setPen(QPen(QColor("#2196F3"), 1.5))
            self.scene.addItem(trail_line)
            self.trail_lines.append(trail_line)
        
        self.position_label.setText(f"Position: ({int(self.robot_x)}, {int(self.robot_y)})")
        self.send_command(command)
        
        if self.robot_connection.connected and command in ['forward', 'backward', 'left', 'right', 'stop']:
            movement_data = {
                'direction': command,
                'distance': math.sqrt(dx*dx + dy*dy)
            }
            self.robot_connection.send_command('move', movement_data)

    def send_command(self, command):
        self.log.append(f"Command: {command}")

    def update_real_sensors(self, sensor_data):
        distance = sensor_data.get('distance', 0)
        temperature = sensor_data.get('temperature', 25)
        battery = sensor_data.get('battery', 100)
        
        self.sensor_label.setText(f"Distance: {distance} cm | Temp: {temperature} °C")
        self.battery_bar.setValue(battery)

    def update_sensors(self):
        if not self.robot_connection.connected:
            distance = random.randint(10, 100)
            temperature = random.randint(20, 35)
            battery = max(0, self.battery_bar.value() - random.randint(0, 2))
            self.sensor_label.setText(f"Distance: {distance} cm | Temp: {temperature} °C")
            self.battery_bar.setValue(battery)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EduBotExplorer()
    window.show()
    sys.exit(app.exec_())
