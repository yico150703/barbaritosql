import os
from app import create_app
from app.extensions import db

app = create_app()

# Al arrancar en producción (Render) o desarrollo, garantizar que las tablas existan
with app.app_context():
    try:
        db.create_all()
        from app.models.usuario import Usuario
        if Usuario.query.count() == 0:
            print("Base de datos inicial vacía en Render. Ejecutando seed automático...")
            from seed import ejecutar_seed
            ejecutar_seed()
    except Exception as e:
        print("Aviso al verificar o inicializar base de datos:", e)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
