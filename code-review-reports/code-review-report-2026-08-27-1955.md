# Reporte de Code Review (Solo Lectura)

**Proyecto:** Netzaro (ecom) — Django ecommerce/e-learning
**Fecha:** 2026-08-27 19:55
**Archivos analizados en profundidad:** 17
**Archivos excluidos (gitignore/binarios/lockfiles/estáticos):** ~640 (staticfiles/, media/, `.pyc`, imágenes, css/js de terceros)

> Este reporte fue generado en modo solo lectura. Ningún archivo de código
> fue modificado, creado ni eliminado durante este análisis.

## Veredicto rápido: ¿listo para producción?

**No.** Hay secretos de la pasarela de pago y de Django commiteados en el repositorio, `DEBUG = True` en el settings usado para producción, control de acceso roto en endpoints de órdenes/pagos, y un bug que rompe el checkout de invitados (`NameError`). Cualquiera de los hallazgos 🔴 por sí solo debería bloquear un despliegue; hay siete.

## Resumen Ejecutivo

| Severidad | Cantidad |
|---|---|
| Crítico | 8 |
| Alto | 6 |
| Medio | 5 |
| Bajo | 4 |
| **Total** | **23** |

| Categoría | Crítico | Alto | Medio | Bajo | Total |
|---|---|---|---|---|---|
| Bugs / errores de lógica | 1 | 1 | 0 | 0 | 2 |
| Seguridad | 6 | 3 | 1 | 0 | 10 |
| Configuración / despliegue | 1 | 2 | 1 | 0 | 4 |
| Código muerto | 0 | 1 | 0 | 0 | 1 |
| Manejo de errores | 0 | 0 | 1 | 0 | 1 |
| Anti-patrones | 0 | 0 | 1 | 0 | 1 |
| Estilo / naming | 0 | 0 | 0 | 4 | 4 |

## 🔴 Crítico

### `Keys/keys.py:5-27` — Credenciales de la pasarela de pago (Izipay) commiteadas en texto plano
- **Categoría:** Seguridad
- **Descripción:** El archivo contiene `USERNAME`, `PASSWORD`, `PUBLIC_KEY` y `HMACSHA256` de Izipay hardcodeados y trackeados en git (aparece en `git ls-files`). Incluye además, comentado, el bloque de **claves de producción** (`prodpassword_...`, `publickey_...`). Cualquiera con acceso al repositorio (colaborador, fork, o si el repo es o llega a ser público) tiene control total de la cuenta comercial: puede cobrar, ver transacciones y, combinado con el hallazgo siguiente, falsificar confirmaciones de pago.
- **Sugerencia:** Mover todas las claves a variables de entorno, añadir `Keys/` al `.gitignore`, eliminar el archivo del historial de git (`git filter-repo` / BFG) y **rotar todas las claves con Izipay inmediatamente** (ya están expuestas).

### `ecom/settings.py:24` — `SECRET_KEY` de Django hardcodeado y commiteado
- **Categoría:** Seguridad
- **Descripción:** La `SECRET_KEY` está escrita literalmente en el archivo trackeado por git. Esta clave firma las cookies de sesión, tokens de reseteo de contraseña (`store/tokens.py`) y el token de verificación de email. Con la clave expuesta, un atacante puede forjar sesiones autenticadas y tokens de "olvidé mi contraseña"/verificación de email para cualquier usuario.
- **Sugerencia:** `SECRET_KEY = os.environ['SECRET_KEY']`, generar una nueva clave, y rotarla (esto invalidará sesiones y tokens pendientes, es esperado).

### `ecom/settings.py:27` — `DEBUG = True` hardcodeado
- **Categoría:** Configuración / despliegue
- **Descripción:** No hay ninguna variable de entorno controlando `DEBUG`; está fijo en `True`. En producción esto expone tracebacks completos (código fuente, valores de settings, variables locales) a cualquier visitante que dispare un error 500, y sirve `/media/` con el handler de desarrollo (ver hallazgo relacionado abajo).
- **Sugerencia:** `DEBUG = os.environ.get('DEBUG', 'False') == 'True'`, con `False` como default seguro.

