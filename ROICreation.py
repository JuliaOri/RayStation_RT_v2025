from raystation import *
import numpy as np
from raystation.v2025.typing.generated import DoseBasedRoiFunction
import tkinter as tk
from tkinter import messagebox, ttk

case = get_current('Case')
examAll=case.Examinations #objeto examination
examCurrent=get_current('Examination')
examCurrentName=examCurrent.Name #nombre de examination
# Selecciona automáticamente el que esté abierto, pero en la segunda ventana de selección te permite cambiarlo con la variable CT
examinationAll=[exam.Name for exam in examAll]

pm = case.PatientModel
rois = pm.RegionsOfInterest 

def center_window(win):
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    ws = win.winfo_screenwidth()
    hs = win.winfo_screenheight()
    x = (ws // 2) - (w // 2)
    y = (hs // 2) - (h // 2)
    win.geometry(f'{w}x{h}+{x}+{y}')


def create_modal_window(title):
    win = tk.Tk()
    win.title(title)
    win.resizable(False, False)
    return win



def ventana_principal():
    win = create_modal_window("Datos del Plan")
    variables = {}

    # --- CT actual como valor por defecto ---
    default_ct = examCurrentName if examCurrentName in examinationAll else (examinationAll[0] if examinationAll else "N/A")
    ct_var = tk.StringVar(value=default_ct)


    ttk.Label(win, text="CT:").grid(row=5, column=0, sticky='w', padx=10, pady=5)
    ct_cb = ttk.Combobox(win, values=examinationAll, textvariable=ct_var, state='readonly')
    ct_cb.grid(row=5, column=1, padx=10, pady=5)

    if default_ct in examinationAll:
        ct_cb.current(examinationAll.index(default_ct))
    elif examinationAll:
        ct_cb.current(0)

    # --- Botones ---
    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=6, column=0, columnspan=2, pady=15)
    btn_frame.columnconfigure((0, 1), weight=1)


    exam_name = ct_var.get()
    def on_ok():
  #Para que no permita seleccionar la energía de 6FFF el los TrueBeam 3 y 4

        exam_name = ct_var.get()

        # --- Obtenemos el objeto Examination ---
        examination_obj = case.Examinations[exam_name] if exam_name in [ex.Name for ex in case.Examinations] else None

        # --- Obtenemos las ROIs segmentadas en esa examinación ---
        geometries = []
        if examination_obj:
            ss = case.PatientModel.StructureSets[exam_name]
            geometries = [
                geom.OfRoi.Name for geom in ss.RoiGeometries
                if geom.HasContours()  # solo las ROIs segmentadas
            ]

        # --- Guardamos todos los datos ---
        variables.update({
            "examinationName": exam_name,#nombre del CT seleccionado
            "_Examination": examination_obj,#objeto del CT
            "geometries": geometries
        })
        win.destroy()


    def on_cancel():
        variables.clear()
        win.destroy()

    ok_btn = ttk.Button(btn_frame, text="Ok", command=on_ok)
    ok_btn.grid(row=0, column=0, padx=10)
    cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=on_cancel)
    cancel_btn.grid(row=0, column=1, padx=10)

    def key_press(event):
        if event.keysym == 'Return':
            on_ok()
        elif event.keysym == 'Escape':
            on_cancel()

    win.bind('<Key>', key_press)
    center_window(win)
    win.mainloop()

    return variables if variables else None

