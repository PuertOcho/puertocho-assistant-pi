import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    
    property string title: "Status"
    property string value: "N/A"
    property string subtitle: ""
    property string icon: "📊"
    property color cardColor: "#FFFFFF"
    property color accentColor: "#2196F3"
    property bool isActive: false
    
    width: 200
    height: 120
    color: cardColor
    radius: 12
    border.color: isActive ? accentColor : "#E0E0E0"
    border.width: isActive ? 2 : 1
    
    // Efecto de sombra
    Rectangle {
        anchors.fill: parent
        anchors.topMargin: 2
        anchors.leftMargin: 2
        color: "#10000000"
        radius: parent.radius
        z: -1
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8
        
        // Header con icono y título
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            
            Text {
                text: root.icon
                font.pixelSize: 24
            }
            
            Text {
                text: root.title
                font.pixelSize: 14
                font.bold: true
                color: "#212121"
                Layout.fillWidth: true
            }
            
            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: root.isActive ? "#4CAF50" : "#9E9E9E"
            }
        }
        
        // Valor principal
        Text {
            text: root.value
            font.pixelSize: 24
            font.bold: true
            color: root.accentColor
            Layout.fillHeight: true
            verticalAlignment: Text.AlignVCenter
        }
        
        // Subtítulo
        Text {
            text: root.subtitle
            font.pixelSize: 12
            color: "#666666"
            visible: subtitle !== ""
        }
    }
    
    // Animación al hacer hover (si es interactivo)
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        
        onEntered: {
            parent.scale = 1.02
        }
        
        onExited: {
            parent.scale = 1.0
        }
        
        onClicked: {
            console.log("Card clicked:", root.title)
        }
    }
    
    // Animación de escala
    Behavior on scale {
        NumberAnimation {
            duration: 150
            easing.type: Easing.OutQuart
        }
    }
    
    // Animación del borde cuando cambia el estado
    Behavior on border.color {
        ColorAnimation {
            duration: 300
        }
    }
} 