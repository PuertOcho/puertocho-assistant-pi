#!/usr/bin/env python3
"""
Monitor de rendimiento para el asistente de voz Puertocho
Mide CPU, RAM, latencia, temperatura y otros parámetros en tiempo real
"""

import os
import sys
import time
import json
import threading
import psutil
from datetime import datetime, timedelta
from pathlib import Path

class PerformanceMonitor:
    """Monitor de rendimiento del sistema durante operación del asistente"""
    
    def __init__(self, monitor_interval=5.0, log_file="performance.log"):
        self.monitor_interval = monitor_interval
        self.log_file = log_file
        self.monitoring = False
        self.start_time = None
        self.process = None
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "temperature": [],
            "audio_latency": [],
            "detection_count": 0,
            "false_positives": 0,
            "commands_executed": 0
        }
        
        # Buscar proceso del asistente
        self._find_assistant_process()
    
    def _find_assistant_process(self):
        """Encontrar el proceso del asistente"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any('main.py' in arg for arg in proc.info['cmdline']):
                    self.process = psutil.Process(proc.info['pid'])
                    print(f"✅ Proceso asistente encontrado: PID {proc.info['pid']}")
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print("⚠️ Proceso del asistente no encontrado - métricas del sistema general")
    
    def get_cpu_usage(self):
        """Obtener uso de CPU"""
        if self.process and self.process.is_running():
            try:
                return self.process.cpu_percent(interval=1)
            except psutil.NoSuchProcess:
                self.process = None
        
        return psutil.cpu_percent(interval=1)
    
    def get_memory_usage(self):
        """Obtener uso de memoria"""
        if self.process and self.process.is_running():
            try:
                mem_info = self.process.memory_info()
                return mem_info.rss / 1024 / 1024  # MB
            except psutil.NoSuchProcess:
                self.process = None
        
        return psutil.virtual_memory().used / 1024 / 1024  # MB
    
    def get_temperature(self):
        """Obtener temperatura del CPU (Raspberry Pi)"""
        try:
            # Método 1: Raspberry Pi específico
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp = int(f.read().strip()) / 1000.0
                    return temp
        except Exception:
            pass
        
        try:
            # Método 2: psutil sensors
            temps = psutil.sensors_temperatures()
            if 'cpu_thermal' in temps:
                return temps['cpu_thermal'][0].current
            elif 'coretemp' in temps:
                return temps['coretemp'][0].current
        except Exception:
            pass
        
        return None
    
    def get_system_load(self):
        """Obtener carga del sistema"""
        return os.getloadavg()[0] if hasattr(os, 'getloadavg') else None
    
    def get_disk_usage(self):
        """Obtener uso de disco"""
        return psutil.disk_usage('/').percent
    
    def check_throttling(self):
        """Verificar si el sistema está siendo throttled (Raspberry Pi)"""
        try:
            if os.path.exists('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'):
                with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'r') as f:
                    current_freq = int(f.read().strip())
                
                with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq', 'r') as f:
                    max_freq = int(f.read().strip())
                
                return current_freq < max_freq * 0.8  # Throttled si está bajo 80%
        except Exception:
            pass
        
        return False
    
    def log_metrics(self, metrics):
        """Registrar métricas en archivo"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            **metrics
        }
        
        # Escribir al archivo de log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def monitor_loop(self):
        """Loop principal de monitoreo"""
        print(f"🔄 Iniciando monitoreo cada {self.monitor_interval}s...")
        print(f"📝 Logs en: {self.log_file}")
        
        while self.monitoring:
            try:
                # Recopilar métricas
                metrics = {
                    "cpu_percent": self.get_cpu_usage(),
                    "memory_mb": self.get_memory_usage(),
                    "temperature": self.get_temperature(),
                    "load_avg": self.get_system_load(),
                    "disk_percent": self.get_disk_usage(),
                    "throttled": self.check_throttling(),
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
                }
                
                # Almacenar para estadísticas
                self.metrics["cpu_usage"].append(metrics["cpu_percent"])
                self.metrics["memory_usage"].append(metrics["memory_mb"])
                if metrics["temperature"]:
                    self.metrics["temperature"].append(metrics["temperature"])
                
                # Log
                self.log_metrics(metrics)
                
                # Mostrar en consola cada minuto
                if len(self.metrics["cpu_usage"]) % (60 // self.monitor_interval) == 0:
                    self.print_current_status(metrics)
                
                # Alertas
                self.check_alerts(metrics)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                print(f"❌ Error en monitoreo: {e}")
                time.sleep(self.monitor_interval)
    
    def print_current_status(self, metrics):
        """Mostrar estado actual"""
        print(f"\n📊 Estado actual ({datetime.now().strftime('%H:%M:%S')}):")
        print(f"   🖥️  CPU: {metrics['cpu_percent']:.1f}%")
        print(f"   🧠 RAM: {metrics['memory_mb']:.0f} MB")
        if metrics['temperature']:
            print(f"   🌡️  Temp: {metrics['temperature']:.1f}°C")
        if metrics['load_avg']:
            print(f"   ⚖️  Load: {metrics['load_avg']:.2f}")
        print(f"   💾 Disk: {metrics['disk_percent']:.1f}%")
        if metrics['throttled']:
            print(f"   ⚠️  THROTTLED!")
    
    def check_alerts(self, metrics):
        """Verificar alertas de rendimiento"""
        alerts = []
        
        if metrics["cpu_percent"] > 80:
            alerts.append(f"🔥 CPU alto: {metrics['cpu_percent']:.1f}%")
        
        if metrics["memory_mb"] > 800:  # Para RPi con 1GB
            alerts.append(f"🧠 RAM alta: {metrics['memory_mb']:.0f} MB")
        
        if metrics["temperature"] and metrics["temperature"] > 70:
            alerts.append(f"🌡️ Temperatura alta: {metrics['temperature']:.1f}°C")
        
        if metrics["throttled"]:
            alerts.append("⚠️ Sistema throttled")
        
        for alert in alerts:
            print(f"🚨 ALERTA: {alert}")
    
    def get_statistics(self):
        """Obtener estadísticas del período monitoreado"""
        if not self.metrics["cpu_usage"]:
            return {}
        
        stats = {
            "duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
            "cpu": {
                "avg": sum(self.metrics["cpu_usage"]) / len(self.metrics["cpu_usage"]),
                "max": max(self.metrics["cpu_usage"]),
                "min": min(self.metrics["cpu_usage"])
            },
            "memory": {
                "avg": sum(self.metrics["memory_usage"]) / len(self.metrics["memory_usage"]),
                "max": max(self.metrics["memory_usage"]),
                "min": min(self.metrics["memory_usage"])
            }
        }
        
        if self.metrics["temperature"]:
            stats["temperature"] = {
                "avg": sum(self.metrics["temperature"]) / len(self.metrics["temperature"]),
                "max": max(self.metrics["temperature"]),
                "min": min(self.metrics["temperature"])
            }
        
        return stats
    
    def start(self):
        """Iniciar monitoreo"""
        self.monitoring = True
        self.start_time = datetime.now()
        
        # Crear archivo de log con header
        with open(self.log_file, 'w') as f:
            f.write(f"# Performance log started at {self.start_time.isoformat()}\n")
        
        # Iniciar thread de monitoreo
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print(f"✅ Monitor iniciado - PID: {os.getpid()}")
    
    def stop(self):
        """Detener monitoreo"""
        self.monitoring = False
        
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5)
        
        # Mostrar estadísticas finales
        stats = self.get_statistics()
        if stats:
            print(f"\n📈 ESTADÍSTICAS FINALES:")
            print(f"   Duración: {stats['duration_minutes']:.1f} minutos")
            print(f"   CPU promedio: {stats['cpu']['avg']:.1f}% (max: {stats['cpu']['max']:.1f}%)")
            print(f"   RAM promedio: {stats['memory']['avg']:.0f} MB (max: {stats['memory']['max']:.0f} MB)")
            if 'temperature' in stats:
                print(f"   Temp promedio: {stats['temperature']['avg']:.1f}°C (max: {stats['temperature']['max']:.1f}°C)")
        
        print(f"📝 Log guardado en: {self.log_file}")


