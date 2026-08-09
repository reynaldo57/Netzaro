# Reporte: Netzaro vs. Udemy/Coursera — Funcionalidades y Diseño (Solo Lectura)

**Proyecto:** C:\Netzaro (Django — apps `store`, `cart`, `payment`)
**Fecha:** 2026-08-06 12:44
**Alcance:** Comparación funcional contra Udemy/Coursera + recomendaciones de diseño (paleta "fuego"). No se modificó, creó ni eliminó ningún archivo de código — solo este reporte.
**Nota:** Existe un reporte previo (`elearning-functional-report-2026-08-04-1039.md`) centrado en bugs funcionales del flujo de pago/matrícula. Varios de esos issues bloqueantes **ya fueron corregidos** desde entonces (confirmado leyendo el código actual): ahora existe `payment/models.py::grant_course_access_on_payment` (otorga acceso al pagar), `payment/views.py::my_courses` ("Mis cursos") y el guardado de `paid=True` en PayPal/Izipay ya funciona. Este reporte no repite esos hallazgos; se enfoca en la comparación contra Udemy/Coursera.

---

## Resumen ejecutivo

Netzaro ya tiene el esqueleto correcto de un e-learning: catálogo con categorías, ficha de curso, instructores con proceso de aprobación (`TeacherApplication`), lecciones organizadas por nivel, carrito/checkout con 3 pasarelas, y ya se otorga acceso real al comprar. Lo que falta para parecerse a Udemy/Coursera **no son módulos nuevos exóticos**, sino piezas estándar de cualquier plataforma de cursos seria:

1. **Reproducción en la plataforma** — hoy una lección es un archivo para descargar, no un video/PDF que se ve dentro del sitio.
2. **Progreso y continuidad** — no existe "% completado" ni "continuar donde lo dejaste".
3. **Prueba social real** — hay comentarios de texto, pero no calificación por estrellas ni promedio visible en el catálogo.
4. **Certificados** — se promocionan en `search.html` pero no existen.
5. **Identidad visual propia** — hoy es Bootstrap por defecto (azul `#0d6efd`) mezclado con naranja/rojo puestos a mano en algunos botones (`product.html`), sin una paleta consistente.

---

## 1. Comparación funcional por área

Leyenda de estado: 🟢 Presente y sólido · 🟡 Presente pero limitado · 🔴 Ausente

### 1.1 Descubrimiento y catálogo

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| Listado de cursos por categoría | 🟢 | `category`, `category_summary` |
| Búsqueda por texto | 🟡 | `search()` solo busca en `name`/`description`, sin filtros ni orden |
| Paginación de resultados | 🔴 | `index()` hace `Product.objects.all()` sin límite — a más cursos, la home se vuelve lenta |
| Filtros combinables (precio, nivel, categoría) | 🔴 | No existe ningún filtro más allá de categoría exacta |
| Ordenar por popularidad/precio/calificación | 🔴 | No existe |
| Recomendados / "estudiantes también vieron" | 🔴 | No existe |
| Wishlist / guardar para después | 🔴 | No existe |

### 1.2 Ficha de curso

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| Precio con descuento tachado | 🟢 | `product.html` ya soporta `is_sale`/`sale_price` |
| Video promocional | 🟢 | Campo `Product.video` |
| "Lo que aprenderás" (bullets) | 🔴 | Solo hay `description` de 250 caracteres, sin estructura |
| Temario/currícula visible antes de comprar | 🟡 | Existe por nivel (`Clase`), pero se ve en una página aparte (`product_detail`), no como preview dentro de la ficha |
| Requisitos previos / audiencia | 🔴 | No existe campo para esto |
| Duración total, nº de lecciones, idioma | 🔴 | No existe |
| Instructor visible (foto, bio, nº de cursos) | 🟡 | `Profile.about_me`/`image` existen pero no se muestran en la ficha del curso |
| Calificación en estrellas + nº de reseñas | 🔴 | Solo hay comentarios de texto libre (`Comment`), sin puntaje |
| Vista previa gratuita de una lección | 🔴 | No existe — todo o nada según `nivel` |
| "X estudiantes inscritos" | 🔴 | No existe (aunque ya se puede calcular vía `OrderItem`) |

### 1.3 Reproducción de contenido

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| Reproductor embebido (video/PDF/slides) | 🔴 | `Clase.fileClase` es un link de **descarga directa** (`product_detail.html`) |
| Secciones/módulos expandibles (acordeón) | 🟡 | Existen 3 niveles fijos (Básico/Intermedio/Avanzado); Udemy permite secciones libres definidas por el instructor |
| "Continuar donde lo dejaste" | 🔴 | No existe |
| Marcar lección como completada | 🔴 | No existe |
| Descarga para offline (mobile) | 🔴 | No existe (irónicamente lo único que sí existe es la descarga forzada del archivo completo) |

