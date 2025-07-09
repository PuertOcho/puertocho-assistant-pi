import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: window
    visible: true
    width: 800
    height: 600
    minimumWidth: 640
    minimumHeight: 480
    title: "PuertoCho Assistant Dashboard"
    
    // Propiedades del estado de la aplicación
    property real cpuUsage: 35.0
    property real memoryUsage: 60.0
    property real temperature: 42.5
    property bool assistantActive: false
    property int messagesCount: 0
    
    // Color scheme
    readonly property color primaryColor: "#2196F3"
    readonly property color secondaryColor: "#FF9800"
    readonly property color backgroundColor: "#FAFAFA"
    readonly property color surfaceColor: "#FFFFFF"
    readonly property color textColor: "#212121"
    
    // Simulación de datos en tiempo real
    Timer {
        interval: 2000
        running: true
        repeat: true
        onTriggered: {
            cpuUsage = Math.random() * 100
            memoryUsage = Math.random() * 100
            temperature = 35 + Math.random() * 20
        }
    }
    
    Rectangle {
        anchors.fill: parent
        color: backgroundColor
        
        ScrollView {
            anchors.fill: parent
            anchors.margins: 20
            
            ColumnLayout {
                width: parent.width
                spacing: 20
                
                // Header
                Rectangle {
                    Layout.fillWidth: true
                    height: 80
                    color: primaryColor
                    radius: 10
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        
                        Text {
                            text: "🤖 PuertoCho Assistant"
                            color: "white"
                            font.pixelSize: 24
                            font.bold: true
                        }
                        
                        Item { Layout.fillWidth: true }
                        
                        Switch {
                            id: assistantSwitch
                            checked: assistantActive
                            onToggled: {
                                assistantActive = checked
                                console.log("Asistente " + (checked ? "activado" : "desactivado"))
                            }
                        }
                        
                        Text {
                            text: assistantActive ? "ACTIVO" : "INACTIVO"
                            color: "white"
                            font.pixelSize: 16
                            font.bold: true
                        }
                    }
                }
                
                // Métricas del sistema
                GroupBox {
                    title: "📊 Métricas del Sistema"
                    Layout.fillWidth: true
                    
                    GridLayout {
                        anchors.fill: parent
                        columns: 3
                        columnSpacing: 20
                        rowSpacing: 15
                        
                        // CPU Usage
                        Column {
                            spacing: 10
                            
                            Text {
                                text: "💻 CPU"
                                font.pixelSize: 16
                                font.bold: true
                                color: textColor
                            }
                            
                            ProgressBar {
                                width: 150
                                from: 0
                                to: 100
                                value: cpuUsage
                                
                                background: Rectangle {
                                    implicitWidth: 150
                                    implicitHeight: 6
                                    color: "#E0E0E0"
                                    radius: 3
                                }
                                
                                contentItem: Item {
                                    implicitWidth: 150
                                    implicitHeight: 6
                                    
                                    Rectangle {
                                        width: parent.width * (cpuUsage / 100)
                                        height: parent.height
                                        radius: 3
                                        color: cpuUsage > 80 ? "#F44336" : cpuUsage > 60 ? secondaryColor : "#4CAF50"
                                    }
                                }
                            }
                            
                            Text {
                                text: Math.round(cpuUsage) + "%"
                                font.pixelSize: 14
                                color: textColor
                            }
                        }
                        
                        // Memory Usage
                        Column {
                            spacing: 10
                            
                            Text {
                                text: "💾 Memoria"
                                font.pixelSize: 16
                                font.bold: true
                                color: textColor
                            }
                            
                            ProgressBar {
                                width: 150
                                from: 0
                                to: 100
                                value: memoryUsage
                                
                                background: Rectangle {
                                    implicitWidth: 150
                                    implicitHeight: 6
                                    color: "#E0E0E0"
                                    radius: 3
                                }
                                
                                contentItem: Item {
                                    implicitWidth: 150
                                    implicitHeight: 6
                                    
                                    Rectangle {
                                        width: parent.width * (memoryUsage / 100)
                                        height: parent.height
                                        radius: 3
                                        color: memoryUsage > 80 ? "#F44336" : memoryUsage > 60 ? secondaryColor : "#4CAF50"
                                    }
                                }
                            }
                            
                            Text {
                                text: Math.round(memoryUsage) + "%"
                                font.pixelSize: 14
                                color: textColor
                            }
                        }
                        
                        // Temperature
                        Column {
                            spacing: 10
                            
                            Text {
                                text: "🌡️ Temperatura"
                                font.pixelSize: 16
                                font.bold: true
                                color: textColor
                            }
                            
                            Rectangle {
                                width: 150
                                height: 40
                                color: surfaceColor
                                border.color: "#E0E0E0"
                                border.width: 1
                                radius: 5
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: Math.round(temperature * 10) / 10 + "°C"
                                    font.pixelSize: 18
                                    font.bold: true
                                    color: temperature > 60 ? "#F44336" : temperature > 50 ? secondaryColor : "#4CAF50"
                                }
                            }
                        }
                    }
                }
                
                // Controles del Asistente
                GroupBox {
                    title: "🎛️ Controles del Asistente"
                    Layout.fillWidth: true
                    
                    RowLayout {
                        anchors.fill: parent
                        spacing: 20
                        
                        Column {
                            spacing: 15
                            
                            Button {
                                text: assistantActive ? "⏸️ Pausar" : "▶️ Iniciar"
                                font.pixelSize: 16
                                implicitWidth: 150
                                implicitHeight: 50
                                
                                background: Rectangle {
                                    color: parent.pressed ? Qt.darker(primaryColor) : primaryColor
                                    radius: 8
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    color: "white"
                                    font: parent.font
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                onClicked: {
                                    assistantActive = !assistantActive
                                    assistantSwitch.checked = assistantActive
                                    console.log("Asistente " + (assistantActive ? "iniciado" : "pausado"))
                                }
                            }
                            
                            Button {
                                text: "🔄 Reiniciar"
                                font.pixelSize: 16
                                implicitWidth: 150
                                implicitHeight: 50
                                
                                background: Rectangle {
                                    color: parent.pressed ? Qt.darker(secondaryColor) : secondaryColor
                                    radius: 8
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    color: "white"
                                    font: parent.font
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                onClicked: {
                                    console.log("Reiniciando asistente...")
                                    messagesCount = 0
                                }
                            }
                            
                            Button {
                                text: "⚙️ Configuración"
                                font.pixelSize: 16
                                implicitWidth: 150
                                implicitHeight: 50
                                
                                background: Rectangle {
                                    color: parent.pressed ? Qt.darker("#9E9E9E") : "#9E9E9E"
                                    radius: 8
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    color: "white"
                                    font: parent.font
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                onClicked: {
                                    console.log("Abriendo configuración...")
                                }
                            }
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: surfaceColor
                            border.color: "#E0E0E0"
                            border.width: 1
                            radius: 10
                            
                            Column {
                                anchors.centerIn: parent
                                spacing: 10
                                
                                Text {
                                    text: "📈 Estadísticas"
                                    font.pixelSize: 18
                                    font.bold: true
                                    color: textColor
                                }
                                
                                Text {
                                    text: "Mensajes procesados: " + messagesCount
                                    font.pixelSize: 14
                                    color: textColor
                                }
                                
                                Text {
                                    text: "Estado: " + (assistantActive ? "Funcionando" : "Inactivo")
                                    font.pixelSize: 14
                                    color: assistantActive ? "#4CAF50" : "#F44336"
                                }
                                
                                Button {
                                    text: "➕ Simular Mensaje"
                                    onClicked: {
                                        messagesCount++
                                        console.log("Mensaje simulado. Total: " + messagesCount)
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Panel de configuración rápida
                GroupBox {
                    title: "⚡ Configuración Rápida"
                    Layout.fillWidth: true
                    
                    GridLayout {
                        anchors.fill: parent
                        columns: 2
                        columnSpacing: 30
                        rowSpacing: 15
                        
                        Text {
                            text: "🔊 Volumen:"
                            font.pixelSize: 14
                            color: textColor
                        }
                        
                        Slider {
                            id: volumeSlider
                            Layout.fillWidth: true
                            from: 0
                            to: 100
                            value: 70
                            stepSize: 1
                            
                            onValueChanged: {
                                console.log("Volumen: " + Math.round(value) + "%")
                            }
                        }
                        
                        Text {
                            text: "💬 Sensibilidad:"
                            font.pixelSize: 14
                            color: textColor
                        }
                        
                        Slider {
                            id: sensitivitySlider
                            Layout.fillWidth: true
                            from: 0
                            to: 100
                            value: 50
                            stepSize: 1
                            
                            onValueChanged: {
                                console.log("Sensibilidad: " + Math.round(value) + "%")
                            }
                        }
                        
                        CheckBox {
                            text: "🌙 Modo nocturno"
                            onToggled: {
                                console.log("Modo nocturno: " + checked)
                            }
                        }
                        
                        CheckBox {
                            text: "🔔 Notificaciones"
                            checked: true
                            onToggled: {
                                console.log("Notificaciones: " + checked)
                            }
                        }
                    }
                }
            }
        }
    }
} 