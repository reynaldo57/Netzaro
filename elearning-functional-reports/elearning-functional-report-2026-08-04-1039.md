# Reporte Funcional de Proyecto E-learning (Solo Lectura)

**Proyecto:** C:\Netzaro (Django — apps `store`, `cart`, `payment`)
**Fecha:** 2026-08-04 10:39
**Alcance:** Exclusivamente funcional/producto, desde la perspectiva de un usuario final (estudiante) y de un instructor. No se evalúa calidad de código ni seguridad (SQLi, XSS, autenticación, claves hardcodeadas, autorización como vector de ataque, etc.).

> Este reporte fue generado en modo solo lectura, a partir del código y las plantillas del proyecto. Ningún archivo fue modificado, creado ni eliminado salvo este reporte.

## Resumen Ejecutivo

Netzaro es, en esencia, una plataforma de e-learning: los **instructores** publican **cursos** (`Product`) y suben **lecciones** (`Clase`, archivos descargables) organizadas en tres niveles — Básico, Intermedio y Avanzado. El problema central es que **los dos únicos mecanismos de "pago que desbloquea contenido" no están conectados entre sí**: pagar el curso completo por el checkout principal (PayPal/Stripe/Izipay) no matricula al estudiante en nada, mientras que el único desbloqueo de contenido real es un micropago fijo de $2 por lección Avanzada, ajeno al precio del curso. A esto se suma que, en casi todos los métodos de pago, el pedido nunca llega a marcarse como "pagado" en la base de datos por errores concretos en el código. No existen conceptos típicos de e-learning como progreso del estudiante, quizzes, certificados (aunque se promocionan en el sitio) ni notificaciones.

**Issues bloqueantes: 4** — todos relacionados con inscribirse/pagar un curso y no obtener acceso, o con que el equipo no tenga visibilidad de quién compró qué.

**Top 3 recomendaciones:**
1. Definir y construir una **matrícula real** (registro de qué estudiante tiene acceso a qué curso) y conectarla al pago — hoy no existe tal registro; solo existe el pago aislado por lección.
2. Arreglar el guardado de "pagado" en los tres métodos de pago (falta un paréntesis en el webhook de PayPal, falta el webhook de Stripe, e Izipay no actualiza el pedido).
3. Agregar seguimiento de progreso del estudiante sobre las lecciones que ya tiene, aprovechando que el modelo de niveles (Básico/Intermedio/Avanzado) ya existe.

---

## Estado Funcional Actual (Inventario)

| Funcionalidad | Estado | Dónde vive |
|---|---|---|
| Catálogo de cursos (listado, categorías, búsqueda) | Presente | `store/views.py` (`index`, `category`, `search`), plantillas `index.html`, `category.html`, `search.html` |
| Ficha de curso (detalle, precio, video promocional, comentarios) | Presente | `store/views.py::product`, `product.html` |
| Panel de instructor: crear/editar/eliminar curso | Presente | `add_product`, `update_product`, `my_products` |
| Subida de lecciones por curso y nivel (Básico/Intermedio/Avanzado) | Presente | `add_clase`, modelo `Clase` |
| Descarga de lecciones Básico/Intermedio | Presente (libre, sin login) | `product_detail.html` |
| Desbloqueo de lección Avanzada vía micropago ($2, Izipay) | Presente y funcional de punta a punta | `izipay_checkout_clase` / `izipay_result_clase` |
| Carrito y checkout de curso completo | Presente pero desconectado del acceso al contenido | `cart/`, `payment/views.py` |
| Pagos: PayPal, Stripe, Izipay (para el curso completo) | Presente pero roto en el marcado de "pagado" | `payment/hooks.py`, `payment/views.py` |
| "Matrícula"/inscripción formal | No existe como tal — hay un sistema de comentarios etiquetado internamente como matrícula | `Comment` / `CommentResponse` |
| Cuenta de usuario (registro, login, editar perfil, cambiar contraseña logueado) | Presente | `store/views.py`, `store/forms.py` |
| Panel de pedidos para staff | Presente pero no funciona (queda vacío) | `not_shipped_dash`, `shipped_dash` |
| Panel administrativo | Presente (Django admin genérico) | `admin.py` de cada app |
| Reproductor de lecciones dentro de la plataforma (video/slides embebidos) | No existe — solo descarga de archivo | `Clase.fileClase` |
| Seguimiento de progreso del estudiante | No existe | — |
| Quizzes/evaluaciones | No existe | — |
| Certificados | No existe (pero se promociona en el sitio) | `search.html` |
| Notificaciones (email/push/in-app) | No existe | — |
| Roles diferenciados estudiante/instructor/admin | No existe formalmente — cualquier usuario logueado puede publicar cursos | `add_product` |

---

## Issues Detectados

### 🔴 Bloqueantes