### 1.4 Progreso del estudiante

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| % de curso completado | 🔴 | No existe ningún modelo de progreso |
| Indicador visual en "Mis cursos" | 🔴 | `my_courses.html` lista cursos comprados, sin barra de progreso |
| Historial de actividad reciente | 🔴 | No existe |

### 1.5 Evaluación y certificación

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| Quizzes/exámenes con calificación | 🔴 | No existe ningún modelo relacionado |
| Tareas/ejercicios entregables | 🔴 | No existe |
| Certificado de finalización | 🔴 | **Se promociona en `search.html` pero no existe** — brecha entre promesa y producto |

### 1.6 Reseñas y prueba social

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| Comentarios/preguntas sobre el curso | 🟡 | Existe (`Comment`/`CommentResponse`), pero está etiquetado internamente como "matrícula" (placeholders "¿Por qué te interesa esta clase?") y no filtra si el usuario compró el curso |
| Calificación 1-5 estrellas | 🔴 | No existe campo de rating en ningún modelo |
| Promedio de calificación visible en catálogo | 🔴 | No existe |
| Reseña "verificada" (solo quien compró) | 🔴 | Cualquier visitante puede comentar, incluso anónimo |

### 1.7 Herramientas de instructor

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| Alta de curso con imagen, precio, categoría | 🟢 | `add_product`, `AddProductForm` |
| Alta de lecciones por nivel | 🟢 | `add_clase`, modelo `Clase` |
| Proceso de aprobación de instructor | 🟢 | `TeacherApplication` + `teacher_requests_dash` — esto es un acierto, es exactamente el patrón que usa Udemy |
| Dashboard con analítica (inscritos, ingresos) | 🔴 | No existe — `my_products` solo lista/edita/borra cursos |
| Responder reseñas públicamente | 🔴 | No existe (no hay reseñas con rating tampoco) |
| Cupones de descuento por curso | 🔴 | No existe |
| Borrador vs. publicado | 🔴 | Un curso creado con `add_product` queda visible de inmediato |

### 1.8 Monetización

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| Precio fijo + oferta | 🟢 | `Product.price`/`sale_price`/`is_sale` |
| Múltiples pasarelas de pago | 🟢 | PayPal, Stripe, Izipay |
| Cupones/códigos de descuento | 🔴 | No existe |
| Bundles/paquetes de cursos | 🔴 | No existe |
| Suscripción tipo "Coursera Plus" | 🔴 | No existe (razonable no tenerlo en una v1) |
| Micropago de $2 por lección Avanzada | 🟡 | Con `grant_access` ya funcionando al comprar el curso completo, este mecanismo paralelo puede quedar redundante o confuso — vale la pena revisar si sigue siendo necesario |

### 1.9 Cuenta y perfil

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| Registro/login/editar perfil | 🟢 | Presente y funcional |
| "Mis cursos" | 🟢 | Ya agregado (`payment/views.py::my_courses`) |
| Recuperar contraseña por email | 🔴 | Solo existe cambio de password **estando logueado** (`update_password`); si el usuario la olvida, no tiene salida |
| Verificación de email al registrarse | 🔴 | No existe |
| Login social (Google) | 🔴 | No existe (no crítico para un MVP) |
| Perfil público de instructor | 🟡 | Existe `user_information.html` mostrando cursos del usuario, pero sin bio/credenciales destacadas de instructor |

### 1.10 Notificaciones

| Funcionalidad Udemy/Coursera | Estado en Netzaro | Detalle |
|---|---|---|
| Email de confirmación de compra | 🔴 | No existe envío de email en el proyecto |
| Notificación de aprobación como instructor | 🔴 | Se actualiza el estado (`teacher_request_status`) pero el usuario no es notificado, debe entrar a revisar |
| Recordatorios / novedades del curso | 🔴 | No existe |

---

## 2. Diseño: de "Bootstrap por defecto" a identidad propia con tema fuego

### Diagnóstico actual

- `static/css/styles.css` es el CSS compilado por defecto de un tema Bootstrap (`--bs-primary: #0d6efd`, azul estándar) — es el mismo azul que trae cualquier plantilla de Bootstrap sin personalizar.
- Ya hay intentos manuales de un tono cálido: `product.html` define `.price { color: #e67e22 }` (naranja) y usa clases `btn-custom-danger` (rojo) para los CTA de compra — es decir, **la intención de "fuego" ya está apareciendo de forma orgánica pero sin sistema**: cada plantilla define su propio color suelto en lugar de una paleta compartida.
- El navbar (`navbar.html`) tiene su propio bloque `<style>` inline, separado del resto.