### `payment/views.py:26-53` (`orders`) — Control de acceso roto (IDOR) sobre órdenes de cualquier usuario
- **Categoría:** Seguridad
- **Descripción:** La condición es `if request.user.is_authenticated and request.user.is_authenticated:` (repetida, sin sentido — no valida que la orden pertenezca al usuario ni que sea staff). Cualquier usuario logueado puede visitar `/payment/orders/<pk>` con **cualquier `pk`** y ver nombre completo, email y dirección de envío de otro cliente, y con un POST cambiar el estado `shipped`/`date_shipped` de esa orden ajena.
- **Sugerencia:** `if request.user.is_authenticated and (order.user_id == request.user.id or request.user.is_staff):` antes de exponer/mutar la orden.

### `payment/views.py:485-517` y `:601-633` (`izipay_checkout`, `izipay_checkout_clase`) — Generación de sesión de pago sin autenticación ni verificación de dueño
- **Categoría:** Seguridad
- **Descripción:** La URL `izipay_checkout/<int:order_id>/` (payment/urls.py:16) no tiene `@login_required` ni valida `order.user == request.user`. Cualquiera (incluso anónimo) puede solicitar un token de pago válido para la orden de otra persona, exponiendo el monto y permitiendo iniciar una sesión de cobro sobre una orden ajena.
- **Sugerencia:** Añadir `@login_required` y `get_object_or_404(Order, id=order_id, user=request.user)`.

### `payment/views.py:564-586` (`ipn`) — Verificación de firma con la clave incorrecta
- **Categoría:** Seguridad
- **Descripción:** `izipay_result` y `izipay_result_clase` verifican la firma con `keys["HMACSHA256"]` (correcto según la documentación de Izipay/Lyra para notificaciones), pero `ipn` la verifica con `keys["PASSWORD"]`. Esto es inconsistente: o el endpoint `/payment/ipn` nunca validará notificaciones reales de Izipay (rompiendo esa vía de confirmación), o —peor— multiplica los secretos con los que se puede forjar una firma válida. Como **ambas claves (`PASSWORD` y `HMACSHA256`) ya están expuestas en git** (ver primer hallazgo), cualquiera puede calcular un `kr-hash` válido y hacer POST directo a `/payment/izipay_result`, `/payment/ipn` o `/payment/izipay/result/` marcando **cualquier orden existente como pagada**, obteniendo acceso gratuito a cursos sin pagar.
- **Sugerencia:** Usar consistentemente la clave HMAC-SHA-256 dedicada para notificaciones (nunca la `PASSWORD`), y sobre todo resolver el hallazgo de exposición de claves — mientras las claves sigan en el repo, este control es inútil.

### `payment/hooks.py:9-26` (`paypal_payment_received`) — El IPN de PayPal no valida estado, receptor ni monto
- **Categoría:** Seguridad
- **Descripción:** El handler marca `order.paid = True` para **cualquier** IPN verificado por `django-paypal`, sin comprobar `payment_status == ST_PP_COMPLETED`, sin comparar `receiver_email` contra `settings.PAYPAL_RECEIVER_EMAIL`, y sin comparar `mc_gross`/`mc_currency` contra `order.amount_paid`. Un IPN de un pago `Pending`, `Reversed`, `Denied`, dirigido a una cuenta receptora distinta, o por un monto menor (ej. $0.01), también otorgaría acceso pagado al curso. Este es exactamente el checklist estándar que la documentación de `django-paypal` pide validar y aquí falta.
- **Sugerencia:**
  ```python
  if (paypal_obj.payment_status == ST_PP_COMPLETED
          and paypal_obj.receiver_email.lower() == settings.PAYPAL_RECEIVER_EMAIL.lower()
          and paypal_obj.mc_gross == my_Order.amount_paid
          and paypal_obj.mc_currency == 'USD'):
      my_Order.paid = True
      my_Order.save()
  ```

### `payment/views.py:371-398` (`billing_info`, rama de invitado) — `NameError` que rompe el checkout de usuarios no autenticados
- **Categoría:** Bugs / errores de lógica
- **Descripción:** Dentro del `else:` (usuario **no** autenticado), al crear cada `OrderItem` se usa `user=user` (línea 397), pero la variable `user` nunca se define en esa rama (solo existe como `user = request.user` en la rama `if request.user.is_authenticated:` de más arriba, línea 324). Cualquier visitante no logueado que intente comprar vía `billing_info` (el flujo normal de checkout) provoca un `NameError: name 'user' is not defined` y un error 500, **rompiendo la compra para todo usuario invitado**. (Comparar con `proccess_order`, que sí resuelve esto correctamente omitiendo `user=` en su rama de invitado — línea 219.)
- **Sugerencia:** Quitar `user=user` de esa rama (o usar `user=None`), igual que en `proccess_order`.

