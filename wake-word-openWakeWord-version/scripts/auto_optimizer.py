#!/usr/bin/env python3
"""
Auto-optimizador para el asistente de voz Puertocho
Analiza rendimiento y ajusta parámetros automáticamente según condiciones
"""

import os
import sys
import json
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path

class AutoOptimizer:
    """Optimizador automático de parámetros según condiciones del sistema"""
    
    def __init__(self, config_file=".env"):
        self.config_file = config_file
        self.performance_log = "performance.log"
        
        # Configuración actual
        self.current_config = {}
        self.load_current_config()
        
        # Thresholds y rangos de optimización
        self.optimization_rules = {
            "cpu_high": {
                "threshold": 70,  # CPU > 70%
                "actions": {
                    "AUDIO_CHUNK_SIZE": {"increase": 1.5, "max": 2560},  # Chunks más grandes = menos CPU
                    "OPENWAKEWORD_THRESHOLD": {"increase": 0.1, "max": 0.8},  # Threshold más alto = menos false positives
                }
            },
            "memory_high": {
                "threshold": 700,  # RAM > 700MB
                "actions": {
                    "AUDIO_CHUNK_SIZE": {"increase": 1.2, "max": 1920},
                    "OPENWAKEWORD_VAD_THRESHOLD": {"set": 0.3},  # Activar VAD para filtrar
                }
            },
            "temperature_high": {
                "threshold": 65,  # Temp > 65°C
                "actions": {
                    "OPENWAKEWORD_ENABLE_SPEEX_NS": {"set": "false"},  # Desactivar Speex NS
                    "AUDIO_CHUNK_SIZE": {"increase": 2.0, "max": 3840},  # Menos frecuencia de procesamiento
                }
            },
            "false_positives_high": {
                "threshold": 3,  # > 3 detecciones por minuto
                "actions": {
                    "OPENWAKEWORD_THRESHOLD": {"increase": 0.05, "max": 0.9},
                }
            }
        }
    
    def load_current_config(self):
        """Cargar configuración actual del .env"""
        if not os.path.exists(self.config_file):
            print(f"⚠️ Archivo {self.config_file} no encontrado")
            return
        
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    self.current_config[key] = value
        
        print(f"✅ Configuración cargada: {len(self.current_config)} parámetros")
    
    def save_config(self, new_config):
        """Guardar nueva configuración al .env"""
        # Backup del archivo actual
        if os.path.exists(self.config_file):
            backup_file = f"{self.config_file}.backup.{int(time.time())}"
            os.rename(self.config_file, backup_file)
            print(f"💾 Backup guardado: {backup_file}")
        
        # Escribir nueva configuración
        with open(self.config_file, 'w') as f:
            f.write("# Configuración auto-optimizada del Asistente de Voz Puertocho\n")
            f.write(f"# Optimizado automáticamente: {datetime.now().isoformat()}\n\n")
            
            for key, value in new_config.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ Nueva configuración guardada en {self.config_file}")
    
    def get_system_metrics(self):
        """Obtener métricas actuales del sistema"""
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_mb": psutil.virtual_memory().used / 1024 / 1024,
            "temperature": self.get_temperature(),
            "load_avg": os.getloadavg()[0] if hasattr(os, 'getloadavg') else None,
            "disk_percent": psutil.disk_usage('/').percent
        }
        return metrics
    
    def get_temperature(self):
        """Obtener temperatura del CPU"""
        try:
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    return int(f.read().strip()) / 1000.0
        except Exception:
            pass
        
        try:
            temps = psutil.sensors_temperatures()
            if 'cpu_thermal' in temps:
                return temps['cpu_thermal'][0].current
        except Exception:
            pass
        
        return None
    
    def analyze_performance_log(self):
        """Analizar log de rendimiento para patrones"""
        if not os.path.exists(self.performance_log):
            print(f"⚠️ Log {self.performance_log} no encontrado")
            return {}
        
        print(f"📊 Analizando {self.performance_log}...")
        
        # Leer últimos 100 registros (últimos ~8 minutos si se toma cada 5s)
        recent_metrics = []
        
        with open(self.performance_log, 'r') as f:
            lines = f.readlines()
            for line in lines[-100:]:
                if line.startswith('#'):
                    continue
                try:
                    data = json.loads(line)
                    recent_metrics.append(data)
                except json.JSONDecodeError:
                    continue
        
        if not recent_metrics:
            return {}
        
        # Calcular promedios y tendencias
        analysis = {
            "avg_cpu": sum(m.get('cpu_percent', 0) for m in recent_metrics) / len(recent_metrics),
            "max_cpu": max(m.get('cpu_percent', 0) for m in recent_metrics),
            "avg_memory": sum(m.get('memory_mb', 0) for m in recent_metrics) / len(recent_metrics),
            "max_memory": max(m.get('memory_mb', 0) for m in recent_metrics),
            "avg_temperature": None,
            "max_temperature": None,
            "samples": len(recent_metrics)
        }
        
        temp_values = [m.get('temperature') for m in recent_metrics if m.get('temperature')]
        if temp_values:
            analysis["avg_temperature"] = sum(temp_values) / len(temp_values)
            analysis["max_temperature"] = max(temp_values)
        
        return analysis
    
    def determine_optimizations(self, current_metrics, performance_analysis):
        """Determinar qué optimizaciones aplicar"""
        optimizations = {}
        reasons = []
        
        # Verificar CPU alto
        if current_metrics["cpu_percent"] > self.optimization_rules["cpu_high"]["threshold"]:
            optimizations.update(self.optimization_rules["cpu_high"]["actions"])
            reasons.append(f"CPU alto: {current_metrics['cpu_percent']:.1f}%")
        
        # Verificar memoria alta
        if current_metrics["memory_mb"] > self.optimization_rules["memory_high"]["threshold"]:
            optimizations.update(self.optimization_rules["memory_high"]["actions"])
            reasons.append(f"RAM alta: {current_metrics['memory_mb']:.0f} MB")
        
        # Verificar temperatura alta
        if current_metrics["temperature"] and current_metrics["temperature"] > self.optimization_rules["temperature_high"]["threshold"]:
            optimizations.update(self.optimization_rules["temperature_high"]["actions"])
            reasons.append(f"Temperatura alta: {current_metrics['temperature']:.1f}°C")
        
        # Verificar promedios del performance log
        if performance_analysis:
            if performance_analysis["avg_cpu"] > 60:
                optimizations.update(self.optimization_rules["cpu_high"]["actions"])
                reasons.append(f"CPU promedio alto: {performance_analysis['avg_cpu']:.1f}%")
            
            if performance_analysis["avg_memory"] > 600:
                optimizations.update(self.optimization_rules["memory_high"]["actions"])
                reasons.append(f"RAM promedio alta: {performance_analysis['avg_memory']:.0f} MB")
        
        return optimizations, reasons
    
    def apply_optimization(self, param, action):
        """Aplicar una optimización específica"""
        current_value = self.current_config.get(param)
        if not current_value:
            print(f"⚠️ Parámetro {param} no encontrado en configuración")
            return None
        
        try:
            if "set" in action:
                # Valor fijo
                new_value = str(action["set"])
                
            elif "increase" in action:
                # Incremento proporcional
                if param in ["AUDIO_CHUNK_SIZE"]:
                    # Valores numéricos
                    current_num = int(current_value)
                    new_num = int(current_num * action["increase"])
                    
                    # Aplicar máximo si existe
                    if "max" in action:
                        new_num = min(new_num, action["max"])
                    
                    new_value = str(new_num)
                    
                elif param in ["OPENWAKEWORD_THRESHOLD", "OPENWAKEWORD_VAD_THRESHOLD"]:
                    # Valores decimales
                    current_float = float(current_value)
                    new_float = current_float + action["increase"]
                    
                    # Aplicar máximo si existe
                    if "max" in action:
                        new_float = min(new_float, action["max"])
                    
                    new_value = f"{new_float:.1f}"
                else:
                    print(f"⚠️ No sé cómo incrementar {param}")
                    return None
            else:
                print(f"⚠️ Acción desconocida para {param}: {action}")
                return None
            
            return new_value
            
        except (ValueError, TypeError) as e:
            print(f"❌ Error aplicando optimización a {param}: {e}")
            return None
    
    def optimize(self, dry_run=False):
        """Ejecutar optimización completa"""
        print("🔧 INICIANDO AUTO-OPTIMIZACIÓN")
        print("=" * 40)
        
        # Obtener métricas actuales
        current_metrics = self.get_system_metrics()
        print(f"📊 Métricas actuales:")
        print(f"   CPU: {current_metrics['cpu_percent']:.1f}%")
        print(f"   RAM: {current_metrics['memory_mb']:.0f} MB")
        if current_metrics['temperature']:
            print(f"   Temp: {current_metrics['temperature']:.1f}°C")
        
        # Analizar performance log
        performance_analysis = self.analyze_performance_log()
        if performance_analysis:
            print(f"📈 Análisis del log ({performance_analysis['samples']} muestras):")
            print(f"   CPU promedio: {performance_analysis['avg_cpu']:.1f}%")
            print(f"   RAM promedio: {performance_analysis['avg_memory']:.0f} MB")
            if performance_analysis['avg_temperature']:
                print(f"   Temp promedio: {performance_analysis['avg_temperature']:.1f}°C")
        
        # Determinar optimizaciones
        optimizations, reasons = self.determine_optimizations(current_metrics, performance_analysis)
        
        if not optimizations:
            print("✅ No se requieren optimizaciones - sistema funcionando bien")
            return
        
        print(f"\n🎯 Optimizaciones requeridas:")
        for reason in reasons:
            print(f"   • {reason}")
        
        # Aplicar optimizaciones
        new_config = self.current_config.copy()
        changes_made = []
        
        for param, action in optimizations.items():
            old_value = self.current_config.get(param, "NO_SET")
            new_value = self.apply_optimization(param, action)
            
            if new_value and new_value != old_value:
                new_config[param] = new_value
                changes_made.append(f"{param}: {old_value} → {new_value}")
        
        if not changes_made:
            print("ℹ️ No hay cambios que aplicar")
            return
        
        print(f"\n🔄 Cambios propuestos:")
        for change in changes_made:
            print(f"   • {change}")
        
        if dry_run:
            print("\n🔍 MODO DRY-RUN - No se aplicaron cambios")
            return
        
        # Guardar nueva configuración
        self.save_config(new_config)
        
        print("\n✅ Optimización completada")
        print("🔄 Reinicia el asistente para aplicar los cambios")
    
    def revert_to_defaults(self):
        """Revertir a configuración por defecto"""
        default_config = {
            "TRANSCRIPTION_SERVICE_URL": "http://localhost:5000/transcribe",
            "BUTTON_PIN": "22",
            "LED_IDLE_PIN": "17", 
            "LED_RECORD_PIN": "27",
            "OPENWAKEWORD_MODEL_PATHS": "alexa,hey_mycroft",
            "OPENWAKEWORD_THRESHOLD": "0.6",
            "OPENWAKEWORD_VAD_THRESHOLD": "0.0",
            "OPENWAKEWORD_ENABLE_SPEEX_NS": "false",
            "OPENWAKEWORD_INFERENCE_FRAMEWORK": "onnx",
            "AUDIO_SAMPLE_RATE": "16000",
            "AUDIO_CHANNELS": "1",
            "AUDIO_CHUNK_SIZE": "1280"
        }
        
        self.save_config(default_config)
        print("✅ Configuración revertida a valores por defecto")


def main():
    """Función principal"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Auto-optimizador del Asistente de Voz Puertocho")
            print("\nUso:")
            print("  python auto_optimizer.py           # Ejecutar optimización")
            print("  python auto_optimizer.py --dry-run # Ver cambios sin aplicar")  
            print("  python auto_optimizer.py --revert  # Revertir a defaults")
            return
        elif sys.argv[1] == "--dry-run":
            optimizer = AutoOptimizer()
            optimizer.optimize(dry_run=True)
            return
        elif sys.argv[1] == "--revert":
            optimizer = AutoOptimizer()
            optimizer.revert_to_defaults()
            return
    
    # Optimización normal
    optimizer = AutoOptimizer()
    optimizer.optimize()


if __name__ == "__main__":
    main() 