cmake_minimum_required(VERSION 3.16)

project(PuertoChoAssistantView VERSION 1.0.0 LANGUAGES CXX)

# Configuración estándar de Qt
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Encontrar Qt6
find_package(Qt6 6.2 REQUIRED COMPONENTS Core Widgets Qml Quick QuickControls2)

# Habilitar Qt MOC, UIC y RCC automático
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Archivos fuente
set(SOURCES
    main.cpp
)

# Archivos de recursos
qt6_add_resources(RESOURCES resources.qrc)

# Crear el ejecutable con un nombre distinto al del directorio interno para evitar colisiones
qt6_add_executable(PuertoChoAssistantApp ${SOURCES})

# Agregar módulos QML al mismo target del ejecutable
qt6_add_qml_module(PuertoChoAssistantApp
    URI PuertoChoAssistantView
    VERSION 1.0
    QML_FILES
        main.qml
)

# Enlazar bibliotecas de Qt
target_link_libraries(PuertoChoAssistantApp PRIVATE
    Qt6::Core
    Qt6::Widgets  
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
)

# Propiedades específicas para Raspberry Pi
if(CMAKE_SYSTEM_PROCESSOR MATCHES "arm")
    message(STATUS "Configurando para ARM/Raspberry Pi")
    target_compile_definitions(PuertoChoAssistantApp PRIVATE RASPBERRY_PI)
    
    # Optimizaciones para ARM
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2 -march=armv7-a -mfpu=neon-vfpv4")
endif()

# Instalar el ejecutable
install(TARGETS PuertoChoAssistantApp
    BUNDLE DESTINATION .
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
) 