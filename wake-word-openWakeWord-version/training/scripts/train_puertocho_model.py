#!/usr/bin/env python3
"""
🧠 Entrenador del Modelo "Puertocho"
Script principal para entrenar modelo openWakeWord personalizado
"""

import os
import sys
import yaml
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from datetime import datetime
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class PuertochoTrainer:
    def __init__(self, config_path: str = "configs/training_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        
        # Configurar dispositivo
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"🎮 Usando dispositivo: {self.device}")
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            logger.info(f"   GPU: {gpu_name} ({gpu_memory:.1f}GB)")
        
        # Directorios
        self.data_dir = Path(self.config['data']['base_dir'])
        self.models_dir = Path(self.config['training']['models_dir'])
        self.logs_dir = Path(self.config['training']['logs_dir'])
        
        # Crear directorios si no existen
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🗂️ Configuración:")
        logger.info(f"   Datos: {self.data_dir}")
        logger.info(f"   Modelos: {self.models_dir}")
        logger.info(f"   Logs: {self.logs_dir}")

    def load_config(self) -> Dict:
        """Cargar configuración desde archivo YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ Configuración cargada desde {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            # Configuración por defecto
            return self.get_default_config()

    def get_default_config(self) -> Dict:
        """Configuración por defecto si no se encuentra archivo"""
        logger.info("🔧 Usando configuración por defecto")
        return {
            'model': {
                'name': 'puertocho_v1',
                'architecture': 'mel_stft_1d_cnn',
                'sample_rate': 16000,
                'frame_length': 1280,
                'num_mel_features': 32
            },
            'training': {
                'batch_size': 8,
                'learning_rate': 1e-4,
                'epochs': 100,
                'early_stopping_patience': 10,
                'validation_split': 0.2,
                'models_dir': 'models',
                'logs_dir': 'logs'
            },
            'data': {
                'base_dir': 'data',
                'positive_dir': 'data/positive',
                'negative_dir': 'data/negative',
                'target_fpr': 0.5,
                'target_fnr': 0.05
            },
            'optimization': {
                'use_amp': True,
                'gradient_clip_norm': 1.0,
                'warmup_steps': 500
            }
        }

    def prepare_datasets(self) -> Tuple[torch.utils.data.DataLoader, torch.utils.data.DataLoader]:
        """Preparar datasets de entrenamiento y validación"""
        logger.info("📊 Preparando datasets...")
        
        try:
            # Importar openWakeWord para entrenamiento
            import openwakeword.train as oww_train
            
            # Configurar paths de datos
            positive_dir = Path(self.config['data']['positive_dir'])
            negative_dir = Path(self.config['data']['negative_dir'])
            
            logger.info(f"   Datos positivos: {positive_dir}")
            logger.info(f"   Datos negativos: {negative_dir}")
            
            # Verificar que existan los directorios
            if not positive_dir.exists():
                raise FileNotFoundError(f"Directorio de datos positivos no encontrado: {positive_dir}")
            if not negative_dir.exists():
                raise FileNotFoundError(f"Directorio de datos negativos no encontrado: {negative_dir}")
            
            # Contar archivos
            positive_files = list(positive_dir.rglob("*.wav"))
            negative_files = []
            
            # Buscar archivos negativos en subdirectorios
            for subdir in negative_dir.iterdir():
                if subdir.is_dir():
                    negative_files.extend(list(subdir.glob("*.wav")))
                else:
                    if subdir.suffix == '.wav':
                        negative_files.append(subdir)
            
            logger.info(f"   Archivos positivos: {len(positive_files)}")
            logger.info(f"   Archivos negativos: {len(negative_files)}")
            
            if len(positive_files) < 100:
                raise ValueError("Necesitas al menos 100 muestras positivas")
            if len(negative_files) < 1000:
                logger.warning("⚠️ Pocos datos negativos, considera generar más")
            
            # Crear dataset usando openWakeWord
            dataset_config = {
                'positive_samples': [str(f) for f in positive_files],
                'negative_samples': [str(f) for f in negative_files],
                'sample_rate': self.config['model']['sample_rate'],
                'frame_length': self.config['model']['frame_length'],
                'batch_size': self.config['training']['batch_size'],
                'validation_split': self.config['training']['validation_split']
            }
            
            # Crear dataloaders
            train_loader, val_loader = oww_train.create_dataloaders(dataset_config)
            
            logger.info(f"✅ Datasets preparados:")
            logger.info(f"   Entrenamiento: {len(train_loader.dataset)} muestras")
            logger.info(f"   Validación: {len(val_loader.dataset)} muestras")
            
            return train_loader, val_loader
            
        except Exception as e:
            logger.error(f"❌ Error preparando datasets: {e}")
            raise

    def create_model(self):
        """Crear modelo openWakeWord"""
        logger.info("🧠 Creando modelo...")
        
        try:
            import openwakeword.train as oww_train
            
            model_config = {
                'architecture': self.config['model']['architecture'],
                'sample_rate': self.config['model']['sample_rate'],
                'frame_length': self.config['model']['frame_length'],
                'num_mel_features': self.config['model'].get('num_mel_features', 32),
                'device': str(self.device)
            }
            
            model = oww_train.create_model(model_config)
            model = model.to(self.device)
            
            # Contar parámetros
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            
            logger.info(f"✅ Modelo creado:")
            logger.info(f"   Arquitectura: {self.config['model']['architecture']}")
            logger.info(f"   Parámetros totales: {total_params:,}")
            logger.info(f"   Parámetros entrenables: {trainable_params:,}")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Error creando modelo: {e}")
            raise

    def setup_training(self, model):
        """Configurar optimizador y scheduler"""
        logger.info("⚙️ Configurando entrenamiento...")
        
        # Optimizador
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=self.config['training']['learning_rate'],
            weight_decay=0.01
        )
        
        # Loss function
        criterion = torch.nn.BCEWithLogitsLoss()
        
        # Scheduler con warmup
        warmup_steps = self.config['optimization'].get('warmup_steps', 500)
        scheduler = torch.optim.lr_scheduler.OneCycleLR(
            optimizer,
            max_lr=self.config['training']['learning_rate'],
            epochs=self.config['training']['epochs'],
            steps_per_epoch=100,  # Estimación, se ajustará
            pct_start=warmup_steps/10000,
            anneal_strategy='cos'
        )
        
        # AMP para entrenamiento mixto
        scaler = torch.cuda.amp.GradScaler() if self.config['optimization'].get('use_amp', True) else None
        
        logger.info(f"✅ Configuración de entrenamiento:")
        logger.info(f"   Learning rate: {self.config['training']['learning_rate']}")
        logger.info(f"   Batch size: {self.config['training']['batch_size']}")
        logger.info(f"   Epochs: {self.config['training']['epochs']}")
        logger.info(f"   AMP activado: {scaler is not None}")
        
        return optimizer, criterion, scheduler, scaler

    def train_epoch(self, model, train_loader, optimizer, criterion, scheduler, scaler, epoch):
        """Entrenar una época"""
        model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_idx, (data, targets) in enumerate(train_loader):
            data, targets = data.to(self.device), targets.to(self.device)
            
            optimizer.zero_grad()
            
            if scaler is not None:
                # Entrenamiento con precisión mixta
                with torch.cuda.amp.autocast():
                    outputs = model(data)
                    loss = criterion(outputs, targets)
                
                scaler.scale(loss).backward()
                
                # Gradient clipping
                clip_norm = self.config['optimization'].get('gradient_clip_norm', 1.0)
                if clip_norm > 0:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), clip_norm)
                
                scaler.step(optimizer)
                scaler.update()
            else:
                # Entrenamiento normal
                outputs = model(data)
                loss = criterion(outputs, targets)
                loss.backward()
                
                # Gradient clipping
                clip_norm = self.config['optimization'].get('gradient_clip_norm', 1.0)
                if clip_norm > 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), clip_norm)
                
                optimizer.step()
            
            scheduler.step()
            
            # Estadísticas
            total_loss += loss.item()
            predicted = torch.sigmoid(outputs) > 0.5
            total += targets.size(0)
            correct += (predicted == targets.byte()).sum().item()
            
            # Log cada 100 batches
            if batch_idx % 100 == 0:
                accuracy = 100. * correct / total
                avg_loss = total_loss / (batch_idx + 1)
                lr = scheduler.get_last_lr()[0]
                
                logger.info(f"   Epoch {epoch} [{batch_idx}/{len(train_loader)}] "
                          f"Loss: {avg_loss:.6f} Acc: {accuracy:.2f}% LR: {lr:.2e}")
        
        epoch_loss = total_loss / len(train_loader)
        epoch_acc = 100. * correct / total
        
        return epoch_loss, epoch_acc

    def validate_epoch(self, model, val_loader, criterion):
        """Validar una época"""
        model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, targets in val_loader:
                data, targets = data.to(self.device), targets.to(self.device)
                
                outputs = model(data)
                loss = criterion(outputs, targets)
                
                total_loss += loss.item()
                predicted = torch.sigmoid(outputs) > 0.5
                total += targets.size(0)
                correct += (predicted == targets.byte()).sum().item()
        
        val_loss = total_loss / len(val_loader)
        val_acc = 100. * correct / total
        
        return val_loss, val_acc

    def save_model(self, model, epoch, val_loss, is_best=False):
        """Guardar modelo"""
        model_name = self.config['model']['name']
        
        # Guardar checkpoint
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'val_loss': val_loss,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
        
        checkpoint_path = self.models_dir / f"{model_name}_epoch_{epoch}.pth"
        torch.save(checkpoint, checkpoint_path)
        
        if is_best:
            best_path = self.models_dir / f"{model_name}_best.pth"
            torch.save(checkpoint, best_path)
            logger.info(f"💾 Mejor modelo guardado: {best_path}")
        
        # Exportar a ONNX para inferencia
        if is_best:
            try:
                self.export_to_onnx(model, model_name)
            except Exception as e:
                logger.warning(f"⚠️ Error exportando a ONNX: {e}")

    def export_to_onnx(self, model, model_name):
        """Exportar modelo a formato ONNX"""
        logger.info("📤 Exportando modelo a ONNX...")
        
        model.eval()
        
        # Crear input dummy
        frame_length = self.config['model']['frame_length']
        dummy_input = torch.randn(1, frame_length).to(self.device)
        
        onnx_path = self.models_dir / f"{model_name}.onnx"
        
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['audio'],
            output_names=['output'],
            dynamic_axes={
                'audio': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        
        logger.info(f"✅ Modelo exportado a ONNX: {onnx_path}")

    def train_model(self):
        """Función principal de entrenamiento"""
        logger.info("🚀 Iniciando entrenamiento del modelo 'Puertocho'")
        logger.info("=" * 60)
        
        try:
            # 1. Preparar datos
            train_loader, val_loader = self.prepare_datasets()
            
            # 2. Crear modelo
            model = self.create_model()
            
            # 3. Configurar entrenamiento
            optimizer, criterion, scheduler, scaler = self.setup_training(model)
            
            # 4. Variables de control
            best_val_loss = float('inf')
            patience_counter = 0
            patience = self.config['training']['early_stopping_patience']
            
            # 5. Métricas de entrenamiento
            train_history = {
                'train_loss': [],
                'train_acc': [],
                'val_loss': [],
                'val_acc': []
            }
            
            # 6. Entrenamiento principal
            epochs = self.config['training']['epochs']
            logger.info(f"🏁 Comenzando entrenamiento por {epochs} épocas...")
            
            for epoch in range(1, epochs + 1):
                logger.info(f"\n📅 Época {epoch}/{epochs}")
                logger.info("-" * 40)
                
                # Entrenar
                train_loss, train_acc = self.train_epoch(
                    model, train_loader, optimizer, criterion, scheduler, scaler, epoch
                )
                
                # Validar
                val_loss, val_acc = self.validate_epoch(model, val_loader, criterion)
                
                # Guardar métricas
                train_history['train_loss'].append(train_loss)
                train_history['train_acc'].append(train_acc)
                train_history['val_loss'].append(val_loss)
                train_history['val_acc'].append(val_acc)
                
                # Log resultado de la época
                logger.info(f"📊 Resultado época {epoch}:")
                logger.info(f"   Train - Loss: {train_loss:.6f}, Acc: {train_acc:.2f}%")
                logger.info(f"   Val   - Loss: {val_loss:.6f}, Acc: {val_acc:.2f}%")
                
                # Verificar mejora
                is_best = val_loss < best_val_loss
                if is_best:
                    best_val_loss = val_loss
                    patience_counter = 0
                    logger.info("🎉 ¡Nuevo mejor modelo!")
                else:
                    patience_counter += 1
                    logger.info(f"📈 Sin mejora ({patience_counter}/{patience})")
                
                # Guardar modelo
                self.save_model(model, epoch, val_loss, is_best)
                
                # Early stopping
                if patience_counter >= patience:
                    logger.info(f"🛑 Early stopping activado después de {epoch} épocas")
                    break
            
            # 7. Guardar historial de entrenamiento
            history_path = self.logs_dir / f"training_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(history_path, 'w') as f:
                json.dump(train_history, f, indent=2)
            
            logger.info(f"📊 Historial guardado: {history_path}")
            
            # 8. Resumen final
            logger.info("\n🎯 ENTRENAMIENTO COMPLETADO")
            logger.info("=" * 60)
            logger.info(f"✅ Mejor validación loss: {best_val_loss:.6f}")
            logger.info(f"📈 Épocas entrenadas: {min(epoch, epochs)}")
            logger.info(f"💾 Modelo final: {self.models_dir}/{self.config['model']['name']}_best.pth")
            logger.info(f"📤 Modelo ONNX: {self.models_dir}/{self.config['model']['name']}.onnx")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante entrenamiento: {e}")
            raise

def main():
    """Función principal"""
    print("🧠 Entrenador del Modelo 'Puertocho'")
    print("=" * 50)
    
    # Verificar CUDA
    if torch.cuda.is_available():
        print(f"🎮 GPU detectada: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️ GPU no disponible, usando CPU")
    
    # Crear entrenador
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/training_config.yaml"
    trainer = PuertochoTrainer(config_path)
    
    # Entrenar modelo
    success = trainer.train_model()
    
    if success:
        print("\n🎉 ¡Modelo 'Puertocho' entrenado exitosamente!")
        print("💡 Próximo paso: Validar y probar el modelo")
    else:
        print("\n❌ Error durante el entrenamiento")
        sys.exit(1)

if __name__ == "__main__":
    main() 