## 🟠 Alto

### `ecom/settings.py:85-91` — Base de datos SQLite en un host con filesystem efímero
- **Categoría:** Configuración / despliegue
- **Descripción:** `ALLOWED_HOSTS` incluye `netzaro.onrender.com` y `netzaro.pythonanywhere.com`, pero `DATABASES` está hardcodeado a `sqlite3` sin override por variable de entorno (`DATABASE_URL`). En Render (plan estándar/free), el filesystem del servicio web es efímero: cada deploy o reinicio del contenedor **borra `db.sqlite3`**, es decir, se pierden usuarios, órdenes, pagos y progreso de cursos. Esto también explica por qué `db.sqlite3` aparece commiteado y modificado en git (probablemente como "respaldo" manual), lo cual es en sí mismo un problema (ver Medio, más abajo) y no resuelve el riesgo de pérdida de datos entre despliegues.
- **Sugerencia:** Usar Postgres administrado (add-on de Render) vía `DATABASE_URL` + `dj-database-url`/`django-environ` en producción.

### `ecom/urls.py:31-32` junto con `ecom/settings.py:27` — `/media/` deja de servirse al corregir `DEBUG`
- **Categoría:** Configuración / despliegue
- **Descripción:** Las URLs de `MEDIA_URL` solo se registran `if settings.DEBUG:`. WhiteNoise (configurado en `MIDDLEWARE`) solo sirve `STATIC_ROOT`, no `MEDIA_ROOT`. En cuanto se corrija el hallazgo crítico de `DEBUG=True`, **todas las imágenes de producto, fotos de perfil y certificados de profesores subidos por usuarios dejarán de ser accesibles** (404), porque no hay storage backend (S3, Cloudinary, whitenoise para media, etc.) configurado para producción.
- **Sugerencia:** Antes de desactivar `DEBUG`, configurar un backend de almacenamiento de media apto para producción (S3/Cloudinary/Backblaze) o servir `/media/` explícitamente vía Nginx/WhiteNoise fuera del bloque `if DEBUG`.

### `requirements.txt:5` — Django pineado a una versión EOL/vulnerable e inconsistente con el código
- **Categoría:** Seguridad / Configuración
- **Descripción:** `Django==3.2.19` (release de abril 2023, rama 3.2 ya sin soporte de seguridad desde abril 2024), mientras que el docstring de `ecom/settings.py:4` indica *"Generated by 'django-admin startproject' using Django 5.1.3"*. Si lo que realmente corre en producción es 3.2.19, faltan múltiples parches de seguridad publicados después de esa versión; si en realidad se está desarrollando/probando contra 5.1.x pero el `requirements.txt` quedó desactualizado, el entorno de producción podría instalar una versión distinta (y con API distinta) a la que se probó localmente.
- **Sugerencia:** Fijar y verificar una única versión de Django, actualmente soportada, y usarla igual en desarrollo y `requirements.txt`.

### `payment/views.py:56-106` (`not_shipped_dash`, `shipped_dash`) — El panel de envíos filtra por el admin, no por el dueño real de la orden
- **Categoría:** Bugs / errores de lógica
- **Descripción:** En el POST, ambas vistas hacen `Order.objects.get(id=num, user=request.user)`, donde `request.user` es el superusuario que está operando el panel — no el cliente dueño de la orden. En la práctica, un admin **nunca podrá marcar como enviada una orden de un cliente real** (solo funcionaría si, por coincidencia, la orden fuera del propio superusuario), porque el filtro `user=request.user` casi siempre falla y cae en el `except Order.DoesNotExist`. El dashboard de envíos está roto para su propósito.
- **Sugerencia:** Quitar el filtro `user=request.user`: `Order.objects.get(id=num)` (el permiso ya está garantizado por `if not request.user.is_superuser: return redirect(...)` al inicio de la vista).