def analyze_log_file(log_file):
    """Analizar archivo de log existente"""
    if not os.path.exists(log_file):
        print(f"❌ Archivo {log_file} no encontrado")
        return
    
    print(f"📊 Analizando {log_file}...")
    
    cpu_values = []
    memory_values = []
    temp_values = []
    
    with open(log_file, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            try:
                data = json.loads(line)
                cpu_values.append(data.get('cpu_percent', 0))
                memory_values.append(data.get('memory_mb', 0))
                if data.get('temperature'):
                    temp_values.append(data['temperature'])
            except json.JSONDecodeError:
                continue
    
    if cpu_values:
        print(f"📈 Análisis de {len(cpu_values)} muestras:")
        print(f"   CPU: promedio {sum(cpu_values)/len(cpu_values):.1f}%, máximo {max(cpu_values):.1f}%")
        print(f"   RAM: promedio {sum(memory_values)/len(memory_values):.0f} MB, máximo {max(memory_values):.0f} MB")
        if temp_values:
            print(f"   Temp: promedio {sum(temp_values)/len(temp_values):.1f}°C, máximo {max(temp_values):.1f}°C")


def main():
    """Función principal"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "analyze":
            log_file = sys.argv[2] if len(sys.argv) > 2 else "performance.log"
            analyze_log_file(log_file)
            return
        elif sys.argv[1] == "--help":
            print("Uso:")
            print("  python monitor_performance.py          # Iniciar monitoreo")
            print("  python monitor_performance.py analyze  # Analizar performance.log")
            print("  python monitor_performance.py analyze custom.log  # Analizar archivo específico")
            return
    
    # Monitoreo en tiempo real
    monitor = PerformanceMonitor(monitor_interval=5.0)
    
    try:
        monitor.start()
        print("⏹️  Presiona Ctrl+C para detener...")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo monitor...")
        monitor.stop()


if __name__ == "__main__":
    main() 