#### 1. Pagar un curso completo no inscribe ni da acceso a ninguna lección
**Ubicación:** `payment/views.py` (`billing_info`, `proccess_order`), `store/models.py::Clase`, `store/views.py::product_detail_view`
Cuando un estudiante agrega un curso al carrito y completa el pago por PayPal, Stripe o Izipay, el sistema crea un `Order`/`OrderItem`, pero **nada conecta ese pedido con el acceso a las lecciones (`Clase`) del curso**. El único mecanismo que realmente desbloquea contenido es un botón aparte, "Pagar $2 por PDF", que cobra un monto fijo por cada lección de nivel Avanzado, sin relación con el precio del curso ni con haberlo comprado antes. Desde la perspectiva del estudiante: pagar el curso completo no le da nada tangible.

#### 2. El pago de un curso casi nunca queda registrado como "pagado" en la base de datos
**Ubicación:** `payment/hooks.py:26`, `payment/views.py` (`stripe_checkout`, `izipay_result`, `ipn`)
- El webhook de PayPal ejecuta `my_Order.save` **sin paréntesis** — no llama al método, así que el cambio a `paid = True` nunca se guarda.
- No existe ningún webhook de Stripe que confirme el pago; se abre la sesión de pago y ahí termina el rastro.
- Las vistas que reciben la respuesta de Izipay para el pago del curso (`izipay_result`, `ipn`) no tocan el `Order` en absoluto.
Por contraste, el flujo paralelo de pago por lección individual (`izipay_result_clase`) sí marca correctamente el pago, lo que confirma que el patrón correcto existe en el proyecto pero no se aplicó al flujo principal de inscripción a un curso.

#### 3. El equipo no tiene forma de ver quién se inscribió/pagó un curso
**Ubicación:** `payment/views.py:56-103` (`not_shipped_dash`, `shipped_dash`)
Estas pantallas están pensadas como el panel donde el staff (usuarios `is_superuser`, según el menú "Orders" en la navegación) revisa las inscripciones pendientes. Pero la consulta filtra `Order.objects.filter(user=request.user, ...)` — es decir, muestra los pedidos donde el propio superusuario es el comprador, no los pedidos de los estudiantes. En la práctica, el panel queda vacío y el equipo no tiene visibilidad operativa de las inscripciones.

#### 4. Se registra la "matrícula" y se vacía el carrito antes de que el pago se confirme
**Ubicación:** `payment/views.py::billing_info`
Al llegar a la pantalla de pago, el sistema ya crea el `Order` (la "matrícula") y vacía el carrito del estudiante, **antes** de que haga clic en pagar o de que el proveedor confirme el cobro. Si el estudiante abandona el pago, se cae la conexión, o el pago es rechazado, queda una matrícula fantasma sin pagar y el estudiante pierde su selección de cursos, teniendo que rearmarla a mano para reintentar.

### 🟡 Parciales

#### 5. Agregar un curso ya presente en el carrito ignora la cantidad
**Ubicación:** `cart/cart.py:33-42`
Si el curso ya está en el carrito, el método `add()` simplemente no hace nada (`pass`) en vez de actualizar la cantidad indicada. Solo el flujo de "actualizar cantidad" en el resumen del carrito puede cambiarla, pero el botón "Reserva una Clase" de la ficha del curso nunca lo usa.

#### 6. El sistema de "comentarios" está etiquetado como matrícula pero no lo es
**Ubicación:** `store/forms.py` (`CommentForm`, `CommentResponseForm`), `store/views.py::product`
Los textos internos del formulario ("¿Por qué te interesa esta clase?", "¿Qué te motivó a matricularte?") sugieren que esto debía funcionar como una solicitud de inscripción, pero técnicamente es un hilo de comentarios público (`Comment`/`CommentResponse`) sin relación con si la persona está realmente inscrita o pagó el curso. Cualquier visitante puede "matricularse" dejando un comentario, sin que eso tenga efecto real en su acceso.

#### 7. Las lecciones son solo archivos para descargar, no contenido reproducible en la plataforma
**Ubicación:** `store/models.py::Clase` (`fileClase`), `product_detail.html`
No hay un reproductor de video, lector de slides o visor embebido — cada lección es un enlace de descarga directa a un archivo (`<a href="{{ clase.fileClase.url }}" download>`). El campo `video` del modelo `Product` solo se usa como material promocional en la ficha del curso, no como contenido de una lección.

#### 8. Control de acceso por nivel inconsistente y no ligado a inscripción
**Ubicación:** `store/models.py::Clase.requiere_pago`, `product_detail.html`
Las lecciones Básico e Intermedio son descargables por cualquiera, incluidos usuarios sin cuenta, mientras que solo Avanzado exige el micropago de $2. No hay ningún nivel que dependa de estar "inscrito" en el curso en general — el acceso se decide lección por lección, no por matrícula.

#### 9. No existe un "Mis cursos" para el estudiante
**Ubicación:** navegación (`navbar.html`), vistas de `payment`
Un estudiante logueado no tiene ninguna pantalla que liste los cursos que compró/a los que tiene acceso; las únicas vistas de pedidos (`orders`, `shipped_dash`, `not_shipped_dash`) están pensadas para staff, y además muestran datos de envío de producto físico (dirección, "shipped"), no de acceso a contenido educativo.