### `store/models.py:554-582` (`Coupon`) — `times_used` nunca se incrementa; `max_uses` no se respeta
- **Categoría:** Bugs / errores de lógica (impacto financiero)
- **Descripción:** `es_valido()` comprueba `self.times_used >= self.max_uses`, pero una búsqueda en todo el repo confirma que **ningún** código incrementa `times_used` al aplicar un cupón (`cart.apply_coupon`, `billing_info`, etc. nunca hacen `coupon.times_used += 1; coupon.save()`, ni siquiera al confirmarse el pago). Un cupón configurado con `max_uses=1` puede usarse un número ilimitado de veces.
- **Sugerencia:** Incrementar `times_used` de forma atómica (`F('times_used') + 1`) en el momento en que la orden asociada pasa a `paid=True` (por ejemplo, en la señal `grant_course_access_on_payment` de `payment/models.py`), no solo al aplicarlo al carrito.

### `payment/forms.py:50-60` (`PaymentForm`) — Formulario de tarjeta "fantasma" que no procesa nada
- **Categoría:** Código muerto
- **Descripción:** `PaymentForm` recoge `card_number`, `card_cvv_number`, `card_exp_date`, etc., y se renderiza en `billing_info.html`/`proccess_order.html`, pero ninguna vista lee ni guarda esos campos (el pago real va por Izipay/PayPal). Hoy es solo una UI confusa que no hace nada al enviarse; el riesgo real es que alguien, sin saber que está "muerto", lo conecte a un modelo o a un log más adelante, convirtiéndolo en una violación de PCI-DSS (datos de tarjeta en texto plano tocando el servidor).
- **Sugerencia:** Eliminar el formulario y su template, o marcarlo explícitamente como deshabilitado/no funcional si se conserva por diseño visual.

## 🟡 Medio

### `.gitignore:1-2` — Prácticamente vacío; secretos, base de datos y artefactos de build están trackeados
- **Categoría:** Configuración / despliegue
- **Descripción:** El `.gitignore` solo excluye dos patrones de video. Como consecuencia, están commiteados en el repo: `db.sqlite3` (datos reales de usuarios/órdenes), todos los `__pycache__/*.pyc`, y el directorio completo `staticfiles/` (artefactos generados por `collectstatic`, incluyendo assets de terceros como jQuery/Select2). Esto es la causa raíz que permite que `Keys/keys.py` y `db.sqlite3` terminen expuestos (hallazgos críticos de arriba).
- **Sugerencia:** Añadir `__pycache__/`, `*.pyc`, `db.sqlite3`, `staticfiles/`, `Keys/keys.py`, `.env` al `.gitignore`, y quitarlos del tracking (`git rm --cached`) sin borrar los archivos locales.

### `store/views.py:326-338` (`my_products`) — Borrado de producto vía GET
- **Categoría:** Anti-patrón / Seguridad
- **Descripción:** `delete = request.GET.get('delete', None)` borra el producto con una petición GET (típicamente un `<a href>`). Aunque valida `request.user.id != product.user.id`, sigue siendo una acción destructiva disparable por CSRF vía link/prefetch de navegador/crawler, sin protección CSRF (los GET no la tienen) ni confirmación.
- **Sugerencia:** Mover el borrado a un POST con `{% csrf_token %}` (patrón ya usado correctamente en `eliminar_quiz`, `eliminar_pregunta`, `eliminar_tarea`, `eliminar_coupon` del mismo archivo).

### `store/views.py:214-226` (`category`) — `except:` desnudo
- **Categoría:** Manejo de errores
- **Descripción:** Captura cualquier excepción (incluyendo errores de programación, no solo `Category.DoesNotExist`) y la convierte silenciosamente en un mensaje genérico "That category Doest exist", dificultando detectar bugs reales.
- **Sugerencia:** `except Category.DoesNotExist:`.

### `payment/views.py:539-562`, `:635-677` — Los webhooks de Izipay devuelven `raise Exception(...)` sin capturar
- **Categoría:** Manejo de errores
- **Descripción:** `izipay_result` hace `raise Exception("No post data received!")` / `raise Exception("Invalid signature")` sin capturarla; con `DEBUG=True` esto expone un traceback completo al endpoint público del webhook (y a la pasarela de pago). Con `DEBUG=False` sería un 500 genérico sin registrar nada útil en logs propios.
- **Sugerencia:** Devolver `HttpResponse(status=400/403)` como ya hace correctamente `izipay_result_clase`, y loguear el motivo con `logging`.

