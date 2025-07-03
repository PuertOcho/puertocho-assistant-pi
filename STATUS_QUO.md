# 📝 STATUS_QUO.md

> **Fecha de actualización:** 2025-07-03
>
> Este documento resume el estado **actual** del proyecto *Puertocho Voice-Assistant*, cubriendo avance funcional, infraestructura, configuraciones clave y próximos pasos.

---

## 1. Visión general

El asistente funciona en Raspberry Pi con `openWakeWord` para la detección de palabra clave. Tras problemas de *false-positives* con modelos genéricos ("alexa"), se decidió entrenar un modelo personalizado **"Puertocho"**. Las fases 1-4 se han completado; la Fase 5 (entrenamiento) está en curso con una instancia GPU en Google Cloud.

---

## 2. Progreso por Fase

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Preparación del entorno | ✅ Completada |
| 2 | Integración básica `openWakeWord` | ✅ Completada |
| 3 | Integración con lógica del asistente | ✅ Completada |
| 4 | Optimización & robustez | ✅ Completada (penden subtareas menores de optimización) |
| 5 | Entrenamiento modelo "Puertocho" | 🔄 En progreso |
| 6 | Validación & despliegue | ⏳ Pendiente |
| 7 | Mejoras avanzadas | ⏳ Pendiente |

---

## 3. TODOs activos

| ID | Tarea | Estado | Dependencias |
|----|-------|--------|--------------|
| generate_positive_samples | Generar ~2000 muestras positivas vía TTS | pending | setup_training_environment |
| download_negative_dataset | Descargar/limpiar Common Voice ES | pending | setup_training_environment |
| train_puertocho_model | Entrenar modelo personalizado | pending | generate_positive_samples,<br/>download_negative_dataset |
| validate_model_performance | Validar métricas del modelo | pending | train_puertocho_model |
| integrate_custom_model | Integrar modelo en RPi & ajustar threshold | pending | validate_model_performance |
| integrate_user_samples | Integrar 103 muestras grabadas por el usuario | completed | generate_positive_samples |

*Nota:* Todos los elementos de Fases 1-4 y los test automatizados aparecen como **completed** en el tracker.

---

## 4. Configuración actual en Raspberry Pi

| Parámetro | Valor |
|-----------|-------|
| `OPENWAKEWORD_THRESHOLD` | **0.6** |
| Cool-down detección | **8 s** (implementado en `app/main.py`) |
| Modelos activos* | `alexa`, `hey_mycroft`† |
| VAD | Deshabilitado (`threshold=0.0`) |
| Speex Noise Suppression | `false` |
| Inference framework | `onnx` |
| Audio | 16 kHz, 1 canal, 1280 samples (80 ms) |
| GPIO | Botón 22, LED verde 17 (IDLE), LED rojo 27 (RECORD) |

\* Se espera reemplazarlos por `checkpoints/puertocho.onnx` cuando el modelo esté listo.

† Wake-words genéricas empleadas sólo para pruebas temporales.

### Servicios & Scripts relevantes

- `scripts/monitor_performance.py` → métricas CPU/GPU, temperatura, RAM.
- `scripts/auto_optimizer.py` → auto-ajuste de parámetros (`threshold`, VAD, etc.) según métricas.
- Docker Compose con `network_mode: host` y dispositivos ALSA/GPIO expuestos.

---

## 5. Infraestructura Google Cloud

| Recurso | Valor |
|---------|-------|
| **Proyecto GCP** | `puertocho-wakeword-training` |
| **Billing Account** | `01D005-255612-3CCE8D` (vinculada) |
| **Cuota GPU T4** | 1 unidad global (aprobada) |

### Instancias activas (03-Jul-2025)

| Nombre | Zona | Tipo máquina | GPU | Disco | Estado | Creación |
|--------|------|--------------|-----|-------|--------|----------|
| `puertocho-training` | us-central1-b | `g2-standard-4` | 1× NVIDIA L4 | 100 GB NVMe | **RUNNING** | 2025-07-03 07:38 UTC |

Detalles adicionales de la VM:

- **Imagen base:** *Deep Learning VM* PyTorch 2.4 CUDA 12.4 (Debian 11)
- **Drivers NVIDIA:** instalados automáticamente (`install-nvidia-driver=True`).
- **IP externa:** `34.61.242.82` (puertos 22, 8080, 6006 abiertos).
- **Etiquetas:** `deeplearning-vm`.

> 💰 **Costo aproximado:** USD 0.596 / h (`g2-standard-4` + 1 L4 GPU @ us-central1-b).

---

## 6. Entorno de entrenamiento

- Carpeta **`training/`** con scripts y configuración detallada.
- Config principal: `configs/training_config.yaml` (batch_size 8, lr 1e-4, epochs 100, AMP = true, target FPR 0.5 / h).
- Pipeline automático: `scripts/run_full_training_pipeline.sh`.
- Datos objetivo: 2000 positivos, ≥10 000 negativos → ratio ~6:1.

---

## 7. Próximas acciones clave

1. **Generar muestras positivas** en la VM (`generate_positive_samples.py`).
2. **Descargar dataset negativo** (`download_negative_data.py`).
3. **Ejecutar entrenamiento** (`train_puertocho_model.py`) y validar métricas.
4. **Exportar modelo ONNX** y **subirlo a la Raspberry Pi**.
5. Ajustar `OPENWAKEWORD_THRESHOLD` (≈0.5-0.8) con pruebas reales.
6. Actualizar `PROJECT_TRACKER.md` y cerrar TODOs correspondientes.

---

## 8. Enlaces útiles

- Documentación entrenamiento: `training/README.md`, `docs/FASE_5_ENTRENAMIENTO_PUERTOCHO.md`
- openWakeWord Repo: <https://github.com/dscripka/openWakeWord>
- Google Cloud GPUs: <https://cloud.google.com/compute/docs/gpus>

---

> Fin del reporte. Mantener este archivo actualizado conforme avance el proyecto. 