# Este archivo puede estar vacío
# solo sirve para marcar el paquete
from .models import sa_db, Oposicion, User, Visita, VisitaGlobal, Favorita, Suscripcion
from .migrar_datos import inicializar_y_migrar 