def ventana_ptvs():
    win = create_modal_window("Seleccionar PTVs")
    variables = {}

    ss = pm.StructureSets[datos["examinationName"]]

    # PTVs ordenados alfabéticamente
    PTVs_inicio = sorted([
        geom for geom in datos["geometries"]
        if ss.RoiGeometries[geom].HasContours()
        and ss.RoiGeometries[geom].OfRoi.Type in ('Ptv', 'Ctv', 'Gtv')
    ])

    ttk.Label(
        win,
        text="Seleccione uno o más PTVs (clic simple / Shift + clic)"
    ).pack(padx=10, pady=10)

    listbox = tk.Listbox(win, selectmode='multiple', height=6)

    for item in PTVs_inicio:
        listbox.insert('end', item)

    listbox.pack(padx=10, pady=5, fill='x')

    # ---------------- Selección personalizada ----------------
    last_index = None

    def on_click(event):
        nonlocal last_index
        index = listbox.nearest(event.y)

        # Shift presionado → rango
        if event.state & 0x0001 and last_index is not None:
            start = min(last_index, index)
            end = max(last_index, index)

            selected = set(listbox.curselection())
            rango = set(range(start, end + 1))

            if rango.issubset(selected):
                listbox.selection_clear(start, end)
            else:
                listbox.selection_set(start, end)

        else:
            # Clic normal → toggle individual
            if index in listbox.curselection():
                listbox.selection_clear(index)
            else:
                listbox.selection_set(index)

            last_index = index

        return "break"  # anula comportamiento por defecto

    listbox.bind("<Button-1>", on_click)
    # ---------------------------------------------------------

    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=10)
    btn_frame.columnconfigure((0, 1), weight=1)

    def on_ok():
        selected = [listbox.get(i) for i in listbox.curselection()]
        if not selected:
            messagebox.showerror("Error", "Por favor, seleccionar al menos un PTV")
            return
        variables['PTVs_0'] = selected
        win.destroy()

    def on_cancel():
        variables.clear()
        win.destroy()

    ttk.Button(btn_frame, text="Ok", command=on_ok).grid(row=0, column=0, padx=10)
    ttk.Button(btn_frame, text="Cancelar", command=on_cancel).grid(row=0, column=1, padx=10)

    def key_press(event):
        if event.keysym == 'Return':
            on_ok()
        elif event.keysym == 'Escape':
            on_cancel()

    win.bind('<Key>', key_press)

    center_window(win)
    win.mainloop()

    return variables if variables else None


def ventana_organos():
    win = create_modal_window("Seleccionar OARs")
    variables = {}
    ss = pm.StructureSets[datos["examinationName"]]

    OARs_inicio = [
        geom for geom in datos["geometries"]
        if ss.RoiGeometries[geom].HasContours()
        and ss.RoiGeometries[geom].OfRoi.Type in ('Avoidance', 'Organ')
    ]

    ttk.Label(
        win,
        text="Seleccione TODOS los órganos para interseccionar"
    ).pack(padx=10, pady=10)

    listbox = tk.Listbox(win, selectmode='multiple', height=6)

    for item in OARs_inicio:
        listbox.insert('end', item)

    # Seleccionar todos por defecto
    listbox.selection_set(0, tk.END)

    listbox.pack(padx=10, pady=5, fill='x')

    # --- Selección múltiple sin CTRL ---
    def on_click(event):
        index = listbox.nearest(event.y)
        if index in listbox.curselection():
            listbox.selection_clear(index)
        else:
            listbox.selection_set(index)
        return "break"  # evita el comportamiento por defecto

    listbox.bind("<Button-1>", on_click)
    # ----------------------------------

    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=10)
    btn_frame.columnconfigure((0, 1), weight=1)

    def on_ok():
        selected = [listbox.get(i) for i in listbox.curselection()]
        if not selected:
            messagebox.showerror("Error", "Por favor, seleccionar al menos un PTV")
            return
        variables['OARs'] = selected
        win.destroy()

    def on_cancel():
        variables.clear()
        win.destroy()

    ttk.Button(btn_frame, text="Ok", command=on_ok).grid(row=0, column=0, padx=10)
    ttk.Button(btn_frame, text="Cancelar", command=on_cancel).grid(row=0, column=1, padx=10)

    def key_press(event):
        if event.keysym == 'Return':
            on_ok()
        elif event.keysym == 'Escape':
            on_cancel()

    win.bind('<Key>', key_press)

    center_window(win)
    win.mainloop()
    return variables if variables else None

def ventana_anillos():
    win = create_modal_window("Anillos")
    variables = {}

    # Texto introductorio al principio
    ttk.Label(win, 
              text="Introduce los anillos en mm", 
              wraplength=400,
              justify='center').grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    ttk.Label(win, text="Anillos en mm(separados por comas):").grid(row=1, column=0, sticky='w', padx=10, pady=10)
    anillos_var = tk.StringVar()
    anillos_entry = ttk.Entry(win, textvariable=anillos_var)
    anillos_entry.grid(row=1, column=1, padx=10, pady=10)
    anillos_entry.focus()
    anillos_entry.select_range(0, 'end')

    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
    btn_frame.columnconfigure((0,1), weight=1)

    def on_ok():
        anillos_vals = [x.strip() for x in anillos_var.get().split(',') if x.strip()]

        variables['Anillos'] = anillos_vals
        win.destroy()

    def on_cancel():
        variables.clear()
        win.destroy()

    ok_btn = ttk.Button(btn_frame, text="Ok", command=on_ok)
    ok_btn.grid(row=0, column=0, padx=10)
    cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=on_cancel)
    cancel_btn.grid(row=0, column=1, padx=10)

    def key_press(event):
        if event.keysym == 'Return':
            on_ok()
        elif event.keysym == 'Escape':
            on_cancel()

    win.bind('<Key>', key_press)
    center_window(win)
    win.mainloop()
    return variables if variables else None


