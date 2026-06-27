import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import requests
from datetime import datetime, date
from collections import defaultdict
from tkcalendar import DateEntry
from dotenv import load_dotenv
from supabase import create_client

import unicodedata

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def normalizar(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()

from werkzeug.security import generate_password_hash, check_password_hash

_db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

_usuario_actual = {"id": None, "username": None}

SESSION_FILE = os.path.join(os.path.dirname(__file__), ".sesion_local.json")

def guardar_sesion_local():
    import json
    with open(SESSION_FILE, "w") as f:
        json.dump(_usuario_actual, f)

def cargar_sesion_local():
    import json
    if not os.path.exists(SESSION_FILE):
        return False
    try:
        with open(SESSION_FILE) as f:
            data = json.load(f)
        if not data.get("id"):
            return False
        # Verificar que el usuario todavía existe
        res = _db.table("usuarios").select("id, username").eq("id", data["id"]).execute()
        if not res.data:
            return False
        _usuario_actual["id"] = data["id"]
        _usuario_actual["username"] = data["username"]
        return True
    except Exception:
        return False

def borrar_sesion_local():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

COLORES = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3e",
    "surface2": "#313148",
    "accent_green": "#4ade80",
    "accent_red": "#f87171",
    "accent_blue": "#60a5fa",
    "accent_yellow": "#fbbf24",
    "text": "#e2e8f0",
    "text_muted": "#94a3b8",
    "border": "#3f3f5a",
}


def cargar_datos():
    res = _db.table("transacciones").select("*").eq("user_id", _usuario_actual["id"]).order("fecha", desc=True).execute()
    return res.data


def insertar_transaccion(t):
    payload = {
        "tipo":        t["tipo"],
        "monto":       float(t["monto"]),
        "fecha":       t["fecha"],
        "categoria":   t.get("categoria", ""),
        "descripcion": t.get("descripcion", ""),
        "moneda":      t.get("moneda", "ARS"),
        "user_id":     _usuario_actual["id"],
    }
    res = _db.table("transacciones").insert(payload).execute()
    return res.data[0]

SIM_MONEDA = {"ARS": "$", "USD": "USD ", "EUR": "€"}

def fmt_mon(monto, moneda="ARS"):
    sym = SIM_MONEDA.get(moneda, "$")
    return f"{sym}{monto:,.2f}"


def eliminar_transaccion(tid):
    _db.table("transacciones").delete().eq("id", tid).eq("user_id", _usuario_actual["id"]).execute()


class FinanzasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de Finanzas")
        self.root.geometry("1100x720")
        self.root.configure(bg=COLORES["bg"])
        self.root.resizable(True, True)

        self.datos = cargar_datos()
        self.filtro_mes = tk.StringVar(value="Todos")
        self.filtro_anio = tk.StringVar(value=str(date.today().year))
        self.filtro_tipo = tk.StringVar(value="Todos")
        self.filtro_cat = tk.StringVar(value="Todas")
        self.filtro_moneda = tk.StringVar(value="Todas")
        self.moneda_form = tk.StringVar(value="ARS")
        self.moneda_consol = "ARS"
        self.cotiz = {"USD": None, "EUR": None}

        self._configurar_estilos()
        self._construir_ui()
        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()
        threading.Thread(target=self._cargar_cotizaciones, daemon=True).start()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=COLORES["bg"], foreground=COLORES["text"],
                        fieldbackground=COLORES["surface2"], borderwidth=0)
        style.configure("TFrame", background=COLORES["bg"])
        style.configure("Surface.TFrame", background=COLORES["surface"])
        style.configure("TLabel", background=COLORES["bg"], foreground=COLORES["text"],
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=COLORES["bg"], foreground=COLORES["text"],
                        font=("Segoe UI", 18, "bold"))
        style.configure("Card.TLabel", background=COLORES["surface"], foreground=COLORES["text"],
                        font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=COLORES["surface"],
                        foreground=COLORES["text_muted"], font=("Segoe UI", 9))
        style.configure("CardValue.TLabel", background=COLORES["surface"],
                        font=("Segoe UI", 20, "bold"))
        style.configure("Green.CardValue.TLabel", foreground=COLORES["accent_green"])
        style.configure("Red.CardValue.TLabel", foreground=COLORES["accent_red"])
        style.configure("Blue.CardValue.TLabel", foreground=COLORES["accent_blue"])

        style.configure("TButton", background=COLORES["accent_blue"], foreground="white",
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(12, 8))
        style.map("TButton", background=[("active", "#3b82f6"), ("pressed", "#2563eb")])

        style.configure("Danger.TButton", background=COLORES["accent_red"], foreground="white",
                        font=("Segoe UI", 9, "bold"), borderwidth=0, padding=(8, 5))
        style.map("Danger.TButton", background=[("active", "#ef4444")])

        style.configure("TCombobox", fieldbackground=COLORES["surface2"],
                        background=COLORES["surface2"], foreground=COLORES["text"],
                        arrowcolor=COLORES["text_muted"], borderwidth=0)
        style.map("TCombobox", fieldbackground=[("readonly", COLORES["surface2"])],
                  foreground=[("readonly", COLORES["text"])])

        style.configure("Treeview", background=COLORES["surface2"], foreground=COLORES["text"],
                        fieldbackground=COLORES["surface2"], rowheight=32,
                        font=("Segoe UI", 10), borderwidth=0)
        style.configure("Treeview.Heading", background=COLORES["surface"],
                        foreground=COLORES["text_muted"], font=("Segoe UI", 10, "bold"),
                        borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", "#3b4a6b")],
                  foreground=[("selected", COLORES["text"])])
        style.map("Treeview.Heading", background=[("active", COLORES["border"])])

        style.configure("TSeparator", background=COLORES["border"])

    def _construir_ui(self):
        # Header
        header = tk.Frame(self.root, bg=COLORES["surface"], height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        tk.Label(header, text="💰 Control de Finanzas", bg=COLORES["surface"],
                 fg=COLORES["text"], font=("Segoe UI", 16, "bold")).pack(side="left", padx=20, pady=15)

        # Botón cerrar sesión (derecha)
        btn_logout = tk.Button(header, text="Cerrar sesión", bg=COLORES["surface2"],
                               fg=COLORES["text_muted"], font=("Segoe UI", 9), bd=0,
                               relief="flat", padx=10, pady=5, cursor="hand2",
                               command=self._cerrar_sesion)
        btn_logout.pack(side="right", padx=12)

        tk.Label(header, text=f"Hola, {_usuario_actual['username']}", bg=COLORES["surface"],
                 fg=COLORES["text"], font=("Segoe UI", 13, "bold")).pack(side="right", padx=(20, 4))

        # Main layout
        main = tk.Frame(self.root, bg=COLORES["bg"])
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # Left panel: form
        left = tk.Frame(main, bg=COLORES["surface"], bd=0, relief="flat")
        left.pack(side="left", fill="y", padx=(0, 10), ipadx=10, ipady=10)

        self._construir_formulario(left)

        # Right panel: filters + table + balances
        right = tk.Frame(main, bg=COLORES["bg"])
        right.pack(side="left", fill="both", expand=True)

        self._construir_tarjetas_balance(right)
        self._construir_consolidado(right)
        self._construir_filtros(right)
        self._construir_tabla(right)

    def _construir_formulario(self, parent):
        tk.Label(parent, text="Nueva Transacción", bg=COLORES["surface"],
                 fg=COLORES["text"], font=("Segoe UI", 13, "bold")).pack(pady=(15, 5), padx=15, anchor="w")

        sep = tk.Frame(parent, bg=COLORES["border"], height=1)
        sep.pack(fill="x", padx=15, pady=5)

        form = tk.Frame(parent, bg=COLORES["surface"])
        form.pack(fill="x", padx=15, pady=5)

        def label(text):
            tk.Label(form, text=text, bg=COLORES["surface"], fg=COLORES["text_muted"],
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))

        # Tipo
        label("Tipo")
        self.tipo_var = tk.StringVar(value="Gasto")
        tipo_frame = tk.Frame(form, bg=COLORES["surface"])
        tipo_frame.pack(fill="x")
        self.btn_gasto = tk.Button(tipo_frame, text="Gasto", bg=COLORES["accent_red"],
                                   fg="white", font=("Segoe UI", 10, "bold"), bd=0,
                                   relief="flat", padx=15, pady=6, cursor="hand2",
                                   command=lambda: self._set_tipo("Gasto"))
        self.btn_gasto.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.btn_ingreso = tk.Button(tipo_frame, text="Ingreso", bg=COLORES["surface2"],
                                     fg=COLORES["text_muted"], font=("Segoe UI", 10, "bold"), bd=0,
                                     relief="flat", padx=15, pady=6, cursor="hand2",
                                     command=lambda: self._set_tipo("Ingreso"))
        self.btn_ingreso.pack(side="left", fill="x", expand=True, padx=(3, 0))

        # Moneda
        label("Moneda")
        mon_frame = tk.Frame(form, bg=COLORES["surface"])
        mon_frame.pack(fill="x")
        self.btn_mon = {}
        for m, txt in [("ARS", "$ ARS"), ("USD", "USD"), ("EUR", "€ EUR")]:
            b = tk.Button(mon_frame, text=txt,
                          bg=COLORES["accent_blue"] if m == "ARS" else COLORES["surface2"],
                          fg="white" if m == "ARS" else COLORES["text_muted"],
                          font=("Segoe UI", 9, "bold"), bd=0, relief="flat",
                          padx=8, pady=5, cursor="hand2",
                          command=lambda x=m: self._set_moneda(x))
            b.pack(side="left", fill="x", expand=True, padx=1)
            self.btn_mon[m] = b

        # Monto
        label("Monto")
        self.monto_var = tk.StringVar()
        monto_entry = tk.Entry(form, textvariable=self.monto_var, bg=COLORES["surface2"],
                               fg=COLORES["text"], font=("Segoe UI", 11), bd=0,
                               insertbackground=COLORES["text"], relief="flat")
        monto_entry.pack(fill="x", ipady=7)
        monto_frame = tk.Frame(form, bg=COLORES["accent_blue"], height=2)
        monto_frame.pack(fill="x")

        # Fecha
        label("Fecha")
        self.fecha_entry = DateEntry(
            form,
            width=20,
            date_pattern="dd/mm/yyyy",
            locale="es_ES",
            background=COLORES["accent_blue"],
            foreground="white",
            selectbackground=COLORES["accent_blue"],
            selectforeground="white",
            normalbackground=COLORES["surface2"],
            normalforeground=COLORES["text"],
            weekendbackground=COLORES["surface2"],
            weekendforeground=COLORES["accent_yellow"],
            headersbackground=COLORES["surface"],
            headersforeground=COLORES["text_muted"],
            othermonthbackground=COLORES["bg"],
            othermonthforeground=COLORES["border"],
            font=("Segoe UI", 11),
        )
        self.fecha_entry.set_date(date.today())
        self.fecha_entry.pack(fill="x", ipady=5)

        # Categoría
        label("Categoría")
        self.cat_var = tk.StringVar()
        cat_entry = tk.Entry(form, textvariable=self.cat_var, bg=COLORES["surface2"],
                             fg=COLORES["text"], font=("Segoe UI", 11), bd=0,
                             insertbackground=COLORES["text"], relief="flat")
        cat_entry.pack(fill="x", ipady=7)
        tk.Frame(form, bg=COLORES["accent_blue"], height=2).pack(fill="x")

        # Descripción
        label("Descripción")
        self.desc_var = tk.StringVar()
        desc_entry = tk.Entry(form, textvariable=self.desc_var, bg=COLORES["surface2"],
                              fg=COLORES["text"], font=("Segoe UI", 11), bd=0,
                              insertbackground=COLORES["text"], relief="flat")
        desc_entry.pack(fill="x", ipady=7)
        tk.Frame(form, bg=COLORES["accent_blue"], height=2).pack(fill="x")

        # Botón agregar
        tk.Frame(form, bg=COLORES["surface"], height=15).pack()
        btn_agregar = tk.Button(form, text="+ Agregar Transacción",
                                bg=COLORES["accent_blue"], fg="white",
                                font=("Segoe UI", 11, "bold"), bd=0, relief="flat",
                                pady=10, cursor="hand2", command=self._agregar_transaccion)
        btn_agregar.pack(fill="x")
        btn_agregar.bind("<Enter>", lambda e: btn_agregar.config(bg="#3b82f6"))
        btn_agregar.bind("<Leave>", lambda e: btn_agregar.config(bg=COLORES["accent_blue"]))

        # Info
        tk.Frame(parent, bg=COLORES["surface"], height=10).pack()
        self.info_label = tk.Label(parent, text="", bg=COLORES["surface"],
                                   fg=COLORES["accent_green"], font=("Segoe UI", 9),
                                   wraplength=220)
        self.info_label.pack(padx=15, anchor="w")

    def _set_tipo(self, tipo):
        self.tipo_var.set(tipo)
        if tipo == "Gasto":
            self.btn_gasto.config(bg=COLORES["accent_red"], fg="white")
            self.btn_ingreso.config(bg=COLORES["surface2"], fg=COLORES["text_muted"])
        else:
            self.btn_ingreso.config(bg=COLORES["accent_green"], fg="#1e1e2e")
            self.btn_gasto.config(bg=COLORES["surface2"], fg=COLORES["text_muted"])

    def _set_moneda(self, moneda):
        self.moneda_form.set(moneda)
        for m, btn in self.btn_mon.items():
            btn.config(bg=COLORES["accent_blue"] if m == moneda else COLORES["surface2"],
                       fg="white" if m == moneda else COLORES["text_muted"])

    def _construir_tarjetas_balance(self, parent):
        pass  # reemplazado por consolidado

    def _tarjeta(self, parent, titulo, valor, color):
        card = tk.Frame(parent, bg=COLORES["surface"], bd=0, relief="flat")
        card.pack(side="left", fill="both", expand=True, padx=4, ipady=12, ipadx=10)
        tk.Label(card, text=titulo.upper(), bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        val_label = tk.Label(card, text=valor, bg=COLORES["surface"],
                             fg=color, font=("Segoe UI", 22, "bold"))
        val_label.pack(anchor="w", padx=12, pady=(0, 10))
        return val_label

    def _tarjeta_mini(self, parent, titulo, valor, color):
        card = tk.Frame(parent, bg=COLORES["surface"], bd=0, relief="flat")
        card.pack(side="left", fill="both", expand=True, padx=4, ipady=4, ipadx=8)
        tk.Label(card, text=titulo.upper(), bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(6, 1))
        val_label = tk.Label(card, text=valor, bg=COLORES["surface"],
                             fg=color, font=("Segoe UI", 13, "bold"))
        val_label.pack(anchor="w", padx=10, pady=(0, 6))
        return val_label

    def _construir_filtros(self, parent):
        frame = tk.Frame(parent, bg=COLORES["surface"])
        frame.pack(fill="x", pady=(0, 10), ipady=6)

        tk.Label(frame, text="Filtros:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=(12, 8), pady=8)

        # Mes
        tk.Label(frame, text="Mes:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        mes_combo = ttk.Combobox(frame, textvariable=self.filtro_mes,
                                  values=["Todos"] + MESES, state="readonly",
                                  width=10, font=("Segoe UI", 9))
        mes_combo.pack(side="left", padx=(0, 10))
        mes_combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Año
        anios = [str(y) for y in range(2020, date.today().year + 2)]
        tk.Label(frame, text="Año:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        anio_combo = ttk.Combobox(frame, textvariable=self.filtro_anio,
                                   values=anios, state="readonly",
                                   width=7, font=("Segoe UI", 9))
        anio_combo.pack(side="left", padx=(0, 10))
        anio_combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Tipo
        tk.Label(frame, text="Tipo:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        tipo_combo = ttk.Combobox(frame, textvariable=self.filtro_tipo,
                                   values=["Todos", "Gasto", "Ingreso"], state="readonly",
                                   width=8, font=("Segoe UI", 9))
        tipo_combo.pack(side="left", padx=(0, 10))
        tipo_combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Moneda
        tk.Label(frame, text="Moneda:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        mon_combo = ttk.Combobox(frame, textvariable=self.filtro_moneda,
                                  values=["Todas", "ARS", "USD", "EUR"], state="readonly",
                                  width=7, font=("Segoe UI", 9))
        mon_combo.pack(side="left", padx=(0, 10))
        mon_combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Categoría
        tk.Label(frame, text="Categoría:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.cat_filtro_combo = ttk.Combobox(frame, textvariable=self.filtro_cat,
                                              values=["Todas"], state="readonly",
                                              width=13, font=("Segoe UI", 9))
        self.cat_filtro_combo.pack(side="left", padx=(0, 10))
        self.cat_filtro_combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Botón limpiar filtros
        tk.Button(frame, text="Mostrar todos", bg=COLORES["surface2"], fg=COLORES["text_muted"],
                  font=("Segoe UI", 9), bd=0, relief="flat", padx=8, pady=4, cursor="hand2",
                  command=self._limpiar_filtros).pack(side="left", padx=4)

    def _construir_tabla(self, parent):
        frame = tk.Frame(parent, bg=COLORES["surface"])
        frame.pack(fill="both", expand=True)

        # Barra de acción
        action_bar = tk.Frame(frame, bg=COLORES["surface"])
        action_bar.pack(fill="x", padx=12, pady=(10, 5))

        self.count_label = tk.Label(action_bar, text="0 transacciones",
                                     bg=COLORES["surface"], fg=COLORES["text_muted"],
                                     font=("Segoe UI", 9))
        self.count_label.pack(side="left")

        tk.Button(action_bar, text="Eliminar",
                  bg=COLORES["accent_red"], fg="white",
                  font=("Segoe UI", 9, "bold"), bd=0, relief="flat",
                  padx=10, pady=4, cursor="hand2",
                  command=self._eliminar_seleccionado).pack(side="right")

        tk.Button(action_bar, text="✏️  Editar",
                  bg=COLORES["accent_blue"], fg="white",
                  font=("Segoe UI", 9, "bold"), bd=0, relief="flat",
                  padx=10, pady=4, cursor="hand2",
                  command=self._editar_seleccionado).pack(side="right", padx=(0, 6))

        # Tabla
        cols = ("Fecha", "Tipo", "Moneda", "Categoría", "Descripción", "Monto")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                  selectmode="browse")

        self.tree.heading("Fecha",       text="Fecha")
        self.tree.heading("Tipo",        text="Tipo")
        self.tree.heading("Moneda",      text="Moneda")
        self.tree.heading("Categoría",   text="Categoría")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.heading("Monto",       text="Monto")

        self.tree.column("Fecha",       width=90,  anchor="center")
        self.tree.column("Tipo",        width=75,  anchor="center")
        self.tree.column("Moneda",      width=60,  anchor="center")
        self.tree.column("Categoría",   width=120, anchor="center")
        self.tree.column("Descripción", width=220)
        self.tree.column("Monto",       width=120, anchor="e")

        # Scrollbar
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        sb.pack(side="right", fill="y", pady=(0, 12), padx=(0, 12))

        # Tags de color por tipo
        self.tree.tag_configure("ingreso", foreground=COLORES["accent_green"])
        self.tree.tag_configure("gasto", foreground=COLORES["accent_red"])

    def _agregar_transaccion(self):
        monto_str = self.monto_var.get().strip().replace(",", ".")
        cat = self.cat_var.get()
        desc = self.desc_var.get().strip()
        tipo = self.tipo_var.get()

        if not monto_str:
            messagebox.showerror("Error", "Ingresá un monto.")
            return
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número positivo.")
            return

        fecha = self.fecha_entry.get_date()

        transaccion = {
            "tipo": tipo,
            "monto": monto,
            "fecha": fecha.isoformat(),
            "categoria": cat,
            "descripcion": desc,
            "moneda": self.moneda_form.get(),
        }

        guardado = insertar_transaccion(transaccion)
        self.datos.insert(0, guardado)

        self.monto_var.set("")
        self.desc_var.set("")
        self.fecha_entry.set_date(date.today())

        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()

        mon = self.moneda_form.get()
        signo = "+" if tipo == "Ingreso" else "-"
        self.info_label.config(
            text=f"✓ {tipo} de {signo}{fmt_mon(monto, mon)} agregado.",
            fg=COLORES["accent_green"] if tipo == "Ingreso" else COLORES["accent_red"]
        )
        self.root.after(3000, lambda: self.info_label.config(text=""))

    def _datos_filtrados(self):
        mes_sel = self.filtro_mes.get()
        anio_sel = self.filtro_anio.get()
        tipo_sel = self.filtro_tipo.get()
        cat_sel = self.filtro_cat.get()

        mon_sel = self.filtro_moneda.get()
        resultado = []
        for t in self.datos:
            f = date.fromisoformat(t["fecha"])
            if mes_sel != "Todos" and MESES[f.month - 1] != mes_sel:
                continue
            if anio_sel and str(f.year) != anio_sel:
                continue
            if tipo_sel != "Todos" and t["tipo"] != tipo_sel:
                continue
            if mon_sel != "Todas" and (t.get("moneda") or "ARS") != mon_sel:
                continue
            if cat_sel != "Todas" and normalizar(t.get("categoria", "")) != normalizar(cat_sel):
                continue
            resultado.append(t)

        resultado.sort(key=lambda x: x["fecha"], reverse=True)
        return resultado

    def _datos_filtrados_sin_moneda(self):
        mes_sel  = self.filtro_mes.get()
        anio_sel = self.filtro_anio.get()
        tipo_sel = self.filtro_tipo.get()
        cat_sel  = self.filtro_cat.get()
        resultado = []
        for t in self.datos:
            f = date.fromisoformat(t["fecha"])
            if mes_sel != "Todos" and MESES[f.month - 1] != mes_sel: continue
            if anio_sel and str(f.year) != anio_sel: continue
            if tipo_sel != "Todos" and t["tipo"] != tipo_sel: continue
            if cat_sel != "Todas" and normalizar(t.get("categoria", "")) != normalizar(cat_sel): continue
            resultado.append(t)
        return resultado

    def _actualizar_categorias_filtro(self):
        seen, cats = set(), []
        for t in self.datos:
            c = t.get("categoria", "")
            if c and normalizar(c) not in seen:
                seen.add(normalizar(c))
                cats.append(c)
        cats = sorted(cats, key=normalizar)
        self.cat_filtro_combo.config(values=["Todas"] + cats)
        if self.filtro_cat.get() not in ["Todas"] + cats:
            self.filtro_cat.set("Todas")

    def _actualizar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtrados = self._datos_filtrados()
        self.count_label.config(text=f"{len(filtrados)} transacciones")

        for t in filtrados:
            f = date.fromisoformat(t["fecha"])
            fecha_fmt = f.strftime("%d/%m/%Y")
            signo = "+" if t["tipo"] == "Ingreso" else "-"
            mon = t.get("moneda") or "ARS"
            monto_fmt = f"{signo}{fmt_mon(t['monto'], mon)}"
            tag = "ingreso" if t["tipo"] == "Ingreso" else "gasto"
            self.tree.insert("", "end",
                             values=(fecha_fmt, t["tipo"], mon, t["categoria"],
                                     t["descripcion"], monto_fmt),
                             tags=(tag,),
                             iid=str(t["id"]))

    def _actualizar_balances(self):
        self._actualizar_consolidado()

    def _construir_consolidado(self, parent):
        frame = tk.Frame(parent, bg=COLORES["surface"])
        frame.pack(fill="x", pady=(0, 8), ipady=8)

        top = tk.Frame(frame, bg=COLORES["surface"])
        top.pack(fill="x", padx=12, pady=(8, 6))

        tk.Label(top, text="🔄  Total consolidado en:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9, "bold")).pack(side="left")

        self.btn_consol = {}
        btn_frame = tk.Frame(top, bg=COLORES["surface"])
        btn_frame.pack(side="right")
        for m, txt in [("ARS", "$ ARS"), ("USD", "USD"), ("EUR", "€ EUR")]:
            b = tk.Button(btn_frame, text=txt,
                          bg=COLORES["accent_blue"] if m == "ARS" else COLORES["surface2"],
                          fg="white" if m == "ARS" else COLORES["text_muted"],
                          font=("Segoe UI", 9, "bold"), bd=0, relief="flat",
                          padx=10, pady=4, cursor="hand2",
                          command=lambda x=m: self._set_consolidado(x))
            b.pack(side="left", padx=2)
            self.btn_consol[m] = b

        cards = tk.Frame(frame, bg=COLORES["surface"])
        cards.pack(fill="x", padx=12)
        self.cons_ing = self._tarjeta_mini(cards, "Ingresos totales", "—", COLORES["accent_green"])
        self.cons_gas = self._tarjeta_mini(cards, "Gastos totales",   "—", COLORES["accent_red"])
        self.cons_net = self._tarjeta_mini(cards, "Balance total",    "—", COLORES["accent_blue"])

        self.cons_nota = tk.Label(frame, text="Cargando cotizaciones...",
                                  bg=COLORES["surface"], fg=COLORES["text_muted"],
                                  font=("Segoe UI", 8))
        self.cons_nota.pack(anchor="e", padx=14, pady=(2, 4))

    def _set_consolidado(self, moneda):
        self.moneda_consol = moneda
        for m, btn in self.btn_consol.items():
            btn.config(bg=COLORES["accent_blue"] if m == moneda else COLORES["surface2"],
                       fg="white" if m == moneda else COLORES["text_muted"])
        self._actualizar_consolidado()

    def _cargar_cotizaciones(self):
        try:
            r = requests.get("https://api.bluelytics.com.ar/v2/latest", timeout=6)
            data = r.json()
            self.cotiz["USD"] = round(data["oficial"]["value_sell"], 2)
            self.cotiz["EUR"] = round(data["oficial_euro"]["value_sell"], 2)
            self.root.after(0, self._actualizar_consolidado)
            self.root.after(0, lambda: self.cons_nota.config(
                text=f"Tipo de cambio oficial BNA  |  USD ${self.cotiz['USD']:,.2f}  |  EUR ${self.cotiz['EUR']:,.2f}"))
        except Exception:
            self.root.after(0, lambda: self.cons_nota.config(text="Sin conexión para cotizaciones"))

    def _to_ars(self, monto, moneda):
        if moneda == "ARS": return monto
        if moneda == "USD": return monto * self.cotiz["USD"] if self.cotiz["USD"] else None
        if moneda == "EUR": return monto * self.cotiz["EUR"] if self.cotiz["EUR"] else None
        return monto

    def _from_ars(self, ars, moneda):
        if moneda == "ARS": return ars
        if moneda == "USD": return ars / self.cotiz["USD"] if self.cotiz["USD"] else None
        if moneda == "EUR": return ars / self.cotiz["EUR"] if self.cotiz["EUR"] else None
        return ars

    def _actualizar_consolidado(self):
        filtrados = self._datos_filtrados_sin_moneda()
        m = self.moneda_consol

        if m != "ARS" and (not self.cotiz["USD"] or not self.cotiz["EUR"]):
            for lbl in [self.cons_ing, self.cons_gas, self.cons_net]:
                lbl.config(text="Sin cotización", fg=COLORES["text_muted"])
            return

        ing_ars = sum(self._to_ars(t["monto"], t.get("moneda") or "ARS") or 0
                      for t in filtrados if t["tipo"] == "Ingreso")
        gas_ars = sum(self._to_ars(t["monto"], t.get("moneda") or "ARS") or 0
                      for t in filtrados if t["tipo"] == "Gasto")

        ing = self._from_ars(ing_ars, m)
        gas = self._from_ars(gas_ars, m)
        net = ing - gas

        self.cons_ing.config(text=f"+{fmt_mon(ing, m)}", fg=COLORES["accent_green"])
        self.cons_gas.config(text=f"-{fmt_mon(gas, m)}", fg=COLORES["accent_red"])
        color = COLORES["accent_green"] if net >= 0 else COLORES["accent_red"]
        self.cons_net.config(text=f"{'+'if net>=0 else '-'}{fmt_mon(abs(net), m)}", fg=color)

    def _cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión", "¿Querés cerrar sesión?"):
            borrar_sesion_local()
            self.root.destroy()

    def _aplicar_filtros(self):
        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()

    def _limpiar_filtros(self):
        self.filtro_mes.set("Todos")
        self.filtro_anio.set(str(date.today().year))
        self.filtro_tipo.set("Todos")
        self.filtro_moneda.set("Todas")
        self.filtro_cat.set("Todas")
        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()

    def _editar_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleccioná una transacción para editar.")
            return
        iid = int(sel[0])
        tx = next((t for t in self.datos if t["id"] == iid), None)
        if not tx:
            return

        win = tk.Toplevel(self.root)
        win.title("Editar transacción")
        win.configure(bg=COLORES["bg"])
        win.geometry("360x480")
        win.resizable(False, False)
        win.grab_set()

        frame = tk.Frame(win, bg=COLORES["surface"], padx=20, pady=20)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(frame, text="Editar transacción", bg=COLORES["surface"],
                 fg=COLORES["text"], font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))

        def campo(label):
            tk.Label(frame, text=label, bg=COLORES["surface"], fg=COLORES["text_muted"],
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 2))

        # Tipo
        tipo_var = tk.StringVar(value=tx["tipo"])
        tipo_frame = tk.Frame(frame, bg=COLORES["surface"])
        tipo_frame.pack(fill="x", pady=(0, 4))
        btn_g = tk.Button(tipo_frame, text="Gasto",   bd=0, relief="flat", padx=12, pady=6,
                          font=("Segoe UI", 10, "bold"), cursor="hand2")
        btn_i = tk.Button(tipo_frame, text="Ingreso", bd=0, relief="flat", padx=12, pady=6,
                          font=("Segoe UI", 10, "bold"), cursor="hand2")
        def set_tipo_edit(t):
            tipo_var.set(t)
            btn_g.config(bg=COLORES["accent_red"]  if t=="Gasto"   else COLORES["surface2"],
                         fg="white"                if t=="Gasto"   else COLORES["text_muted"])
            btn_i.config(bg=COLORES["accent_green"] if t=="Ingreso" else COLORES["surface2"],
                         fg="white"                if t=="Ingreso" else COLORES["text_muted"])
        btn_g.config(command=lambda: set_tipo_edit("Gasto"))
        btn_i.config(command=lambda: set_tipo_edit("Ingreso"))
        btn_g.pack(side="left", padx=(0, 4))
        btn_i.pack(side="left")
        set_tipo_edit(tx["tipo"])

        # Moneda
        mon_var = tk.StringVar(value=tx.get("moneda", "ARS"))
        mon_frame = tk.Frame(frame, bg=COLORES["surface"])
        mon_frame.pack(fill="x", pady=(6, 0))
        mon_btns = {}
        def set_mon_edit(m):
            mon_var.set(m)
            for k, b in mon_btns.items():
                b.config(bg=COLORES["accent_blue"] if k==m else COLORES["surface2"],
                         fg="white" if k==m else COLORES["text_muted"])
        for m, txt in [("ARS","$ ARS"),("USD","USD"),("EUR","€ EUR")]:
            b = tk.Button(mon_frame, text=txt, bd=0, relief="flat", padx=10, pady=5,
                          font=("Segoe UI", 9, "bold"), cursor="hand2",
                          command=lambda x=m: set_mon_edit(x))
            b.pack(side="left", padx=(0, 4))
            mon_btns[m] = b
        set_mon_edit(tx.get("moneda", "ARS"))

        campo("MONTO")
        monto_var = tk.StringVar(value=str(tx["monto"]))
        tk.Entry(frame, textvariable=monto_var, bg=COLORES["surface2"], fg=COLORES["text"],
                 font=("Segoe UI", 11), bd=0, relief="flat", insertbackground=COLORES["text"]).pack(fill="x", ipady=7)

        campo("FECHA")
        fecha_var = tk.StringVar(value=tx["fecha"])
        DateEntry(frame, textvariable=fecha_var, date_pattern="yyyy-mm-dd",
                  background=COLORES["surface2"], foreground=COLORES["text"],
                  font=("Segoe UI", 10)).pack(fill="x", ipady=4)

        campo("CATEGORÍA")
        cat_var = tk.StringVar(value=tx.get("categoria", ""))
        tk.Entry(frame, textvariable=cat_var, bg=COLORES["surface2"], fg=COLORES["text"],
                 font=("Segoe UI", 11), bd=0, relief="flat", insertbackground=COLORES["text"]).pack(fill="x", ipady=7)

        campo("DESCRIPCIÓN")
        desc_var = tk.StringVar(value=tx.get("descripcion", ""))
        tk.Entry(frame, textvariable=desc_var, bg=COLORES["surface2"], fg=COLORES["text"],
                 font=("Segoe UI", 11), bd=0, relief="flat", insertbackground=COLORES["text"]).pack(fill="x", ipady=7)

        error_lbl = tk.Label(frame, text="", bg=COLORES["surface"], fg=COLORES["accent_red"],
                             font=("Segoe UI", 9))
        error_lbl.pack(pady=(6, 0))

        def confirmar():
            try:
                monto = float(monto_var.get().replace(",", "."))
                if monto <= 0:
                    raise ValueError()
            except ValueError:
                error_lbl.config(text="Ingresá un monto válido")
                return
            fecha = fecha_var.get().strip()
            if not fecha:
                error_lbl.config(text="Elegí una fecha")
                return
            payload = {
                "tipo": tipo_var.get(), "monto": monto, "fecha": fecha,
                "categoria": cat_var.get().strip(), "descripcion": desc_var.get().strip(),
                "moneda": mon_var.get(),
            }
            try:
                db.table("transacciones").update(payload).eq("id", iid).eq("user_id", _usuario_actual["id"]).execute()
                for k, v in payload.items():
                    tx[k] = v
                self._actualizar_categorias_filtro()
                self._actualizar_tabla()
                self._actualizar_balances()
                win.destroy()
            except Exception as e:
                error_lbl.config(text=f"Error: {e}")

        tk.Button(frame, text="Guardar cambios", bg=COLORES["accent_blue"], fg="white",
                  bd=0, relief="flat", font=("Segoe UI", 11, "bold"), pady=10,
                  cursor="hand2", command=confirmar).pack(fill="x", pady=(12, 0))

    def _eliminar_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleccioná una transacción para eliminar.")
            return
        iid = int(sel[0])
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta transacción?"):
            return
        eliminar_transaccion(iid)
        self.datos = [t for t in self.datos if t["id"] != iid]
        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Finanzas — Ingresar")
        self.root.geometry("380x480")
        self.root.configure(bg=COLORES["bg"])
        self.root.resizable(False, False)
        self.autenticado = False
        self._construir_ui()

    def _construir_ui(self):
        marco = tk.Frame(self.root, bg=COLORES["surface"], padx=30, pady=30)
        marco.place(relx=0.5, rely=0.5, anchor="center", width=340)

        tk.Label(marco, text="💰", bg=COLORES["surface"], font=("Segoe UI", 36)).pack()
        tk.Label(marco, text="Control de Finanzas", bg=COLORES["surface"],
                 fg=COLORES["text"], font=("Segoe UI", 15, "bold")).pack(pady=(4, 2))
        tk.Label(marco, text="Ingresá o creá tu cuenta", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 10)).pack(pady=(0, 16))

        # Tabs
        tab_frame = tk.Frame(marco, bg=COLORES["surface2"])
        tab_frame.pack(fill="x", pady=(0, 16))
        self.modo = tk.StringVar(value="login")
        self.btn_login = tk.Button(tab_frame, text="Ingresar", bg=COLORES["accent_blue"],
                                   fg="white", bd=0, relief="flat", font=("Segoe UI", 10, "bold"),
                                   pady=7, cursor="hand2", command=lambda: self._set_modo("login"))
        self.btn_login.pack(side="left", fill="x", expand=True)
        self.btn_reg = tk.Button(tab_frame, text="Registrarse", bg=COLORES["surface2"],
                                 fg=COLORES["text_muted"], bd=0, relief="flat",
                                 font=("Segoe UI", 10, "bold"), pady=7, cursor="hand2",
                                 command=lambda: self._set_modo("register"))
        self.btn_reg.pack(side="left", fill="x", expand=True)

        def campo(label):
            tk.Label(marco, text=label, bg=COLORES["surface"], fg=COLORES["text_muted"],
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 2))

        campo("USUARIO")
        self.user_var = tk.StringVar()
        tk.Entry(marco, textvariable=self.user_var, bg=COLORES["surface2"], fg=COLORES["text"],
                 font=("Segoe UI", 11), bd=0, relief="flat", insertbackground=COLORES["text"]).pack(fill="x", ipady=7)

        campo("CONTRASEÑA")
        self.pass_var = tk.StringVar()
        tk.Entry(marco, textvariable=self.pass_var, show="•", bg=COLORES["surface2"],
                 fg=COLORES["text"], font=("Segoe UI", 11), bd=0, relief="flat",
                 insertbackground=COLORES["text"]).pack(fill="x", ipady=7)

        self.error_label = tk.Label(marco, text="", bg=COLORES["surface"],
                                    fg=COLORES["accent_red"], font=("Segoe UI", 9), wraplength=280)
        self.error_label.pack(pady=(8, 0))

        self.btn_submit = tk.Button(marco, text="Ingresar", bg=COLORES["accent_blue"],
                                    fg="white", bd=0, relief="flat", font=("Segoe UI", 11, "bold"),
                                    pady=10, cursor="hand2", command=self._submit)
        self.btn_submit.pack(fill="x", pady=(12, 0))

        self.root.bind("<Return>", lambda e: self._submit())
        self._set_modo("login")

    def _set_modo(self, modo):
        self.modo.set(modo)
        if modo == "login":
            self.btn_login.config(bg=COLORES["accent_blue"], fg="white")
            self.btn_reg.config(bg=COLORES["surface2"], fg=COLORES["text_muted"])
            self.btn_submit.config(text="Ingresar")
        else:
            self.btn_reg.config(bg=COLORES["accent_blue"], fg="white")
            self.btn_login.config(bg=COLORES["surface2"], fg=COLORES["text_muted"])
            self.btn_submit.config(text="Crear cuenta")
        self.error_label.config(text="")

    def _submit(self):
        username = self.user_var.get().strip()
        password = self.pass_var.get()
        self.error_label.config(text="")

        if not username or not password:
            self.error_label.config(text="Completá todos los campos")
            return

        try:
            if self.modo.get() == "login":
                res = _db.table("usuarios").select("*").eq("username", username).execute()
                if not res.data or not check_password_hash(res.data[0]["password_hash"], password):
                    self.error_label.config(text="Usuario o contraseña incorrectos")
                    return
                user = res.data[0]
            else:
                if _db.table("usuarios").select("id").eq("username", username).execute().data:
                    self.error_label.config(text="Ese nombre de usuario ya está en uso")
                    return
                res = _db.table("usuarios").insert({
                    "email": f"{username}@finanzas.local",
                    "username": username,
                    "password_hash": generate_password_hash(password),
                    "verificado": True,
                }).execute()
                user = res.data[0]
                _db.table("transacciones").update({"user_id": user["id"]}).is_("user_id", "null").execute()

            _usuario_actual["id"] = user["id"]
            _usuario_actual["username"] = user["username"]
            guardar_sesion_local()
            self.autenticado = True
            self.root.destroy()

        except Exception as e:
            self.error_label.config(text=f"Error: {e}")


if __name__ == "__main__":
    # Intentar cargar sesión guardada
    if not cargar_sesion_local():
        login_root = tk.Tk()
        login_app = LoginApp(login_root)
        login_root.mainloop()
        if not login_app.autenticado:
            exit()

    # App principal
    root = tk.Tk()
    app = FinanzasApp(root)
    root.mainloop()
