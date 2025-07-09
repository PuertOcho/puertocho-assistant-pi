import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    
    property string title: "Gauge"
    property real value: 0
    property real maxValue: 100
    property real minValue: 0
    property color gaugeColor: "#2196F3"
    property color backgroundColor: "#E0E0E0"
    property string units: "%"
    
    width: 120
    height: 120
    
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        
        // Fondo del gauge
        Rectangle {
            id: background
            anchors.centerIn: parent
            width: 100
            height: 100
            radius: 50
            color: "transparent"
            border.color: backgroundColor
            border.width: 10
        }
        
        // Indicador del progreso
        Canvas {
            id: progressCanvas
            anchors.fill: background
            
            onPaint: {
                var ctx = getContext("2d");
                var centerX = width / 2;
                var centerY = height / 2;
                var radius = 40;
                
                ctx.clearRect(0, 0, width, height);
                
                // Calcular el ángulo basado en el valor
                var percentage = (root.value - root.minValue) / (root.maxValue - root.minValue);
                var endAngle = -Math.PI/2 + (percentage * 2 * Math.PI);
                
                // Dibujar el arco de progreso
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, -Math.PI/2, endAngle);
                ctx.lineWidth = 10;
                ctx.strokeStyle = root.gaugeColor;
                ctx.lineCap = "round";
                ctx.stroke();
            }
        }
        
        // Texto central
        Column {
            anchors.centerIn: parent
            spacing: 2
            
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Math.round(root.value) + root.units
                font.pixelSize: 16
                font.bold: true
                color: "#212121"
            }
            
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.title
                font.pixelSize: 10
                color: "#666666"
            }
        }
    }
    
    // Animación cuando cambia el valor
    Behavior on value {
        NumberAnimation {
            duration: 500
            easing.type: Easing.OutQuart
        }
    }
    
    // Actualizar el canvas cuando cambia el valor
    onValueChanged: {
        progressCanvas.requestPaint();
    }
    
    Component.onCompleted: {
        progressCanvas.requestPaint();
    }
} 