Esto significa que el trabajo de diseño no es "inventar" un tema nuevo desde cero, sino **sistematizar y extender** lo que ya se insinuó en `product.html`.

### Paleta propuesta ("fuego")

| Token | Valor | Uso |
|---|---|---|
| `--flame-700` | `#C7360F` | Hover/estado activo de botones primarios, texto sobre fondo claro |
| `--flame-600` | `#E8491D` | Color primario — reemplaza `--bs-primary` (#0d6efd) |
| `--flame-500` | `#FF6B1A` | Gradientes, hover claro, badges "Nuevo" |
| `--ember-400` | `#F2A93B` | Acentos, ⭐ calificación, badge "Más vendido", precios en oferta |
| `--char-900` | `#241C18` | Navbar/footer oscuro, texto sobre fondo claro |
| `--char-050` | `#FBF4EE` | Fondo general cálido (reemplaza el blanco/gris frío de Bootstrap) |

Este esquema conserva verde para "éxito" (pago confirmado, aprobado) y rojo/ámbar como semántica de error/alerta — el fuego se usa como **marca**, no reemplaza los colores de estado, igual que Udemy no usa su morado para errores.

### Recomendaciones concretas

1. **Centralizar el color, no tocar `styles.css` a mano.** `styles.css` es un build de Bootstrap de 10 800 líneas — editarlo directamente hará que cualquier futura regeneración pierda los cambios. Mejor: un archivo pequeño nuevo (p. ej. `static/css/theme.css`) cargado *después* de `styles.css` en `base.html`, que solo redefina las variables `--bs-primary`, `--bs-primary-rgb`, `--bs-link-color` y las clases `.btn-primary`, `.bg-primary`, `.text-primary` con la paleta de arriba. Esto centraliza en un solo lugar lo que hoy está disperso como `#e67e22` suelto en `product.html` y estilos inline en `navbar.html`.
2. **Curriculum como acordeón**, reemplazando los tres bloques fijos de `product_detail.html` — visualmente esto también ayuda a mostrar progreso por sección más adelante.
3. **Card de curso estilo Udemy**: miniatura, título, instructor, ⭐ rating + nº de reseñas, precio con tachado, badge opcional ("Nuevo"/"Más vendido") en `--ember-400`. Hoy la card de `index.html` no muestra instructor ni rating porque esos datos no existen aún en el modelo.
4. **Barra de progreso** en `--flame-500` sobre fondo `--char-900`, para "Mis cursos" una vez exista tracking de progreso.
5. **Sidebar de compra "sticky"** en la ficha de curso (precio + botón comprar + resumen del temario), que se mantiene visible al hacer scroll — patrón central de la ficha de Udemy.
6. **Franja de categorías** con pills redondeadas en el home (Coursera usa esto para navegar por área temática antes de buscar por texto).
7. **Fondo general cálido** (`--char-050`) en vez del gris/blanco frío por defecto de Bootstrap, para que el naranja/rojo no se vea "pegado" sobre un fondo neutro sin relación.

### Mockup visual

Se adjunta un artifact con la paleta aplicada a los componentes reales del proyecto (botón, badge, card de curso, barra de progreso, navbar) para verlo antes de decidir.

---

## 3. Priorización sugerida

### Quick wins (alto impacto, bajo esfuerzo)
- Sistema de calificación por estrellas (agregar `rating` a `Comment` o modelo nuevo `Review`) + promedio visible en card y ficha.
- Recuperación de contraseña por email (Django trae esto casi listo con `PasswordResetView`).
- Paginación en `index()` y `search()`.
- Centralizar la paleta de color (paso 1 de la sección de diseño).
- Quitar o cumplir la promesa de "Certificado" en `search.html`.

### Mediano plazo
- Reproductor embebido de video/PDF en vez de descarga directa.
- Modelo de progreso del estudiante (qué `Clase` completó, ligado a `usuarios_pagados`/inscripción).
- "Lo que aprenderás" + requisitos + duración en la ficha de curso.
- Dashboard de instructor con inscritos e ingresos por curso.
- Email de confirmación de compra y de aprobación como instructor.

### Largo plazo / diferenciación
- Certificados de finalización (depende de tener progreso primero).
- Quizzes/evaluaciones.
- Cupones de descuento y bundles de cursos.
- Recomendaciones ("estudiantes también compraron").

---

## Nota metodológica

Reporte de solo lectura: se inspeccionaron modelos, vistas, formularios y plantillas de `store`, `cart` y `payment`, además del CSS base (`static/css/styles.css`) y el reporte funcional previo del 2026-08-04 para no duplicar hallazgos ya conocidos. No se ejecutó el proyecto en navegador. Los valores de color propuestos son un punto de partida razonable, no una decisión final — conviene validarlos con el artifact adjunto antes de implementarlos.