#### 10. Cualquier usuario puede publicar cursos; no hay rol de "instructor" diferenciado
**Ubicación:** `store/views.py::add_product`
`add_product` solo exige `@login_required`, sin ninguna verificación de rol. Cualquier estudiante registrado puede convertirse en "instructor" y publicar un curso, sin aprobación ni distinción de perfil en la plataforma.

### 🟢 Menores

#### 11. Selector de cantidad en el carrito limitado a 1–3
**Ubicación:** `store/templates/cart_summary.html:99-101`

#### 12. Enlace "You have to login" no lleva a ningún lado (`href="#"`)
**Ubicación:** `store/templates/cart_summary.html:119`

#### 13. Se promociona "Certificación" al completar un curso, pero no existe
**Ubicación:** `store/templates/search.html:242-246`
El sitio muestra la tarjeta "Certificación: Recibe un certificado al completar tu curso para potenciar tu perfil profesional", pero no hay ningún modelo, vista o generación de certificados en el proyecto — es una promesa visible al estudiante que el sistema no cumple.

#### 14. Mensaje con error de tipeo visible al usuario
**Ubicación:** `store/views.py:70` — "You must be loogged in to view that page..."

---

## Qué Más Puedes Agregar (Gap Analysis)

### Must-have para un e-learning básico

- **Matrícula/inscripción real, independiente del pago roto.** Ya existe el modelo `Order`/`OrderItem` para el cobro; falta un registro explícito de "este estudiante tiene acceso a este curso" (similar a `Clase.usuarios_pagados`, que ya funciona para lecciones individuales) que se active cuando el pedido del curso se marca pagado. Es la pieza que más impacto tiene: hoy es literalmente imposible completar el flujo "pagar un curso → tener acceso a él".
- **Seguimiento de progreso del estudiante.** El proyecto ya organiza el contenido en niveles (Básico/Intermedio/Avanzado) por curso; agregar un registro de qué lecciones completó cada estudiante permitiría mostrar progreso (ej. "2 de 5 lecciones completadas") reutilizando esa estructura existente, en vez de partir de cero.
- **Reproductor de contenido dentro de la plataforma.** Actualmente las lecciones son solo descargas; para un e-learning, tener un visor embebido (video/PDF/slides) mejora sustancialmente la experiencia y permite, a futuro, medir consumo real (¿vio la lección o solo la descargó?).
- **Quizzes/evaluaciones con calificación.** No hay ningún rastro de esto; es una funcionalidad central de casi cualquier e-learning y hoy no existe punto de partida en el modelo de datos.
- **Notificaciones al estudiante.** No se encontró ningún envío de email en el proyecto. Como mínimo, confirmar la inscripción/pago y avisar si el pago falló — hoy el estudiante puede quedar sin saber si su compra se procesó.
- **Recuperación de contraseña por email.** Solo existe cambio de contraseña estando logueado; un estudiante que la olvida y no puede iniciar sesión no tiene forma de recuperarla.
- **"Mis cursos" para el estudiante.** Una pantalla simple que liste `Order`/cursos con acceso otorgado, distinta de los paneles de staff orientados a envío físico.
- **Roles claros (estudiante/instructor/admin).** Ya existe una distinción implícita (`Product.user` como dueño/instructor, `is_superuser` para panel de staff), pero falta formalizarla para poder, por ejemplo, restringir quién puede publicar cursos o aprobarlos antes de publicarse.

### Nice-to-have para diferenciarse

- **Certificados de finalización.** Ya se promociona en el sitio (`search.html`) — implementarlo cerraría una brecha entre lo que se ofrece y lo que existe, y depende de tener antes seguimiento de progreso.
- **Convertir el sistema de comentarios en un foro/matrícula real ligado a inscripción**, en vez de comentarios públicos anónimos etiquetados como "matrícula" sin verificación de que el usuario esté inscrito.
- **Analítica para el instructor** (cuántos estudiantes se inscribieron, progreso agregado por curso), aprovechando que ya existe `my_products` como panel del instructor.
- **Calificación numérica de cursos**, además de los comentarios de texto que ya existen.
- **Cupones/descuentos y precios reales por lección**, reemplazando el monto fijo de $2 hardcodeado para las lecciones Avanzadas, para que el instructor pueda fijar su propio precio.

---

## Nota Metodológica

Este análisis fue automático y de solo lectura: se inspeccionaron modelos, vistas, formularios, URLs y plantillas de las apps `store`, `cart` y `payment` (69 archivos de código/plantillas de negocio, excluyendo estáticos de terceros, migraciones y binarios). No se ejecutó el proyecto ni se probaron los flujos en un navegador, por lo que algunos hallazgos deberían confirmarse con pruebas manuales antes de priorizar trabajo sobre ellos. No se evaluaron temas de seguridad (por ejemplo, se detectaron claves de Stripe/Izipay en texto plano en el código, pero eso queda fuera del alcance de este reporte funcional).
