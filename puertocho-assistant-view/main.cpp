#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QIcon>
#include <QDir>

int main(int argc, char *argv[])
{
    // Configuración para mejorar el rendimiento en Raspberry Pi
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QCoreApplication::setAttribute(Qt::AA_UseHighDpiPixmaps);
    
    QGuiApplication app(argc, argv);
    
    // Información de la aplicación
    app.setApplicationName("PuertoCho Assistant Dashboard");
    app.setApplicationVersion("1.0.0");
    app.setOrganizationName("PuertoCho");
    app.setOrganizationDomain("puertocho.local");
    
    QQmlApplicationEngine engine;
    
    // Configurar el contexto QML con información del sistema
    QQmlContext *context = engine.rootContext();
    context->setContextProperty("applicationVersion", app.applicationVersion());
    context->setContextProperty("applicationName", app.applicationName());
    
    // Cargar el archivo QML principal
    const QUrl url(QStringLiteral("qrc:/main.qml"));
    QObject::connect(&engine, &QQmlApplicationEngine::objectCreated,
                     &app, [url](QObject *obj, const QUrl &objUrl) {
        if (!obj && url == objUrl)
            QCoreApplication::exit(-1);
    }, Qt::QueuedConnection);
    
    engine.load(url);
    
    return app.exec();
} 