### `store/forms.py:123-149` (`SignUpForm`) — El email no es único
- **Categoría:** Bugs / errores de lógica
- **Descripción:** El modelo `User` de Django no impone `email` único por defecto, y `SignUpForm` no agrega esa validación. Dado que el proyecto acaba de incorporar "recuperar contraseña por email" y "validación de email" (commits recientes), dos cuentas podrían registrarse con el mismo email, lo que puede volver ambiguo o inseguro el flujo de reseteo/verificación (dependiendo de cómo busquen el usuario por email en esas vistas, no auditadas en detalle en esta pasada).
- **Sugerencia:** Validar unicidad de `email` en `clean_email()` del formulario.

## 🟢 Bajo

### `payment/views.py:516` — `print(token)` de depuración en producción
- **Categoría:** Estilo / limpieza
- **Descripción:** Imprime el `formToken` de Izipay a stdout; no es información crítica (se entrega igual al navegador) pero es un resto de debug que no debería llegar a producción.
- **Sugerencia:** Quitarlo o reemplazarlo por `logger.debug(...)`.

### `store/views.py:316,372,546` — `print(form.errors)` en `add_product`, `update_product`, `add_clase`
- **Categoría:** Estilo / limpieza
- **Descripción:** Varios `print(form.errors)` quedaron como debugging; en producción no aparecen en ningún log accesible y ensucian stdout.
- **Sugerencia:** Quitarlos o usar `logger.debug`.

### `store/views.py:133,144,415` — Mensajes al usuario con errores tipográficos ("Loggin", "loogged") y uso de `messages.success` para errores
- **Categoría:** Estilo / naming
- **Descripción:** Varios mensajes de error usan `messages.success(...)` en vez de `messages.error(...)` (ej. líneas 133 "Your Password has been updated, Loggin again..." está bien como success, pero 144/415/461 usan success para mensajes que son claramente errores: "You must be loogged in...", "There was an error, try again"). Esto hace que el frontend probablemente los pinte con estilo de "éxito" (verde) en vez de error.
- **Sugerencia:** Usar `messages.error()` para los casos de error.

### `store/templates/order_confirmation_email.html`, `teacher_application_email.html` — Contenido de texto plano con extensión `.html`
- **Categoría:** Estilo / naming
- **Descripción:** Ambos templates se renderizan como texto plano (correcto, dado que `payment/emails.py` y `store/emails.py` los pasan como `message` de `send_mail`, no como `html_message`), pero la extensión `.html` puede inducir a un futuro mantenedor a asumir que son HTML real y cambiarlos a `EmailMultiAlternatives`/`html_message` sin adaptarlos.
- **Sugerencia:** Renombrar a `.txt` o convertir realmente a HTML con `EmailMultiAlternatives`.

## Anexo

**Alcance priorizado:** por el volumen del proyecto (~45 archivos `.py` relevantes fuera de migraciones/templates), esta pasada se concentró en lo pedido explícitamente — `ecom/settings.py`, `payment/models.py`, `payment/emails.py`, `store/emails.py`, `store/views.py` — y en todo lo que esos archivos importan directamente y resultó crítico para el veredicto de producción: `Keys/keys.py`, `payment/views.py`, `payment/hooks.py`, `payment/forms.py`, `payment/urls.py`, `ecom/urls.py`, `cart/cart.py`, partes de `store/models.py` y `store/forms.py`, `requirements.txt` y `.gitignore`. Además se hicieron búsquedas (`grep`) de patrones (`except:` desnudo, `times_used`, `card_number`, credenciales) sobre todo el repo.

**No auditado en profundidad en esta pasada** (candidatos para una siguiente revisión, especialmente si se toca autenticación/dinero): `store/tokens.py` y las vistas completas de reseteo de contraseña/verificación de email; `payment/admin.py`, `store/admin.py`; `cart/views.py`, `cart/context_processors.py`; el resto de `store/models.py` (`Clase`, `Modulo`, `Quiz`, `Certificado`); todos los templates Django (no se buscó `|safe`/XSS de forma sistemática); `store/tests.py`, `payment/tests.py`, `cart/tests.py` (no se evaluó cobertura de tests).

**Directorios/patrones excluidos:** `staticfiles/`, `media/`, `static/assets`, `*.pyc`, `__pycache__/`, migraciones (`*/migrations/*.py`, salvo lectura puntual), assets de terceros (jQuery, Select2, xregexp).

**Limitación:** no es un repo con `.gitignore` completo, por lo que `git ls-files` devolvió también artefactos de build y binarios que normalmente estarían excluidos; se filtraron manualmente para este análisis pero su sola presencia en el repo ya está documentada como hallazgo (Medio, arriba).
