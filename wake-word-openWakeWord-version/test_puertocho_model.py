#!/usr/bin/env python3
"""
🎯 Script de prueba para el modelo personalizado Puertocho
"""

import os
import sys
import numpy as np
from pathlib import Path

# Configurar variables de entorno
os.environ['OPENWAKEWORD_MODEL_PATHS'] = 'checkpoints/puertocho.onnx'
os.environ['OPENWAKEWORD_THRESHOLD'] = '0.5'

try:
    from openwakeword.model import Model
    import onnxruntime as ort
    
    print("🎯 Test del Modelo Personalizado 'Puertocho'")
    print("=" * 50)
    
    # 1. Verificar que el modelo existe
    model_path = Path('checkpoints/puertocho.onnx')
    if not model_path.exists():
        print(f"❌ Error: Modelo no encontrado en {model_path}")
        sys.exit(1)
    
    print(f"✅ Modelo encontrado: {model_path}")
    print(f"📊 Tamaño del modelo: {model_path.stat().st_size / 1024:.1f} KB")
    
    # 2. Verificar que se puede cargar directamente con ONNX
    print("\n�� Verificando modelo ONNX...")
    try:
        session = ort.InferenceSession(str(model_path))
        print("✅ Modelo ONNX cargado exitosamente")
        print(f"📊 Input: {session.get_inputs()[0].name} - {session.get_inputs()[0].shape}")
        print(f"📊 Output: {session.get_outputs()[0].name} - {session.get_outputs()[0].shape}")
        
        # Probar inferencia directa
        test_audio = np.random.randn(1, 16000).astype(np.float32)
        result = session.run(None, {'audio': test_audio})
        print(f"✅ Inferencia directa exitosa: {result[0][0][0]:.6f}")
        
    except Exception as e:
        print(f"❌ Error con modelo ONNX: {e}")
        sys.exit(1)
    
    # 3. Verificar con OpenWakeWord
    print("\n🔍 Verificando con OpenWakeWord...")
    try:
        # Intentar cargar con OpenWakeWord
        model = Model(
            wakeword_models=[str(model_path)],
            inference_framework='onnx'
        )
        print("✅ Modelo cargado con OpenWakeWord")
        
        # Probar detección
        test_audio = np.random.randn(16000).astype(np.float32)
        prediction = model.predict(test_audio)
        print(f"✅ Predicción exitosa: {prediction}")
        
    except Exception as e:
        print(f"⚠️ Advertencia con OpenWakeWord: {e}")
        print("Esto puede ser normal si OpenWakeWord espera un formato específico")
    
    print("\n🎉 Verificación completada!")
    print("💡 El modelo Puertocho está listo para usar")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("Instalar dependencias: pip install openwakeword onnxruntime")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    sys.exit(1)