# Ahora, la secuencia de ejecución y asignación global

datos = {}

d = ventana_principal()
if d is None:
    print("Cancelado en ventana principal")
    exit()
datos.update(d)

d = ventana_ptvs()
if d is None:
    print("Cancelado en ventana de selección PTVs")
    exit()
datos.update(d)

d = ventana_organos()
if d is None:
    print("Cancelado en ventana de selección OARs")
    exit()
datos.update(d)

d = ventana_anillos()
if d is None:
    print("Cancelado en ventana anillos")
    exit()
datos.update(d)

# Asignar variables globales automáticamente
for k, v in datos.items():
    globals()[k] = v

examination=case.Examinations[examinationName]
ss = pm.StructureSets[examination.Name]
def camb_color(roi, factor):
    c = rois[roi].Color
    r = max(0, min(int(c.R * factor), 254))
    g = max(0, min(int(c.G * factor), 254))
    b = max(0, min(int(c.B * factor), 254))
    return f"{r},{g},{b}"




def create_roi_if_not_exists(nombre, color,tipo):
    try:
        case.PatientModel.CreateRoi(Name=nombre, Color=color, Type=tipo, TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    except:
        print(f'La roi ya existe')

            
def create_algebra_geometry(nombre, source_names_a, margin_a, source_names_b, margin_b, result_operation):
 def margin_dict(margin):
     return {'Type': 'Expand', 'Superior': margin, 'Inferior': margin,
             'Anterior': margin, 'Posterior': margin, 'Right': margin, 'Left': margin}

 try:
  case.PatientModel.RegionsOfInterest[nombre].CreateAlgebraGeometry(
   Examination=examination,
   Algorithm="Contours",
   ExpressionA={
       'Operation': "Union",
       'SourceRoiNames': source_names_a,
       'MarginSettings': margin_dict(margin_a)
   },
   ExpressionB={
       'Operation': "Union",
       'SourceRoiNames': source_names_b,
       'MarginSettings': margin_dict(margin_b)
   },
   ResultOperation=result_operation,
   ResultMarginSettings=margin_dict(0)
  )
 
 
 except:
  print(f'La ROI "{nombre}" no se ha podido editar')
 try:
  case.PatientModel.RegionsOfInterest[nombre].CreateAlgebraGeometry(
   Examination=examination,
   Algorithm="Auto",
   ExpressionA={
   'Operation': "Union",
   'SourceRoiNames': [nombre],
   'MarginSettings': margin_dict(0)
   },
   ExpressionB={
   'Operation': "Union",
   'SourceRoiNames': [],
   'MarginSettings': margin_dict(0)
   },
   ResultOperation='None',
   ResultMarginSettings=margin_dict(0)
  )
 except:
  print('No se ha podido interseccionar con el External')

def CrearRois(nombre, roi1, roiSubs, RoiColor, margen, margen2,tipo):
    rois1 = [str(x) for x in roi1]
    rois2 = [str(x) for x in roiSubs]

    create_roi_if_not_exists(nombre, RoiColor,tipo)

    if roiSubs[0] == 'None':
        create_algebra_geometry(nombre, rois1, margen, [], 0, "None")
    else:
        create_algebra_geometry(nombre, rois1, margen, rois2, margen2, "Subtraction")
 
PTVs = PTVs_0

# Crear ROI principal y obtener isocentro
z_PTV='z PTV total '+str(examination.Name)
CrearRois(z_PTV, PTVs, ['None'], 'Blue', 0, 0,tipo='Control')
isocenter = ss.RoiGeometries[z_PTV].GetCenterOfRoi()




dosis_rois_restar=[]
oar_resta=[]
rois_restar=[]
# Aplicar tratamientos y funciones de optimización a PTVs y anillos
for i,ptv in enumerate(PTVs):   
    for oar in OARs:
        # color=1+(i*4/10)
        color=1.2
        nombre = f"z {oar} {ptv}"
        try:
            # CrearRois(nombre, [oar,ptv], [PTVs[:i]], camb_color(oar, color), 0, 0)
            create_roi_if_not_exists(nombre, camb_color(oar, color),tipo='Ptv')
            create_algebra_geometry(nombre, [oar], 0,[ptv] , 0, "Intersection")
        except:
            print(f'z {oar} {ptv} ya existe')
            
        if not ss.RoiGeometries[nombre].HasContours():
            try:
                pm.RegionsOfInterest[nombre].DeleteRoi()
            except:
                print(f'Error con z {oar} {ptv}')
        else:
            oar_resta.append(oar)


CrearRois(f'z exp {Anillos[0]}mm', [z_PTV], ['None'], 'Purple', float(Anillos[0])/10, 0,tipo='Control') 


def create_algebra_geometry_margins(nombre, source_names_a, margin_a, source_names_b, margin_b, result_operation):
    def margin_dict(margin):
        return {'Type': 'Expand', 'Superior': margin[0], 'Inferior': margin[1],
                'Anterior': margin[2], 'Posterior': margin[3], 'Right': margin[4], 'Left': margin[5]}

    try:
        case.PatientModel.RegionsOfInterest[nombre].CreateAlgebraGeometry(
        Examination=examination,
        Algorithm="Auto",
        ExpressionA={
            'Operation': "Union",
            'SourceRoiNames': source_names_a,
            'MarginSettings': margin_dict(margin_a)
        },
        ExpressionB={
            'Operation': "Union",
            'SourceRoiNames': source_names_b,
            'MarginSettings': margin_dict(margin_b)
        },
        ResultOperation=result_operation,
        ResultMarginSettings=margin_dict([0,0,0,0,0,0])
        )

    except:
        print(f'La ROI "{nombre}" no se ha podido editar')


    try:
        case.PatientModel.RegionsOfInterest[nombre].CreateAlgebraGeometry(
            Examination=examination,
            Algorithm="Auto",
            ExpressionA={
            'Operation': "Union",
            'SourceRoiNames': [nombre],
            'MarginSettings': margin_dict([0,0,0,0,0,0])
            },
            ExpressionB={
            'Operation': "Union",
            'SourceRoiNames': [],
            'MarginSettings': margin_dict([0,0,0,0,0,0])
            },
            ResultOperation='Intersection',
            ResultMarginSettings=margin_dict([0,0,0,0,0,0])
        )
    except:
        print('No se ha podido interseccionar con el External')
 

nombre='z Pos'
create_roi_if_not_exists(nombre, 'GreenYellow',tipo='Control')
create_algebra_geometry_margins(nombre, [z_PTV], [0,0,0,15,0,0], [z_PTV], [0.3,0.3,0.3,0.3,0.3,0.3], 'Subtraction')
ss.SimplifyContours(
    RoiNames=[nombre],
    RemoveHoles3D=False, RemoveSmallContours=True, AreaThreshold=8,
    ReduceMaxNumberOfPointsInContours=False, MaxNumberOfPoints=None,
    CreateCopyOfRoi=False, ResolveOverlappingContours=True
)
nombre='z Ant'
create_roi_if_not_exists(nombre, "Violet",tipo='Control')
create_algebra_geometry_margins(nombre, [z_PTV], [0,0,15,0,0,0], [z_PTV], [0.3,0.3,0.3,0.3,0.3,0.3], 'Subtraction')
ss.SimplifyContours(
    RoiNames=[nombre],
    RemoveHoles3D=False, RemoveSmallContours=True, AreaThreshold=8,
    ReduceMaxNumberOfPointsInContours=False, MaxNumberOfPoints=None,
    CreateCopyOfRoi=False, ResolveOverlappingContours=True
)
            
colors = ['Blue','Green','Yellow','Orange','Red',"DeepSkyBlue","GreenYellow","Gold","OrangeRed",]

for k,ani in enumerate(Anillos):
    color=colors[k]
    anillo = f'z exp {ani}mm'
    CrearRois(anillo, [z_PTV], ['None'], color, float(ani)/10, 0,tipo='Control') 



def aviso_final():
    mensaje = (
        'ROIs terminadas.'
    )
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal
    messagebox.showinfo("Aviso Final", mensaje)
    root.destroy() 
aviso_final()
