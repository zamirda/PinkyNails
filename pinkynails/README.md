# pinkynails.ym (Django)

Página de citas para uñas de manos y pies: galería, agenda con solo horas libres, estilos por temporada,
panel con usuario y contraseña, y avisos por WhatsApp y Google Calendar.

## 1. Instalar y correr en tu computador
```bash
python -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # y llena SECRET_KEY (DEBUG=1 para pruebas)
python manage.py makemigrations citas
python manage.py migrate
python manage.py crear_admin --usuario yilemor   # te pide la contraseña
python manage.py runserver
```
- Página: http://127.0.0.1:8000/
- Panel de citas: http://127.0.0.1:8000/panel/entrar/
- Fotos de la galería y horas bloqueadas: http://127.0.0.1:8000/django-admin/ (mismo usuario)

## 2. Qué hace cada cosa
- **Horarios:** 7, 8, 9, 10 y 11 a. m. y 2, 3, 4 y 5 p. m. (cada cita dura 1 hora). Se cambian en `citas/horarios.py`.
- **Solo lo libre:** la clienta nunca ve horas ocupadas ni datos de otras clientas. Una restricción en la base de datos impide dos citas en la misma hora.
- **Fotos:** en `/django-admin/` > Fotos sube las de Murillo. Mientras no haya ninguna se ven 8 de ejemplo (no son suyas: reemplázalas).
- **Bloqueos:** en `/django-admin/` > Bloqueos marca días u horas en que no atiende.
- **Temporadas:** Día de la Mujer (1-10 mar), Día de la Madre (1 may hasta el 2.º domingo), Semana Santa, octubre y diciembre. Para probarlas, entra como administradora y agrega `?tema=dic`, `?tema=octubre`, `?tema=madre`, `?tema=mujer`, `?tema=semana` o `?tema=base` a la dirección de la página.
- **Cambiar usuario/contraseña:** en el panel > "Cambiar usuario o contraseña". Llega un código de 6 dígitos por WhatsApp a `VERIFY_PHONE`; vale 10 minutos y tiene 5 intentos.
- **Seguridad:** contraseñas cifradas por Django, protección CSRF, bloqueo de 10 minutos tras 5 intentos fallidos de acceso, límite de 10 agendamientos por hora por conexión.

## 3. WhatsApp (CallMeBot, gratis, uso personal)
Cada número que recibe mensajes debe activarse una vez en callmebot.com (sigue las instrucciones de su página; te devuelve una clave).
- `WA_PHONE` y `WA_KEY`: el número del negocio que recibe el aviso de cada cita nueva.
- `VERIFY_PHONE` y `VERIFY_KEY`: el celular que recibe los códigos (ahora 302 661 8958, el de pruebas).
Sin clave no se envía nada, pero las citas se guardan igual. Si el negocio crece, cambia a WhatsApp Business (edita `citas/services.py`, función `whatsapp`).

## 4. Google Calendar (opcional)
1. En Google Cloud crea un proyecto, activa "Google Calendar API" y crea una **cuenta de servicio**; descarga su archivo JSON.
2. En Google Calendar de la dueña: Configuración del calendario > "Compartir con determinadas personas" > agrega el correo de la cuenta de servicio con permiso "Hacer cambios en eventos".
3. En `.env`: `GOOGLE_CALENDAR_ID` (el correo del calendario o el ID que sale en su configuración) y `GOOGLE_CREDENTIALS_FILE` (ruta al JSON). Nunca subas ese JSON a GitHub.
Cada cita nueva crea un evento con recordatorios 1 día y 1 hora antes; al cancelarla en el panel, se borra el evento.

## 5. Publicarla
Funciona en Render, Railway, PythonAnywhere o cualquier servidor con Python. En producción: `DEBUG=0`, una `SECRET_KEY` larga,
`ALLOWED_HOSTS` con tu dominio, `CSRF_TRUSTED_ORIGINS=https://tudominio.com`, y ejecuta
`python manage.py collectstatic --noinput` y `gunicorn pinkynails.wsgi`. Usa un disco que no se borre (la base es SQLite y las fotos van a `media/`).
